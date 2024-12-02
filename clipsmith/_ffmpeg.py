"""
Utility to wrap finding and validating path to ffmpeg.
"""

import shutil

ffmpeg = shutil.which("ffmpeg")
ffprobe = shutil.which("ffprobe")

if ffmpeg is None or ffprobe is None:
    raise Exception(f"Dependencies not met: ffmpeg={ffmpeg}, ffprobe={ffprobe}")

FFMPEG_PATH = ffmpeg
FFPROBE_PATH = ffprobe
