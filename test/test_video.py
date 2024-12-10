import math
import shutil
from pathlib import Path

from clipsmith.profiles import GarminDashcamMini2
from clipsmith.video.raw import RAW_CACHE_FILENAME, RawVideo, RawVideoCache

from .conftest import DASHCAM_MINI2_FILENAMES


def test_read(dashcam_mini2_path: Path):
    """
    Read a sample video and verify its metadata.
    """

    sample = RawVideo(
        dashcam_mini2_path / "sample-1.mp4", profile=GarminDashcamMini2
    )

    assert sample.valid
    assert math.isclose(sample.duration, 1.007)


def test_invalid(dashcam_mini2_path: Path):
    """
    Read an invalid sample.
    """

    sample = RawVideo(
        dashcam_mini2_path / "sample-invalid.mp4", profile=GarminDashcamMini2
    )

    assert not sample.valid


def test_cache(dashcam_mini2_path: Path, tmp_path: Path):
    # copy samples to temp path
    for filename in DASHCAM_MINI2_FILENAMES:
        shutil.copy(dashcam_mini2_path / filename, tmp_path / filename)

    cache = RawVideoCache(tmp_path)
    _check_cache(cache)

    # write cache file to temp path
    cache.write()

    # ensure it got written
    cache_path = tmp_path / RAW_CACHE_FILENAME
    assert cache_path.exists()

    # read back from cache
    RawVideoCache(tmp_path)
    _check_cache(cache)


def _check_cache(cache: RawVideoCache):
    assert len(cache.videos) == 4
    assert [v.path.name for v in cache.videos] == DASHCAM_MINI2_FILENAMES

    assert len(cache.valid_videos) == 3
    assert [v.path.name for v in cache.valid_videos] == DASHCAM_MINI2_FILENAMES[
        :3
    ]
