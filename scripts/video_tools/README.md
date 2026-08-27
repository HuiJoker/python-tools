# Video Tools

Small Python utilities for video clipping and frame extraction.

## Requirements

Install OpenCV before running the frame extraction script:

```powershell
python -m pip install opencv-python
```

## Extract Frames

Extract one JPG frame per second from a video:

```powershell
python extract_video_frames.py "F:\path\to\video.mp4" "F:\path\to\frames" --interval-seconds 1
```

Extract frames from every supported video in a folder:

```powershell
python extract_video_frames.py "F:\path\to\videos" "F:\path\to\frames" --interval-seconds 1
```

Include subfolders:

```powershell
python extract_video_frames.py "F:\path\to\videos" "F:\path\to\frames" --recursive
```

Save all images directly into the output folder:

```powershell
python extract_video_frames.py "F:\path\to\videos" "F:\path\to\frames" --flat
```
