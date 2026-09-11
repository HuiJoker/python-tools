import argparse
import math
import time

import cv2
import numpy as np


# 直接在这里配置来源。
# SOURCE_MODE = "stream" 时从 CAMERA_URL 抓一帧量坐标。
# SOURCE_MODE = "image" 时从 IMAGE_PATH 读图片量坐标。
SOURCE_MODE = "stream"
CAMERA_URL = 0  
#r"rtsp://user:password@192.168.1.10:554/stream1"
IMAGE_PATH = r"D:/Yolov11/dataset/images/train/20260609154131_55_83.jpg"

DEFAULT_IMAGE_PATH = r"D:/Yolov11/dataset/images/train/20260609154131_55_83.jpg"

win_w, win_h = 1600, 900

scale = 1.0
min_scale = 0.5
max_scale = 20.0

view_x = 0
view_y = 0
points = []

dragging = False
last_mouse_x = 0
last_mouse_y = 0

img = None
img_h = 0
img_w = 0
source_info = ""


def parse_camera_source(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def read_image_frame(image_path):
    frame = cv2.imread(image_path)
    if frame is None:
        raise FileNotFoundError(f"图片读取失败: {image_path}")
    return frame, image_path


def read_stream_frame(stream_url, warmup_frames=5, timeout_seconds=15):
    source = parse_camera_source(stream_url)
    cap = cv2.VideoCapture(source)
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
        raise RuntimeError(f"拉流取帧失败: {stream_url}")

    return frame, str(stream_url)


def set_image(frame, info):
    global img, img_h, img_w, source_info, scale, view_x, view_y, points
    img = frame
    img_h, img_w = img.shape[:2]
    source_info = info
    scale = 1.0
    view_x = 0
    view_y = 0
    points = []


def limit_view():
    global view_x, view_y

    zoom_w = int(img_w * scale)
    zoom_h = int(img_h * scale)

    max_x = max(0, zoom_w - win_w)
    max_y = max(0, zoom_h - win_h)

    view_x = max(0, min(view_x, max_x))
    view_y = max(0, min(view_y, max_y))


def screen_to_image(sx, sy):
    """窗口坐标 -> 原始图像/原始流帧坐标。"""
    ix = int((sx + view_x) / scale)
    iy = int((sy + view_y) / scale)

    ix = max(0, min(ix, img_w - 1))
    iy = max(0, min(iy, img_h - 1))

    return ix, iy


def image_to_screen(ix, iy):
    """原始图像/原始流帧坐标 -> 窗口坐标。"""
    sx = int(ix * scale - view_x)
    sy = int(iy * scale - view_y)
    return sx, sy


def redraw():
    limit_view()

    zoom_img = cv2.resize(
        img,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_LINEAR,
    )

    canvas = np.zeros((win_h, win_w, 3), dtype=np.uint8)

    zoom_h, zoom_w = zoom_img.shape[:2]

    x1 = view_x
    y1 = view_y
    x2 = min(view_x + win_w, zoom_w)
    y2 = min(view_y + win_h, zoom_h)

    crop = zoom_img[y1:y2, x1:x2]
    canvas[0:crop.shape[0], 0:crop.shape[1]] = crop

    for i, (px, py) in enumerate(points):
        sx, sy = image_to_screen(px, py)

        if 0 <= sx < win_w and 0 <= sy < win_h:
            cv2.circle(canvas, (sx, sy), 6, (0, 0, 255), -1)
            cv2.putText(
                canvas,
                f"P{i + 1}({px},{py})",
                (sx + 10, sy - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

    if len(points) >= 2:
        p1 = points[0]
        p2 = points[1]

        sx1, sy1 = image_to_screen(*p1)
        sx2, sy2 = image_to_screen(*p2)

        cv2.line(canvas, (sx1, sy1), (sx2, sy2), (0, 0, 255), 2)

        dist = math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

        cv2.putText(
            canvas,
            f"Pixel Length: {dist:.2f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2,
        )

    cv2.putText(
        canvas,
        f"Scale: {scale:.2f}x  Frame: {img_w}x{img_h}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 0),
        2,
    )

    cv2.imshow("Point Selector", canvas)


def mouse_callback(event, x, y, flags, param):
    global scale, view_x, view_y
    global dragging, last_mouse_x, last_mouse_y
    global points

    if event == cv2.EVENT_LBUTTONDOWN:
        ix, iy = screen_to_image(x, y)

        if len(points) >= 2:
            points = []

        points.append((ix, iy))

        print(f"点{len(points)}: x={ix}, y={iy}")

        if len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]

            dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            print("\n==============================")
            print(f"red_x1, red_y1 = {x1}, {y1}")
            print(f"red_x2, red_y2 = {x2}, {y2}")
            print(f"red_pixel_length = {dist:.2f}")
            print(f"red_line = [{x1}, {y1}, {x2}, {y2}]")
            print("==============================\n")

        redraw()

    elif event == cv2.EVENT_RBUTTONDOWN:
        if points:
            points.pop()
            print("删除最后一个点")
            redraw()

    elif event == cv2.EVENT_MBUTTONDOWN:
        dragging = True
        last_mouse_x = x
        last_mouse_y = y

    elif event == cv2.EVENT_MBUTTONUP:
        dragging = False

    elif event == cv2.EVENT_MOUSEMOVE:
        if dragging:
            dx = x - last_mouse_x
            dy = y - last_mouse_y

            view_x -= dx
            view_y -= dy

            last_mouse_x = x
            last_mouse_y = y

            redraw()

    elif event == cv2.EVENT_MOUSEWHEEL:
        ix, iy = screen_to_image(x, y)

        if flags > 0:
            scale *= 1.25
        else:
            scale /= 1.25

        scale = max(min_scale, min(max_scale, scale))

        view_x = int(ix * scale - x)
        view_y = int(iy * scale - y)

        print(f"当前缩放: {scale:.2f}x")
        redraw()


def print_help():
    print("========== 操作说明 ==========")
    print("鼠标左键: 选点")
    print("鼠标右键: 删除最后一个点")
    print("鼠标滚轮: 放大 / 缩小")
    print("鼠标中键拖动: 平移图像")
    print("键盘 + 或 =: 放大")
    print("键盘 -: 缩小")
    print("W/A/S/D: 平移图像")
    print("R: 重置视图")
    print("C: 清空点")
    print("F: 从流重新抓一帧，仅 --source stream 有效")
    print("Esc: 退出")
    print("==============================")


def build_args():
    parser = argparse.ArgumentParser(description="量取原图或原始流帧上的像素坐标。")
    parser.add_argument(
        "--source",
        choices=("image", "stream"),
        default=None,
        help="读取图片或从视频流抓一帧；默认使用脚本顶部 SOURCE_MODE",
    )
    parser.add_argument("--image-path", default=None, help="图片路径")
    parser.add_argument("--stream-url", default=None, help="RTSP/视频文件/摄像头编号")
    parser.add_argument("--warmup-frames", type=int, default=5, help="拉流后丢弃/预读的帧数")
    return parser.parse_args()


def main():
    global scale, view_x, view_y, points

    args = build_args()

    source = args.source or SOURCE_MODE
    if source not in {"image", "stream"}:
        source = "image"

    if source == "stream":
        stream_url = args.stream_url or CAMERA_URL
        if stream_url is None or stream_url == "":
            raise ValueError("没有摄像头地址，请在像素.py 顶部配置 CAMERA_URL 或传 --stream-url")
        frame, info = read_stream_frame(stream_url, warmup_frames=args.warmup_frames)
    else:
        image_path = args.image_path or IMAGE_PATH or DEFAULT_IMAGE_PATH
        frame, info = read_image_frame(image_path)

    set_image(frame, info)

    cv2.namedWindow("Point Selector", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Point Selector", win_w, win_h)
    cv2.setMouseCallback("Point Selector", mouse_callback)

    redraw()

    print(f"当前来源: {source_info}")
    print(f"原始帧尺寸: {img_w}x{img_h}")
    print_help()

    while True:
        key = cv2.waitKey(20) & 0xFF

        if key == 27:
            break

        elif key == ord("+") or key == ord("="):
            scale *= 1.25
            scale = min(scale, max_scale)
            redraw()

        elif key == ord("-"):
            scale /= 1.25
            scale = max(scale, min_scale)
            redraw()

        elif key == ord("w"):
            view_y -= 80
            redraw()

        elif key == ord("s"):
            view_y += 80
            redraw()

        elif key == ord("a"):
            view_x -= 80
            redraw()

        elif key == ord("d"):
            view_x += 80
            redraw()

        elif key == ord("r"):
            scale = 1.0
            view_x = 0
            view_y = 0
            redraw()

        elif key == ord("c"):
            points = []
            print("已清空点")
            redraw()

        elif key == ord("f") and source == "stream":
            stream_url = args.stream_url or CAMERA_URL
            frame, info = read_stream_frame(stream_url, warmup_frames=args.warmup_frames)
            set_image(frame, info)
            print("已从流重新抓取一帧")
            print(f"原始帧尺寸: {img_w}x{img_h}")
            redraw()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
