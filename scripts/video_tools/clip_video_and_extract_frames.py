#!/usr/bin/env python3
"""Clip a video segment with ffmpeg, then extract JPG frames from the segment."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clip a video segment with ffmpeg and extract frames from the clipped segment."
    )
    parser.add_argument("input_video", help="Input video path.")
    parser.add_argument("output_video", help="Output clipped video path.")
    parser.add_argument("frames_dir", help="Output folder for extracted JPG frames.")
    parser.add_argument("--start", required=True, help='Start time, for example "00:03:57" or "237".')
    parser.add_argument("--end", required=True, help='End time, for example "00:04:31" or "271".')
    parser.add_argument(
        "-i",
        "--interval-seconds",
        type=float,
        default=1.0,
        help="Time interval between extracted frames in seconds. Default: 1.0.",
    )
    parser.add_argument(
        "--prefix",
        default="frame",
        help="Output image filename prefix. Default: frame.",
    )
    parser.add_argument(
        "--reencode",
        action="store_true",
        help="Re-encode the clipped video instead of stream copying.",
    )
    parser.add_argument(
        "--skip-clip",
        action="store_true",
        help="Skip ffmpeg clipping and extract frames from output_video if it already exists.",
    )
    return parser.parse_args()


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg was not found on PATH.")


def clip_video(input_video: Path, output_video: Path, start_time: str, end_time: str, reencode: bool) -> None:
    if not input_video.exists():
        raise FileNotFoundError(f"Input video does not exist: {input_video}")

    require_ffmpeg()
    output_video.parent.mkdir(parents=True, exist_ok=True)

    if reencode:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_video),
            "-ss",
            start_time,
            "-to",
            end_time,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(output_video),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            start_time,
            "-to",
            end_time,
            "-i",
            str(input_video),
            "-c",
            "copy",
            str(output_video),
        ]

    print("Clipping video:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Clipped video written: {output_video}")


def save_jpg(image_path: Path, frame) -> bool:
    image_path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded_image = cv2.imencode(".jpg", frame)
    if not ok:
        return False
    encoded_image.tofile(str(image_path))
    return True


def extract_frames(video_path: Path, frames_dir: Path, interval_seconds: float, prefix: str) -> int:
    if interval_seconds <= 0:
        raise ValueError("Interval seconds must be greater than 0.")
    if not video_path.exists():
        raise FileNotFoundError(f"Video does not exist: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0:
        cap.release()
        raise RuntimeError(f"Cannot read video FPS: {video_path}")

    duration = total_frames / fps
    saved_count = 0
    current_time = 0.0

    print(f"Extracting frames from: {video_path}")
    print(f"FPS: {fps:.2f}, duration: {duration:.2f}s, interval: {interval_seconds}s")

    while current_time <= duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
        success, frame = cap.read()
        if not success:
            break

        time_ms = int(round(current_time * 1000))
        image_path = frames_dir / f"{prefix}_{time_ms:010d}ms.jpg"
        if save_jpg(image_path, frame):
            saved_count += 1
        else:
            print(f"[warning] Failed to encode image: {image_path}")

        current_time += interval_seconds

    cap.release()
    print(f"Saved frames: {saved_count}")
    print(f"Frames folder: {frames_dir}")
    return saved_count


def main() -> None:
    args = parse_args()
    input_video = Path(args.input_video).resolve()
    output_video = Path(args.output_video).resolve()
    frames_dir = Path(args.frames_dir).resolve()

    if args.skip_clip:
        if not output_video.exists():
            raise FileNotFoundError(f"--skip-clip was used but output_video does not exist: {output_video}")
    else:
        clip_video(input_video, output_video, args.start, args.end, args.reencode)

    extract_frames(output_video, frames_dir, args.interval_seconds, args.prefix)


if __name__ == "__main__":
    main()
