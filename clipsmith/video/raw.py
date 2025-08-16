from __future__ import annotations

import logging
from datetime import datetime as DateTime
from functools import cached_property
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel

from ..profile import BaseProfile
from .base import BaseVideo, _extract_duration, _extract_res

__all__ = [
    "BaseVideo",
    "RawVideoMetadata",
    "RawVideo",
]

RAW_CACHE_FILENAME = ".clipsmith_cache.yaml"

VIDEO_SUFFIXES = [
    ".mp4",
]


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
        cls,
        path: Path,
        *,
        root_path: Path | None = None,
        profile: BaseProfile | None = None,
    ) -> RawVideoMetadata:
        """
        Gets metadata from the given path.
        """

        duration, duration_valid = _extract_duration(path.resolve())
        res, res_valid = _extract_res(path.resolve())

        valid = duration_valid and res_valid

        # TODO: try to extract datetime_start based on profile

        rel_filename = (
            path.name if root_path is None else str(path.relative_to(root_path))
        )

        return cls(
            filename=rel_filename,
            valid=valid,
            duration=duration,
            resolution=res,
        )


class RawVideo(BaseVideo):
    """
    Encapsulates a single pre-existing video file.
    """

    __metadata: RawVideoMetadata

    def __init__(
        self,
        path: Path,
        *,
        metadata: RawVideoMetadata | None = None,
        profile: BaseProfile | None = None,
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
            logging.info(f"Loading inputs from cache: '{cache_path}'")

            # load from cache
            with cache_path.open() as fh:
                model_dict = yaml.safe_load(fh)

            return cls(**model_dict)

        # get models from videos
        logging.info(f"Scanning inputs from folder: '{folder_path}'")

        files = sorted(
            (
                p
                for p in folder_path.iterdir()
                if p.is_file()
                and not p.name.startswith(".")
                and p.suffix.lower() in VIDEO_SUFFIXES
            ),
            key=lambda p: p.name,
        )

        video_models = [
            RawVideoMetadata._extract(p, root_path=folder_path) for p in files
        ]

        for model in video_models:
            if not model.valid:
                logging.warning(
                    f"-> Found invalid input: '{folder_path / model.filename}'"
                )

        return cls(videos=video_models)


class RawVideoCache:
    """
    Cache of videos from a single folder.
    """

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

        valid_count = len(self.valid_videos)
        invalid_count = len(self.videos) - len(self.valid_videos)
        logging.info(f"-> {valid_count} valid, {invalid_count} invalid")

    @cached_property
    def valid_videos(self) -> list[RawVideo]:
        """
        Get a filtered list of raw videos.
        """
        return [v for v in self.videos if v.valid]

    @property
    def cache_path(self) -> Path:
        """
        Path to this cache's .yaml file.
        """
        return self.folder_path / RAW_CACHE_FILENAME

    def write(self):
        """
        Write .yaml cache of video listing.
        """
        logging.info(f"Writing cache: {self.cache_path}")
        with self.cache_path.open("w") as fh:
            yaml.safe_dump(
                self.__model.model_dump(),
                fh,
                default_flow_style=False,
                sort_keys=False,
            )
