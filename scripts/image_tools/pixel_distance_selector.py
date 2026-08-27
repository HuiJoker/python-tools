#!/usr/bin/env python3
"""Interactively select points on an image or video frame and measure pixel distance."""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np


@dataclass
class ViewerState:
    image: np.ndarray
    source_info: str
    window_width: int
    window_height: int
    min_scale: float = 0.5
    max_scale: float = 20.0
    scale: float = 1.0
    view_x: int = 0
    view_y: int = 0
    points: list[tuple[int, int]] = field(default_factory=list)
    dragging: bool = False
    last_mouse_x: int = 0
    last_mouse_y: int = 0

    @property
    def image_height(self) -> int:
        return self.image.shape[0]

    @property
    def image_width(self) -> int:
        return self.image.shape[1]


state: ViewerState | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure pixel coordinates and distances on an image, camera frame, or video stream."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--image", help="Image path to open.")
    source.add_argument("--stream", help='RTSP URL, video file path, or camera index such as "0".')
    parser.add_argument("--warmup-frames", type=int, default=5, help="Frames to read before using a stream frame.")
    parser.add_argument("--timeout-seconds", type=float, default=15.0, help="Stream frame read timeout.")
    parser.add_argument("--window-width", type=int, default=1600, help="Viewer window width.")
    parser.add_argument("--window-height", type=int, default=900, help="Viewer window height.")
    return parser.parse_args()


def parse_stream_source(value: str):
    return int(value) if value.isdigit() else value


def read_image(image_path: str) -> tuple[np.ndarray, str]:
    path = Path(image_path)
    frame = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return frame, str(path)


def read_stream_frame(stream_url: str, warmup_frames: int, timeout_seconds: float) -> tuple[np.ndarray, str]:
    cap = cv2.VideoCapture(parse_stream_source(stream_url))
    deadline = time.monotonic() + timeout_seconds
    frame = None
    read_count = 0

    try:
        while time.monotonic() < deadline:
            ok, current = cap.read()
            if not ok or current is None:
                time.sleep(0.1)
                continue

            frame = current
            read_count += 1
            if read_count >= warmup_frames:
                break
    finally:
        cap.release()

    if frame is None:
        raise RuntimeError(f"Failed to read a frame from stream: {stream_url}")

    return frame, str(stream_url)


def require_state() -> ViewerState:
    if state is None:
        raise RuntimeError("Viewer state has not been initialized.")
    return state


def limit_view() -> None:
    current = require_state()
    zoom_w = int(current.image_width * current.scale)
    zoom_h = int(current.image_height * current.scale)
    current.view_x = max(0, min(current.view_x, max(0, zoom_w - current.window_width)))
    current.view_y = max(0, min(current.view_y, max(0, zoom_h - current.window_height)))


def screen_to_image(sx: int, sy: int) -> tuple[int, int]:
    current = require_state()
    ix = int((sx + current.view_x) / current.scale)
    iy = int((sy + current.view_y) / current.scale)
    ix = max(0, min(ix, current.image_width - 1))
    iy = max(0, min(iy, current.image_height - 1))
    return ix, iy


def image_to_screen(ix: int, iy: int) -> tuple[int, int]:
    current = require_state()
    sx = int(ix * current.scale - current.view_x)
    sy = int(iy * current.scale - current.view_y)
    return sx, sy


def redraw() -> None:
    current = require_state()
    limit_view()

    zoom_img = cv2.resize(
        current.image,
        None,
        fx=current.scale,
        fy=current.scale,
        interpolation=cv2.INTER_LINEAR,
    )
    canvas = np.zeros((current.window_height, current.window_width, 3), dtype=np.uint8)
    zoom_h, zoom_w = zoom_img.shape[:2]

    x1 = current.view_x
    y1 = current.view_y
    x2 = min(current.view_x + current.window_width, zoom_w)
    y2 = min(current.view_y + current.window_height, zoom_h)

    crop = zoom_img[y1:y2, x1:x2]
    canvas[0 : crop.shape[0], 0 : crop.shape[1]] = crop

    for index, (px, py) in enumerate(current.points, start=1):
        sx, sy = image_to_screen(px, py)
        if 0 <= sx < current.window_width and 0 <= sy < current.window_height:
            cv2.circle(canvas, (sx, sy), 6, (0, 0, 255), -1)
            cv2.putText(
                canvas,
                f"P{index}({px},{py})",
                (sx + 10, sy - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

    if len(current.points) >= 2:
        p1, p2 = current.points[:2]
        sx1, sy1 = image_to_screen(*p1)
        sx2, sy2 = image_to_screen(*p2)
        cv2.line(canvas, (sx1, sy1), (sx2, sy2), (0, 0, 255), 2)
        distance = math.dist(p1, p2)
        cv2.putText(canvas, f"Pixel Length: {distance:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.putText(
        canvas,
        f"Scale: {current.scale:.2f}x  Frame: {current.image_width}x{current.image_height}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 0),
        2,
    )
    cv2.imshow("Pixel Distance Selector", canvas)


def mouse_callback(event, x, y, flags, _param) -> None:
    current = require_state()

    if event == cv2.EVENT_LBUTTONDOWN:
        point = screen_to_image(x, y)
        if len(current.points) >= 2:
            current.points.clear()
        current.points.append(point)
        print(f"Point {len(current.points)}: x={point[0]}, y={point[1]}")

        if len(current.points) == 2:
            (x1, y1), (x2, y2) = current.points
            distance = math.dist((x1, y1), (x2, y2))
            print("\n==============================")
            print(f"x1, y1 = {x1}, {y1}")
            print(f"x2, y2 = {x2}, {y2}")
            print(f"pixel_length = {distance:.2f}")
            print(f"line = [{x1}, {y1}, {x2}, {y2}]")
            print("==============================\n")

        redraw()

    elif event == cv2.EVENT_RBUTTONDOWN:
        if current.points:
            current.points.pop()
            print("Removed last point.")
            redraw()

    elif event == cv2.EVENT_MBUTTONDOWN:
        current.dragging = True
        current.last_mouse_x = x
        current.last_mouse_y = y

    elif event == cv2.EVENT_MBUTTONUP:
        current.dragging = False

    elif event == cv2.EVENT_MOUSEMOVE and current.dragging:
        current.view_x -= x - current.last_mouse_x
        current.view_y -= y - current.last_mouse_y
        current.last_mouse_x = x
        current.last_mouse_y = y
        redraw()

    elif event == cv2.EVENT_MOUSEWHEEL:
        ix, iy = screen_to_image(x, y)
        current.scale *= 1.25 if flags > 0 else 1 / 1.25
        current.scale = max(current.min_scale, min(current.max_scale, current.scale))
        current.view_x = int(ix * current.scale - x)
        current.view_y = int(iy * current.scale - y)
        print(f"Scale: {current.scale:.2f}x")
        redraw()


def print_help() -> None:
    print("========== Controls ==========")
    print("Left mouse: select point")
    print("Right mouse: remove last point")
    print("Mouse wheel: zoom in/out")
    print("Middle mouse drag: pan")
    print("+ or =: zoom in")
    print("-: zoom out")
    print("W/A/S/D: pan")
    print("R: reset view")
    print("C: clear points")
    print("Esc: exit")
    print("==============================")


def run_viewer(args: argparse.Namespace) -> None:
    global state

    if args.image:
        frame, info = read_image(args.image)
    else:
        frame, info = read_stream_frame(args.stream, args.warmup_frames, args.timeout_seconds)

    state = ViewerState(
        image=frame,
        source_info=info,
        window_width=args.window_width,
        window_height=args.window_height,
    )

    cv2.namedWindow("Pixel Distance Selector", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Pixel Distance Selector", state.window_width, state.window_height)
    cv2.setMouseCallback("Pixel Distance Selector", mouse_callback)
    redraw()

    print(f"Source: {state.source_info}")
    print(f"Frame size: {state.image_width}x{state.image_height}")
    print_help()

    while True:
        key = cv2.waitKey(20) & 0xFF
        if key == 27:
            break
        if key in (ord("+"), ord("=")):
            state.scale = min(state.scale * 1.25, state.max_scale)
        elif key == ord("-"):
            state.scale = max(state.scale / 1.25, state.min_scale)
        elif key == ord("w"):
            state.view_y -= 80
        elif key == ord("s"):
            state.view_y += 80
        elif key == ord("a"):
            state.view_x -= 80
        elif key == ord("d"):
            state.view_x += 80
        elif key == ord("r"):
            state.scale = 1.0
            state.view_x = 0
            state.view_y = 0
        elif key == ord("c"):
            state.points.clear()
            print("Cleared points.")
        else:
            continue
        redraw()

    cv2.destroyAllWindows()


def main() -> None:
    run_viewer(parse_args())


if __name__ == "__main__":
    main()
