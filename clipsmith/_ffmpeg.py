"""
Utility to wrap finding and validating path to ffmpeg.
"""

import shutil
from functools import lru_cache


def get_ffmpeg() -> str:
    return _get_command("ffmpeg")


def get_ffprobe() -> str:
    return _get_command("ffprobe")


@lru_cache()
def _get_command(cmd: str) -> str:
    path = shutil.which(cmd)
    if path is None:
        raise RuntimeError(
            f"Could not find required command in system PATH: {cmd}"
        )
    return path
