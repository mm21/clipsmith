from __future__ import annotations

from abc import ABC
from datetime import datetime as DateTime
from pathlib import Path

from pydantic import BaseModel

from .profile import BaseProfile, DefaultProfile


class VideoMetadata(BaseModel):
    """
    Metadata associated with a video file. Can be cached to avoid
    re-processing the video.
    """

    duration: float
    datetime: tuple[DateTime, DateTime] | None = None

    @classmethod
    def _extract(cls, path: Path, profile: BaseProfile | None) -> VideoMetadata:
        """
        Gets metadata from the given path.
        """

        profile or DefaultProfile()

        # TODO

        return cls()


class BaseVideo(ABC):
    __path: Path
    __metadata: VideoMetadata

    def __init__(self, path: Path, metadata: VideoMetadata):
        self.__path = path
        self.__metadata = metadata

    @property
    def path(self) -> Path:
        """
        Path to file for this video.
        """
        return self.__path

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
