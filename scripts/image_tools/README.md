# Image Tools

Small utilities for image inspection and pixel-level measurements.

## Pixel Distance Selector

Open an image and interactively select two points to print their original-image coordinates and pixel distance:

```powershell
python pixel_distance_selector.py --image "F:\path\to\image.jpg"
```

Read one frame from a camera, RTSP stream, or video source:

```powershell
python pixel_distance_selector.py --stream "0"
python pixel_distance_selector.py --stream "rtsp://user:password@192.168.1.10:554/stream1"
```

Controls:

- Left mouse: select point
- Right mouse: remove last point
- Mouse wheel: zoom in/out
- Middle mouse drag: pan
- `+` or `=`: zoom in
- `-`: zoom out
- `W/A/S/D`: pan
- `R`: reset view
- `C`: clear points
- `Esc`: exit

Requirements:

```powershell
python -m pip install opencv-python numpy
```
