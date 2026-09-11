#!/usr/bin/env python3
"""Split images in one folder into numbered batch folders.

Example:
    python split_images_by_count.py "F:\\work\\数据\\2_蜀渝\\SY_General_Tools\\20260820_SY_General_Tools_all_CS"
    python split_images_by_count.py "F:\\work\\数据\\03_蜀渝_General_Person" --batch-size 500 --copy
"""

from __future__ import annotations

import argparse
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
    def is_prior_output(item: Path) -> bool:
        relative_parts = item.relative_to(source).parts
        return (
            recursive
            and len(relative_parts) > 1
            and relative_parts[0].startswith(f"{source.name}_")
        )

    return sorted(
        (item for item in source.glob(pattern) if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS and not is_prior_output(item)),
        key=lambda path: str(path).lower(),
    )


def group_images(images: list[Path], batch_size: int) -> list[list[Path]]:
    """Create batches and merge a small final remainder into the last batch."""
    batches = [images[index : index + batch_size] for index in range(0, len(images), batch_size)]
    if len(batches) > 1 and len(batches[-1]) < batch_size / 2:
        batches[-2].extend(batches.pop())
    return batches


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


def split_images(
    source: Path, batch_size: int, copy_files: bool, dry_run: bool, recursive: bool
) -> dict[str, object]:
    if not source.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Source path is not a folder: {source}")
    if batch_size <= 0:
        raise ValueError("Batch size must be greater than 0.")

    images = collect_images(source, recursive)
    if not images:
        print(f"No supported image files found in: {source}")
        return {"image_count": 0, "batch_count": 0, "batch_sizes": [], "output_dirs": []}

    batches = group_images(images, batch_size)
    action = "Copy" if copy_files else "Move"
    print(f"{action} {len(images)} images into {len(batches)} folders: {[len(batch) for batch in batches]}.")

    output_dirs = []
    for batch_number, batch in enumerate(batches, start=1):
        target_dir = source / f"{source.name}_{batch_number}"
        output_dirs.append(target_dir)
        for image in batch:
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
    return {
        "image_count": len(images),
        "batch_count": len(batches),
        "batch_sizes": [len(batch) for batch in batches],
        "output_dirs": [str(path) for path in output_dirs],
    }


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
