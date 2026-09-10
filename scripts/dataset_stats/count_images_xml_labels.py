#!/usr/bin/env python3
"""Count images and labels in XML annotation files."""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".webp",
}


def iter_files(root: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return [path for path in root.glob(pattern) if path.is_file()]


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def find_voc_labels(xml_path: Path) -> list[str]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    labels: list[str] = []

    for obj in root.iter():
        if local_name(obj.tag) != "object":
            continue
        for child in obj:
            if local_name(child.tag) == "name" and child.text:
                label = child.text.strip()
                if label:
                    labels.append(label)
                break

    return labels


def count_xml_element_tags(xml_path: Path) -> Counter[str]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    return Counter(local_name(elem.tag) for elem in root.iter())


def write_csv(csv_path: Path, label_counts: Counter[str]) -> None:
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["label", "count"])
        for label, count in label_counts.most_common():
            writer.writerow([label, count])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count images, XML files, and Pascal VOC object/name labels."
    )
    parser.add_argument("folder", type=Path, help="Dataset folder to scan.")
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only scan the top-level files in the dataset folder.",
    )
    parser.add_argument(
        "--all-xml-tags",
        action="store_true",
        help="Also count XML element tag names, such as annotation, object, and name.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Export object/name label counts to CSV, for example label_counts.csv.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    folder = args.folder.expanduser().resolve()

    if not folder.exists():
        print(f"Error: folder does not exist: {folder}", file=sys.stderr)
        return 1
    if not folder.is_dir():
        print(f"Error: not a folder: {folder}", file=sys.stderr)
        return 1

    recursive = not args.no_recursive
    files = iter_files(folder, recursive)
    image_files = [path for path in files if path.suffix.lower() in IMAGE_EXTENSIONS]
    xml_files = [path for path in files if path.suffix.lower() == ".xml"]

    label_counts: Counter[str] = Counter()
    xml_tag_counts: Counter[str] = Counter()
    parse_errors: list[tuple[Path, str]] = []

    for xml_path in xml_files:
        try:
            label_counts.update(find_voc_labels(xml_path))
            if args.all_xml_tags:
                xml_tag_counts.update(count_xml_element_tags(xml_path))
        except ET.ParseError as exc:
            parse_errors.append((xml_path, str(exc)))

    print(f"Directory: {folder}")
    print(f"Recursive: {'yes' if recursive else 'no'}")
    print(f"Images: {len(image_files)}")
    print(f"XML files: {len(xml_files)}")
    print(f"Failed XML files: {len(parse_errors)}")
    print(f"Total object/name labels: {sum(label_counts.values())}")
    print(f"Label classes: {len(label_counts)}")

    if label_counts:
        print("\nLabel counts:")
        label_width = max(len(label) for label in label_counts)
        for label, count in label_counts.most_common():
            print(f"{label:<{label_width}}  {count}")

    if args.all_xml_tags and xml_tag_counts:
        print("\nXML element tag counts:")
        tag_width = max(len(tag) for tag in xml_tag_counts)
        for tag, count in xml_tag_counts.most_common():
            print(f"{tag:<{tag_width}}  {count}")

    if parse_errors:
        print("\nFailed XML file details:")
        for xml_path, error in parse_errors:
            print(f"{xml_path}: {error}")

    if args.csv:
        csv_path = args.csv.expanduser().resolve()
        write_csv(csv_path, label_counts)
        print(f"\nCSV written: {csv_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
