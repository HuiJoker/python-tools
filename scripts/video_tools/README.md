# Video Tools

Small Python utilities for video clipping and frame extraction.

## Requirements

Install OpenCV before running the frame extraction scripts:

```powershell
python -m pip install opencv-python
```

`clip_video_and_extract_frames.py` also requires `ffmpeg` to be installed and available on `PATH`.

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

## Clip Video And Extract Frames

Clip a video segment, then extract one JPG frame per second from the clipped video:

```powershell
python clip_video_and_extract_frames.py "F:\path\to\input.mp4" "F:\path\to\clip.mp4" "F:\path\to\frames" --start "00:03:57" --end "00:04:31" --interval-seconds 1 --prefix cut
```

Use `--reencode` if stream copy produces inaccurate clip boundaries or an unplayable output video.

If the clipped video already exists, skip the ffmpeg step and only extract frames:

```powershell
python clip_video_and_extract_frames.py "F:\path\to\input.mp4" "F:\path\to\clip.mp4" "F:\path\to\frames" --start "00:03:57" --end "00:04:31" --skip-clip
```
