from __future__ import annotations

import subprocess
from abc import ABC
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel

from ._ffmpeg import FFPROBE_PATH
from .profile import BaseProfile, DefaultProfile

__all__ = [
    "BaseVideo",
    "RawVideoMetadata",
    "RawVideo",
]

RAW_CACHE_FILENAME = ".clipsmith_cache.yaml"


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
        if start := self.__datetime_start:
            return start + TimeDelta(seconds=self.duration)
        return None

    @property
    def datetime_range(self) -> tuple[DateTime, DateTime] | None:
        if start := self.datetime_start:
            end = self.datetime_end
            assert end is not None
            return (start, end)
        return None

    def _extract_duration(self):
        """
        Get duration from existing file.
        """
        duration, valid = _extract_duration(self.path)
        assert valid
        self.__duration = duration


class RawVideoMetadata(BaseModel):
    """
    Metadata associated with a raw video file. Can be cached to avoid
    re-processing the video.
    """

    filename: str
    valid: bool
    duration: float | None
    resolution: tuple[int, int] | None
    datetime_start: tuple[DateTime, DateTime] | None = None

    @classmethod
    def _extract(
        cls, path: Path, profile: BaseProfile | None = None
    ) -> RawVideoMetadata:
        """
        Gets metadata from the given path.
        """

        profile or DefaultProfile()

        duration, duration_valid = _extract_duration(path.resolve())
        res, res_valid = _extract_res(path.resolve())

        valid = duration_valid and res_valid

        # TODO: try to extract datetime_start based on profile

        return cls(
            filename=path.name, valid=valid, duration=duration, resolution=res
        )


class RawVideo(BaseVideo):
    """
    Encapsulates a single pre-existing video file.
    """

    __metadata: RawVideoMetadata

    def __init__(
        self,
        path: Path,
        profile: BaseProfile | None = None,
        metadata: RawVideoMetadata | None = None,
    ):
        """
        Create a new raw video from a file, using profile to extract
        metadata if not given.
        """
        meta = metadata or RawVideoMetadata._extract(path, profile=profile)

        super().__init__(
            path,
            meta.resolution,
            duration=meta.duration,
            datetime_start=meta.datetime_start,
        )

        self.__metadata = meta

    @property
    def valid(self) -> bool:
        return self.__metadata.valid


class RawVideoCacheModel(BaseModel):
    """
    Represents a video cache file.
    """

    videos: list[RawVideoMetadata]

    @classmethod
    def _from_folder(cls, folder_path: Path) -> Self:
        """
        Get model from folder, using the existing cache if present.
        """

        cache_path = folder_path / RAW_CACHE_FILENAME

        if cache_path.exists():
            # load from cache
            with cache_path.open() as fh:
                model_dict = yaml.safe_load(fh)

            return cls(**model_dict)
        else:
            # get models from videos
            files = sorted(folder_path.iterdir(), key=lambda p: p.name)
            video_models: list[RawVideoMetadata] = [
                RawVideoMetadata._extract(p)
                for p in files
                if p.is_file() and not p.name.startswith(".")
            ]

            return cls(videos=video_models)


class RawVideoCache:
    folder_path: Path
    videos: list[RawVideo]

    __model: RawVideoCacheModel

    def __init__(self, folder_path: Path):
        assert folder_path.is_dir()

        self.folder_path = folder_path
        self.__model = RawVideoCacheModel._from_folder(folder_path)

        # create video instances from metadata
        self.videos = [
            RawVideo(self.folder_path / m.filename, metadata=m)
            for m in self.__model.videos
        ]

    @property
    def valid_videos(self) -> list[RawVideo]:
        """
        Get a filtered list of raw videos.
        """
        return [v for v in self.videos if v.valid]

    def write(self):
        """
        Write .yaml cache of video listing.
        """
        cache_path = self.folder_path / RAW_CACHE_FILENAME
        with cache_path.open("w") as fh:
            yaml.safe_dump(
                self.__model.model_dump(),
                fh,
                default_flow_style=False,
                sort_keys=False,
            )


def _extract_duration(path: Path) -> tuple[float | None, bool]:
    """
    Get duration and validity.
    """
    assert path.exists()

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
        duration = None
        valid = False
    else:
        duration = float(stdout)
        valid = True

    return (duration, valid)


def _extract_res(path: Path) -> tuple[tuple[int, int] | None, bool]:
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
        res = None
        valid = False
    else:
        split = stdout.split(",")
        assert len(split) == 2
        res = int(split[0]), int(split[1])
        valid = True

    return (res, valid)
