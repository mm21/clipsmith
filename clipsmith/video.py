from __future__ import annotations

import subprocess
from abc import ABC
from datetime import datetime as DateTime
from pathlib import Path

from pydantic import BaseModel

from ._ffmpeg import FFPROBE_PATH
from .profile import BaseProfile, DefaultProfile


def _extract_duration(path: Path) -> tuple[float, bool]:
    """
    Get duration and validity.
    """
    cmd = [
        FFPROBE_PATH,
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
        duration = 0.0
        valid = False
    else:
        duration = float(stdout)
        valid = True

    return (duration, valid)


def _extract_res(path: Path) -> tuple[tuple[int, int], bool]:
    """
    Extract resolution and validity.
    """

    cmd = [
        FFPROBE_PATH,
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
        res = (0, 0)
        valid = False
    else:
        res = map(int, stdout.split(","))
        valid = True

    return (res, valid)


class VideoMetadata(BaseModel):
    """
    Metadata associated with a video file. Can be cached to avoid
    re-processing the video.
    """

    valid: bool
    duration: float
    resolution: tuple[int, int]
    datetime: tuple[DateTime, DateTime] | None = None

    @classmethod
    def _extract(cls, path: Path, profile: BaseProfile | None) -> VideoMetadata:
        """
        Gets metadata from the given path.
        """

        profile or DefaultProfile()

        duration, duration_valid = _extract_duration(path.resolve())
        res, res_valid = _extract_res(path.resolve())

        valid = duration_valid and res_valid

        # TODO: try to extract datetime based on profile

        return cls(valid=valid, duration=duration, resolution=res)


class BaseVideo(ABC):
    __path: Path
    __metadata: VideoMetadata

    def __init__(self, path: Path, metadata: VideoMetadata):
        self.__path = path
        self.__metadata = metadata

    def __repr__(self) -> str:
        return f"{type(self).__name__}(path={self.__path}, metadata={{{self.__metadata}}})"

    @property
    def path(self) -> Path:
        """
        Path to file for this video.
        """
        return self.__path

    @property
    def valid(self) -> bool:
        return self.__metadata.valid

    @property
    def duration(self) -> float:
        """
        Getter for duration in seconds.
        """
        return self.__metadata.duration

    @property
    def resolution(self) -> tuple[int, int]:
        return self.__metadata.resolution

    @property
    def datetime(self) -> tuple[DateTime, DateTime] | None:
        """
        Getter for timezone-unaware start/end datetime, if applicable.
        """
        return self.__metadata.datetime


class RawVideo(BaseVideo):
    """
    Encapsulates a single pre-existing video file.
    """

    def __init__(
        self,
        path: Path,
        profile: BaseProfile | None = None,
        metadata: VideoMetadata | None = None,
    ):
        """
        Create a new raw video from a file, using profile to extract
        metadata if metadata is not explicitly given.
        """
        metadata_ = metadata or VideoMetadata._extract(path, profile)
        super().__init__(path, metadata_)

    @classmethod
    def from_folder(
        self, path: Path, profile: BaseProfile | None = None
    ) -> list[RawVideo]:
        """
        Get list of raw videos from a folder.

        Attempts to read from the .yaml cache first, and creates it after
        processing if it doesn't exist.
        """
