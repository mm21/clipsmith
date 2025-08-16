from __future__ import annotations

import subprocess
from abc import ABC
from datetime import datetime as DateTime
from pathlib import Path

from .._ffmpeg import get_ffprobe

__all__ = [
    "BaseVideo",
    "RawVideoMetadata",
    "RawVideo",
]


class BaseVideo(ABC):
    __path: Path
    __resolution: tuple[int, int]
    __duration: float | None
    __datetime_start: DateTime | None

    def __init__(
        self,
        path: Path,
        resolution: tuple[int, int],
        duration: float | None = None,
        datetime_start: DateTime | None = None,
    ):
        self.__path = path
        self.__resolution = resolution
        self.__duration = duration
        self.__datetime_start = datetime_start

    def __repr__(self) -> str:
        return f"{type(self).__name__}(path={self.__path})"

    @property
    def path(self) -> Path:
        """
        Path to file for this video.
        """
        return self.__path

    @property
    def resolution(self) -> tuple[int, int]:
        """
        Video resolution as width, height.
        """
        return self.__resolution

    @property
    def duration(self) -> float:
        """
        Getter for duration in seconds.

        :raises ValueError: If duration has not been set (file does not exist yet)
        """
        if self.__duration is None:
            raise ValueError(f"Video has no duration: {self}")
        return self.__duration

    @property
    def datetime_start(self) -> DateTime | None:
        """
        Getter for timezone-unaware start datetime, if applicable.
        """
        return self.__datetime_start

    @property
    def datetime_end(self) -> DateTime | None:
        """
        Getter for timezone-unaware end datetime, if applicable.
        """
        # if start := self.__datetime_start:
        #    return start + TimeDelta(seconds=self.duration)
        return None

    @property
    def datetime_range(self) -> tuple[DateTime, DateTime] | None:
        """
        Getter for timezone-unaware datetime range, if applicable.
        """
        # if start := self.datetime_start:
        #    end = self.datetime_end
        #    assert end is not None
        #    return (start, end)
        return None

    def _extract_duration(self):
        """
        Get duration from existing file.
        """
        duration, valid = extract_duration(self.path)
        assert valid
        self.__duration = duration


def extract_duration(path: Path) -> tuple[float | None, bool]:
    """
    Get duration and validity.
    """
    assert path.exists()

    cmd = [
        get_ffprobe(),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]

    pipes = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = pipes.communicate()
    stdout = stdout.decode()

    if pipes.returncode != 0 or len(stderr) > 0 or len(stdout) == 0:
        duration = None
        valid = False
    else:
        duration = float(stdout)
        valid = True

    return (duration, valid)


def extract_res(path: Path) -> tuple[tuple[int, int] | None, bool]:
    """
    Extract resolution and validity.
    """

    cmd = [
        get_ffprobe(),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0",
        str(path),
    ]

    pipes = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = pipes.communicate()
    stdout = stdout.decode().strip()

    if pipes.returncode != 0 or len(stderr) > 0 or len(stdout) == 0:
        res = None
        valid = False
    else:
        split = stdout.split(",")
        assert len(split) == 2
        res = int(split[0]), int(split[1])
        valid = True

    return (res, valid)
