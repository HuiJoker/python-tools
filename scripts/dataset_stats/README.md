# Dataset Stats Scripts

Small command-line tools for quickly checking dataset folders.

## Files

- `count_images_xml_labels.py`: counts image files, XML files, Pascal VOC `object/name` labels, and optionally XML element tag names.

## Usage

Count files and Pascal VOC object labels. By default, the script scans subfolders recursively:

```powershell
python count_images_xml_labels.py "F:\path\to\dataset"
```

Only scan top-level files in the selected folder:

```powershell
python count_images_xml_labels.py "F:\path\to\dataset" --no-recursive
```

Also count XML element tag names such as `annotation`, `object`, and `name`:

```powershell
python count_images_xml_labels.py "F:\path\to\dataset" --all-xml-tags
```

Export `object/name` label counts to CSV:

```powershell
python count_images_xml_labels.py "F:\path\to\dataset" --csv label_counts.csv
```

## Output

The script prints:

- scanned directory
- whether recursive mode is enabled
- image count
- XML file count
- failed XML parse count
- total Pascal VOC `object/name` label count
- label class count
- label count distribution

## Notes

- Supported image extensions: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tif`, `.tiff`, `.webp`.
- XML label statistics are based on Pascal VOC style `object/name` fields.
- `--all-xml-tags` is for counting XML element names, not annotation classes.
- CSV output uses `utf-8-sig`, which opens cleanly in Excel.
