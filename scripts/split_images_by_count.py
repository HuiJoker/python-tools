#!/usr/bin/env python3
"""Split images in one folder into numbered batch folders.

Example:
    python split_images_by_count.py "F:\\work\\数据\\03_蜀渝_General_Person"
    python split_images_by_count.py "F:\\work\\数据\\03_蜀渝_General_Person" --batch-size 500 --copy
"""

from __future__ import annotations

import argparse
import math
import shutil
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split images in a folder into batch folders named parent_1, parent_2, ..."
    )
    parser.add_argument("source", help="Source folder containing images.")
    parser.add_argument(
        "-n",
        "--batch-size",
        type=int,
        default=400,
        help="Number of images per output folder. Default: 400.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy images instead of moving them.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without moving or copying files.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Include images in subfolders. Default only reads the source folder itself.",
    )
    return parser.parse_args()


def collect_images(source: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return sorted(
        (
            item
            for item in source.glob(pattern)
            if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS
        ),
        key=lambda path: str(path).lower(),
    )


def unique_target_path(target_dir: Path, image: Path) -> Path:
    target = target_dir / image.name
    if not target.exists():
        return target

    stem = image.stem
    suffix = image.suffix
    counter = 1
    while True:
        candidate = target_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def split_images(source: Path, batch_size: int, copy_files: bool, dry_run: bool, recursive: bool) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Source path is not a folder: {source}")
    if batch_size <= 0:
        raise ValueError("Batch size must be greater than 0.")

    images = collect_images(source, recursive)
    if not images:
        print(f"No supported image files found in: {source}")
        return

    total_batches = math.ceil(len(images) / batch_size)
    action = "Copy" if copy_files else "Move"
    print(f"{action} {len(images)} images into {total_batches} folders.")

    for index, image in enumerate(images):
        batch_number = index // batch_size + 1
        target_dir = source.parent / f"{source.name}_{batch_number}"
        target = unique_target_path(target_dir, image)

        if dry_run:
            print(f"[dry-run] {image} -> {target}")
            continue

        target_dir.mkdir(parents=True, exist_ok=True)
        if copy_files:
            shutil.copy2(image, target)
        else:
            shutil.move(str(image), str(target))

    if dry_run:
        print("Dry run finished. No files were changed.")
    else:
        print("Finished.")


def main() -> None:
    args = parse_args()
    split_images(
        source=Path(args.source).resolve(),
        batch_size=args.batch_size,
        copy_files=args.copy,
        dry_run=args.dry_run,
        recursive=args.recursive,
    )


if __name__ == "__main__":
    main()
