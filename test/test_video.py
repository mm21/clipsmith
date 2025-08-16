import math
import shutil
from pathlib import Path

from clipsmith.profiles import GarminDashcamMini2
from clipsmith.video.raw import RAW_CACHE_FILENAME, RawVideo, RawVideoCache

from .conftest import SAMPLE_FILENAMES


def test_read(samples_dir: Path):
    """
    Read a sample video and verify its metadata.
    """

    sample = RawVideo(samples_dir / "sample-1.mp4", profile=GarminDashcamMini2)

    assert sample.valid
    assert math.isclose(sample.duration, 1.007)


def test_invalid(samples_dir: Path):
    """
    Read an invalid sample.
    """

    sample = RawVideo(
        samples_dir / "sample-invalid.mp4", profile=GarminDashcamMini2
    )

    assert not sample.valid


def test_cache(samples_dir: Path, input_dir: Path):
    sample_2 = samples_dir / "sample-2.mp4"
    sample_2_folder = input_dir / "sample-2"

    # copy samples to temp path, putting sample 2 under a subfolder
    for filename in [f for f in SAMPLE_FILENAMES if f != sample_2.name]:
        shutil.copy(samples_dir / filename, input_dir / filename)

    sample_2_folder.mkdir()
    shutil.copy(samples_dir / sample_2.name, sample_2_folder / sample_2.name)

    cache = RawVideoCache(input_dir)
    _check_cache(cache)

    # write cache file to temp path
    cache.write()

    # ensure it got written
    cache_path = input_dir / RAW_CACHE_FILENAME
    assert cache_path.exists()

    # read back from cache
    cache_readback = RawVideoCache(input_dir)
    _check_cache(cache_readback)


def _check_cache(cache: RawVideoCache):
    assert len(cache.videos) == 4
    assert [v.path.name for v in cache.videos] == SAMPLE_FILENAMES

    assert len(cache.valid_videos) == 3
    assert [v.path.name for v in cache.valid_videos] == SAMPLE_FILENAMES[:3]

    for video in cache.videos:
        assert video.path.is_file()
