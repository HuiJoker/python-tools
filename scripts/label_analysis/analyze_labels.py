import argparse
import csv
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def normalize_labels(labels):
    if not labels:
        return None

    if isinstance(labels, str):
        raw_text = labels.strip()
    else:
        raw_text = " ".join(labels).strip()

    if not raw_text or raw_text.lower() == "all":
        return None

    normalized = raw_text.replace(",", " ").replace("，", " ").replace("\n", " ")
    parsed_labels = []

    for label in normalized.split():
        clean_label = label.strip().strip("'\"")
        if clean_label:
            parsed_labels.append(clean_label)

    return parsed_labels


def parse_args():
    parser = argparse.ArgumentParser(description="Count labels in Pascal VOC style XML files.")
    parser.add_argument("--dir", default=".", help="Folder containing images and XML files.")
    parser.add_argument("--labels", nargs="*", help="Labels to count. Use all or omit to count all.")
    parser.add_argument("--csv", help="Optional CSV output path for label counts.")
    return parser.parse_args()


def find_files(data_dir):
    images = [
        path
        for path in data_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    xmls = [path for path in data_dir.iterdir() if path.is_file() and path.suffix.lower() == ".xml"]
    return images, xmls


def text_or_empty(element):
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def read_labels(xml_path):
    root = ET.parse(xml_path).getroot()
    return [
        name.text.strip()
        for name in root.findall("./object/name")
        if name.text and name.text.strip()
    ]


def read_objects(xml_path):
    root = ET.parse(xml_path).getroot()
    objects = []

    for index, obj in enumerate(root.findall("./object"), start=1):
        bndbox = obj.find("bndbox")
        objects.append(
            {
                "index": index,
                "id": text_or_empty(obj.find("id")),
                "name": text_or_empty(obj.find("name")),
                "bbox": (
                    text_or_empty(bndbox.find("xmin")) if bndbox is not None else "",
                    text_or_empty(bndbox.find("ymin")) if bndbox is not None else "",
                    text_or_empty(bndbox.find("xmax")) if bndbox is not None else "",
                    text_or_empty(bndbox.find("ymax")) if bndbox is not None else "",
                ),
            }
        )

    return objects


def write_csv(csv_path, counts, selected_labels, total):
    output_path = Path(csv_path)
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["label", "count"])
        for label in selected_labels:
            writer.writerow([label, counts.get(label, 0)])
        writer.writerow(["TOTAL", total])
    return output_path


def analyze_directory(data_dir, labels=None):
    data_dir = Path(data_dir)

    if not data_dir.exists() or not data_dir.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {data_dir}")

    images, xmls = find_files(data_dir)
    image_stems = {path.stem for path in images}
    xml_stems = {path.stem for path in xmls}

    counts = Counter()
    bad_xmls = []

    for xml_path in xmls:
        try:
            counts.update(read_labels(xml_path))
        except ET.ParseError as exc:
            bad_xmls.append((xml_path.name, str(exc)))

    selected_labels = normalize_labels(labels) or sorted(counts)
    selected_counts = {label: counts.get(label, 0) for label in selected_labels}
    selected_total = sum(selected_counts.values())

    return {
        "directory": data_dir,
        "image_count": len(images),
        "xml_count": len(xmls),
        "missing_xml": sorted(image_stems - xml_stems),
        "missing_image": sorted(xml_stems - image_stems),
        "counts": selected_counts,
        "selected_labels": selected_labels,
        "total": selected_total,
        "bad_xmls": bad_xmls,
    }


def compare_xml_folders(v1_dir, v2_dir):
    v1_dir = Path(v1_dir)
    v2_dir = Path(v2_dir)

    if not v1_dir.exists() or not v1_dir.is_dir():
        raise FileNotFoundError(f"V1 directory does not exist: {v1_dir}")
    if not v2_dir.exists() or not v2_dir.is_dir():
        raise FileNotFoundError(f"V2 directory does not exist: {v2_dir}")

    v1_xmls = {path.name: path for path in v1_dir.iterdir() if path.is_file() and path.suffix.lower() == ".xml"}
    v2_xmls = {path.name: path for path in v2_dir.iterdir() if path.is_file() and path.suffix.lower() == ".xml"}
    common_names = sorted(set(v1_xmls) & set(v2_xmls))

    result = {
        "v1_dir": v1_dir,
        "v2_dir": v2_dir,
        "v1_xml_count": len(v1_xmls),
        "v2_xml_count": len(v2_xmls),
        "common_xml_count": len(common_names),
        "v1_only_xml": sorted(set(v1_xmls) - set(v2_xmls)),
        "v2_only_xml": sorted(set(v2_xmls) - set(v1_xmls)),
        "deleted": [],
        "modified": [],
        "added": [],
        "bad_xmls": [],
    }

    for filename in common_names:
        try:
            v1_objects = read_objects(v1_xmls[filename])
            v2_objects = read_objects(v2_xmls[filename])
        except ET.ParseError as exc:
            result["bad_xmls"].append((filename, str(exc)))
            continue

        compare_objects(filename, v1_objects, v2_objects, result)

    result["deleted_by_label"] = Counter(item["label"] for item in result["deleted"])
    result["added_by_label"] = Counter(item["label"] for item in result["added"])
    result["modified_from_by_label"] = Counter(item["old_label"] for item in result["modified"])
    result["modified_to_by_label"] = Counter(item["new_label"] for item in result["modified"])
    return result


def compare_objects(filename, v1_objects, v2_objects, result):
    v1_remaining, v2_remaining = remove_exact_matches(v1_objects, v2_objects)

    if len(v1_remaining) == len(v2_remaining):
        append_modified(filename, v1_remaining, v2_remaining, result)
        return

    pair_count = min(len(v1_remaining), len(v2_remaining))
    append_modified(filename, v1_remaining[:pair_count], v2_remaining[:pair_count], result)

    for old_obj in v1_remaining[pair_count:]:
        result["deleted"].append(
            {
                "file": filename,
                "label": old_obj["name"],
                "bbox": old_obj["bbox"],
            }
        )

    for new_obj in v2_remaining[pair_count:]:
        result["added"].append(
            {
                "file": filename,
                "label": new_obj["name"],
                "bbox": new_obj["bbox"],
            }
        )


def append_modified(filename, old_objects, new_objects, result):
    for old_obj, new_obj in zip(old_objects, new_objects):
        result["modified"].append(
            {
                "file": filename,
                "old_label": old_obj["name"],
                "new_label": new_obj["name"],
                "old_bbox": old_obj["bbox"],
                "new_bbox": new_obj["bbox"],
            }
        )


def remove_exact_matches(v1_objects, v2_objects):
    used_v2_indexes = set()
    v1_remaining = []

    for old_obj in v1_objects:
        match_index = find_exact_match(old_obj, v2_objects, used_v2_indexes)
        if match_index is None:
            v1_remaining.append(old_obj)
        else:
            used_v2_indexes.add(match_index)

    v2_remaining = [
        new_obj
        for index, new_obj in enumerate(v2_objects)
        if index not in used_v2_indexes
    ]
    return v1_remaining, v2_remaining


def find_exact_match(target, candidates, used_indexes):
    target_signature = object_signature(target)
    for index, candidate in enumerate(candidates):
        if index in used_indexes:
            continue
        if object_signature(candidate) == target_signature:
            return index
    return None


def object_signature(obj):
    return obj["name"], obj["bbox"]


def main():
    args = parse_args()
    try:
        result = analyze_directory(args.dir, args.labels)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Directory: {result['directory']}")
    print(f"Images: {result['image_count']}")
    print(f"XML files: {result['xml_count']}")
    print(f"Images missing XML: {len(result['missing_xml'])}")
    print(f"XML files missing image: {len(result['missing_image'])}")
    print()
    print("Label counts:")

    for label in result["selected_labels"]:
        print(f"  {label}: {result['counts'][label]}")

    print(f"  TOTAL: {result['total']}")

    if result["bad_xmls"]:
        print()
        print("Failed XML files:")
        for filename, error in result["bad_xmls"]:
            print(f"  {filename}: {error}")

    if args.csv:
        output_path = write_csv(args.csv, result["counts"], result["selected_labels"], result["total"])
        print()
        print(f"CSV written: {output_path}")


if __name__ == "__main__":
    main()
