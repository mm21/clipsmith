from __future__ import annotations

import subprocess
from abc import ABC
from datetime import datetime as DateTime
from pathlib import Path

from pydantic import BaseModel

from ._ffmpeg import FFPROBE
from .profile import BaseProfile, DefaultProfile


class VideoMetadata(BaseModel):
    """
    Metadata associated with a video file. Can be cached to avoid
    re-processing the video.
    """

    valid: bool
    duration: float
    datetime: tuple[DateTime, DateTime] | None = None

    @classmethod
    def _extract(cls, path: Path, profile: BaseProfile | None) -> VideoMetadata:
        """
        Gets metadata from the given path.
        """

        profile or DefaultProfile()

        cmd = [
            FFPROBE,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ]

        pipes = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = pipes.communicate()
        stdout = stdout.decode()

        if pipes.returncode != 0 or len(stderr) > 0 or len(stdout) == 0:
            valid = False
            duration = 0.0
        else:
            valid = True
            duration = float(stdout)

        # TODO: try to extract datetime based on profile

        return cls(valid=valid, duration=duration)


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
    def datetime(self) -> tuple[DateTime, DateTime] | None:
        """
        Getter for timezone-unaware start/end datetime, if applicable.
        """
        return self.__metadata.datetime


class RawVideo(BaseVideo):
    """
    Encapsulates a single video file.
    """

    def __init__(
        self,
        path: Path,
        metadata: VideoMetadata | None = None,
        profile: BaseProfile | None = None,
    ):
        metadata_ = metadata or VideoMetadata._extract(path, profile)
        super().__init__(path, metadata_)
