#!/usr/bin/env python3
"""Extract frames from one video or a folder of videos at a fixed time interval."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2


VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".flv",
    ".wmv",
    ".m4v",
    ".ts",
}


# def parse_args() -> argparse.Namespace:
#     parser = argparse.ArgumentParser(
#         description="Extract JPG frames from one video or all videos in a folder."
#     )
#     parser.add_argument("input", help="Input video file or folder.")
#     parser.add_argument("output", help="Output folder for extracted JPG files.")
#     parser.add_argument(
#         "-i",
#         "--interval-seconds",
#         type=float,
#         default=1.0,
#         help="Time interval between frames in seconds. Default: 1.0.",
#     )
#     parser.add_argument(
#         "--recursive",
#         action="store_true",
#         help="When input is a folder, include videos in subfolders.",
#     )
#     parser.add_argument(
#         "--flat",
#         action="store_true",
#         help="Save all frames directly in the output folder instead of one subfolder per video.",
#     )
#     return parser.parse_args()


def save_jpg(image_path: Path, frame) -> bool:
    image_path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded_image = cv2.imencode(".jpg", frame)
    if not ok:
        return False
    encoded_image.tofile(str(image_path))
    return True


def extract_frames_by_seconds(
    video_path: Path,
    output_dir: Path,
    interval_seconds: float,
    flat: bool = False,
) -> int:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[failed] Cannot open video: {video_path}")
        return 0

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0:
        print(f"[failed] Cannot read video FPS: {video_path}")
        cap.release()
        return 0

    duration = total_frames / fps
    video_output_dir = output_dir if flat else output_dir / video_path.stem
    print(f"Processing: {video_path}")
    print(f"  FPS: {fps:.2f}, duration: {duration:.2f}s, interval: {interval_seconds}s")

    saved_count = 0
    current_time = 0.0

    while current_time <= duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
        success, frame = cap.read()
        if not success:
            break

        time_ms = int(round(current_time * 1000))
        image_name = f"{video_path.stem}_{time_ms:010d}ms.jpg"
        image_path = video_output_dir / image_name

        if save_jpg(image_path, frame):
            saved_count += 1
        else:
            print(f"[warning] Failed to encode image: {image_path}")

        current_time += interval_seconds

    cap.release()
    print(f"  Saved frames: {saved_count}")
    return saved_count


def find_videos(input_path: Path, recursive: bool) -> list[Path]:
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() in VIDEO_EXTENSIONS else []

    iterator = input_path.rglob("*") if recursive else input_path.iterdir()
    return sorted(
        path
        for path in iterator
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def extract_batch(input_path: Path, output_dir: Path, interval_seconds: float, recursive: bool, flat: bool) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    if interval_seconds <= 0:
        raise ValueError("Interval seconds must be greater than 0.")

    videos = find_videos(input_path, recursive)
    if not videos:
        print(f"No supported video files found: {input_path}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Found videos: {len(videos)}")
    print(f"Output folder: {output_dir}")

    total_saved = 0
    processed = 0

    for index, video_path in enumerate(videos, start=1):
        print(f"\n[{index}/{len(videos)}]")
        saved = extract_frames_by_seconds(video_path, output_dir, interval_seconds, flat)
        total_saved += saved
        if saved > 0:
            processed += 1

    print("\nDone.")
    print(f"Videos processed: {processed}/{len(videos)}")
    print(f"Total frames saved: {total_saved}")


def main() -> None:
    args = parse_args()
    extract_batch(
        input_path=Path(args.input).resolve(),
        output_dir=Path(args.output).resolve(),
        interval_seconds=args.interval_seconds,
        recursive=args.recursive,
        flat=args.flat,
    )


if __name__ == "__main__":
    main()
