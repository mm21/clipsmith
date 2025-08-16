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


def test_bg_changed(dashcam_mini2_path: Path):
    sample_1 = dashcam_mini2_path / "sample-1.mp4"
    sample_parked = dashcam_mini2_path / "sample-parked.mp4"
    sample_driving = dashcam_mini2_path / "sample-driving.mp4"

    RawVideo(sample_1)
    video_parked = RawVideo(sample_parked)
    video_driving = RawVideo(sample_driving)

    print(f"--- video_parked changed: {video_parked.bg_changed}")
    print(f"--- video_driving changed: {video_driving.bg_changed}")


def test_cache(dashcam_mini2_path: Path, tmp_path: Path):
    sample_2 = dashcam_mini2_path / "sample-2.mp4"
    sample_2_folder = tmp_path / "sample-2"

    # copy samples to temp path, putting sample 2 under a subfolder
    for filename in [f for f in DASHCAM_MINI2_FILENAMES if f != sample_2.name]:
        shutil.copy(dashcam_mini2_path / filename, tmp_path / filename)

    sample_2_folder.mkdir(exist_ok=True)
    shutil.copy(
        dashcam_mini2_path / sample_2.name, sample_2_folder / sample_2.name
    )

    cache = RawVideoCache(tmp_path)
    _check_cache(cache)

    # write cache file to temp path
    cache.write()

    # ensure it got written
    cache_path = tmp_path / RAW_CACHE_FILENAME
    assert cache_path.exists()

    # read back from cache
    cache_readback = RawVideoCache(tmp_path)
    _check_cache(cache_readback)


def _check_cache(cache: RawVideoCache):
    assert len(cache.videos) == 4
    assert [v.path.name for v in cache.videos] == DASHCAM_MINI2_FILENAMES

    assert len(cache.valid_videos) == 3
    assert [v.path.name for v in cache.valid_videos] == DASHCAM_MINI2_FILENAMES[
        :3
    ]

    for video in cache.videos:
        assert video.path.is_file()
