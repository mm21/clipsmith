import math
import shutil
from pathlib import Path

from clipsmith import OperationParams
from clipsmith.context import _normalize_inputs
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
    # copy samples to temp path
    shutil.copytree(samples_dir, input_dir, dirs_exist_ok=True)

    # create cache of samples
    cache = RawVideoCache(input_dir)
    _check_cache(cache)

    # write cache file
    cache.write()

    # ensure it got written
    assert (input_dir / RAW_CACHE_FILENAME).is_file()

    # read back into new cache object
    loaded_cache = RawVideoCache(input_dir)
    _check_cache(loaded_cache)


def test_recurse(samples_dir: Path, input_dir: Path):
    """
    Verify collecting inputs from folder recursively.
    """

    last_filename = SAMPLE_FILENAMES[-1]
    last_input_dir = input_dir / "last"

    # copy samples to temp path, except last sample
    for filename in SAMPLE_FILENAMES[:-1]:
        shutil.copy(samples_dir / filename, input_dir / filename)

    # copy last sample
    last_input_dir.mkdir()
    shutil.copy(samples_dir / last_filename, last_input_dir / last_filename)

    # get inputs without recursing
    flat_inputs = _normalize_inputs(input_dir, OperationParams())
    assert [i.path.name for i in flat_inputs] == SAMPLE_FILENAMES[:-1]

    # get inputs with recursing
    recurse_inputs = _normalize_inputs(input_dir, OperationParams(recurse=True))
    assert [i.path.name for i in recurse_inputs] == SAMPLE_FILENAMES


def _check_cache(cache: RawVideoCache):
    assert [v.path.name for v in cache.videos] == SAMPLE_FILENAMES

    for video in cache.videos:
        assert video.path.is_file()
