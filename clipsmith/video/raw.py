from __future__ import annotations

import logging
from datetime import datetime as DateTime
from functools import cached_property
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel

from ..profile import BaseProfile
from .base import BaseVideo, extract_duration, extract_res

__all__ = [
    "BaseVideo",
    "RawVideoMetadata",
    "RawVideo",
]

RAW_CACHE_FILENAME = ".clipsmith_cache.yaml"

VIDEO_SUFFIXES = [
    ".mp4",
]

SAMPLE_INTERVAL = 1.0
"""
Interval at which to sample frames for processing.
"""

WINDOW_SIZE = 5
"""
Number of frames in rolling window for processing.
"""

SSIM_THRESHOLD = 0.7
"""
Structural similarity threshold below which movement is detected.
"""


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

        duration, duration_valid = extract_duration(path.resolve())
        res, res_valid = extract_res(path.resolve())

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

    @cached_property
    def bg_changed(self) -> bool:
        """
        Analyze video and return whether the background changed. For dashcam
        footage, this should be False if the car was parked for the entire
        clip.
        """
        import cv2
        import numpy as np
        from skimage.metrics import structural_similarity as ssim

        capture = cv2.VideoCapture(self.path)
        fps = capture.get(cv2.CAP_PROP_FPS)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = int(fps * SAMPLE_INTERVAL)

        frame_buffer = []
        ssim_scores = []

        print(f"--- frame_count={frame_count}, frame_interval={frame_interval}")

        for frame_index in range(0, frame_count, frame_interval):
            print(f"--- checking frame: {frame_index}")

            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = capture.read()
            assert ret

            frame = cv2.resize(frame, (320, 240))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Add to buffer
            frame_buffer.append(gray)

            # Keep only last N frames
            if len(frame_buffer) > WINDOW_SIZE:
                frame_buffer.pop(0)

            # Compare with all frames in buffer (except current)
            if len(frame_buffer) > 1:
                current_scores = []
                for prev_frame in frame_buffer[:-1]:
                    score = ssim(prev_frame, gray)
                    current_scores.append(score)

                # Use minimum SSIM (most different comparison)
                min_ssim = min(current_scores)
                ssim_scores.append(min_ssim)

                print(f"--- min_ssim: {min_ssim}")

        capture.release()

        avg_ssim = np.median(ssim_scores) if ssim_scores else 1.0
        print(f"--- avg_ssim: {avg_ssim}")
        return avg_ssim < SSIM_THRESHOLD


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
        else:
            # get models from videos
            logging.info(f"Checking inputs from folder: '{folder_path}'")

            files: list[Path] = []

            for dirpath, _, filenames in folder_path.walk():
                for filename in filenames:
                    file_path = dirpath / filename
                    if (
                        not file_path.name.startswith(".")
                        and file_path.suffix.lower() in VIDEO_SUFFIXES
                    ):
                        files.append(file_path)

            files.sort(key=lambda p: str(p))

            video_models: list[RawVideoMetadata] = [
                RawVideoMetadata._extract(p, root_path=folder_path)
                for p in files
            ]

            for model in video_models:
                if not model.valid:
                    logging.info(
                        f"-> Found invalid input: '{folder_path / model.filename}'"
                    )

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

        valid_videos = self.valid_videos

        logging.info(
            f"-> Found inputs: {len(valid_videos)} valid, {len(self.videos) - len(valid_videos)} invalid"
        )

    @property
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
