# Label Analysis Scripts

Tools for counting labels in Pascal VOC style XML annotation files and comparing two XML annotation folders.

## Files

- `analyze_labels.py`: command-line label counter and reusable comparison functions.
- `label_analysis_gui.py`: Tkinter GUI wrapper around `analyze_labels.py`.

## Count Labels

Count all labels in a folder containing images and matching XML files:

```powershell
python analyze_labels.py --dir "F:\path\to\dataset"
```

Count selected labels:

```powershell
python analyze_labels.py --dir "F:\path\to\dataset" --labels DCC w_rope
```

Write counts to CSV:

```powershell
python analyze_labels.py --dir "F:\path\to\dataset" --csv label_counts.csv
```

## GUI

Run the GUI from the same folder as `analyze_labels.py`:

```powershell
python label_analysis_gui.py
```

## Notes

- Supports image extensions: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`.
- Counts Pascal VOC object labels from `./object/name` in XML files.
- Reports images missing XML files and XML files missing images.
- The comparison logic compares same-named XML files between two folders and summarizes deleted, added, and modified labels.
