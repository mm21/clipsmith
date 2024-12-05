import math
from pathlib import Path

from clipsmith.profiles import GarminDashcamMini2
from clipsmith.video import RawVideo, RawVideoCache

SAMPLE_FILENAMES = [
    "sample-1.mp4",
    "sample-2.mp4",
    "sample-3.mp4",
    "sample-invalid.mp4",
]
"""
List of sample names.
"""


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


def test_cache(dashcam_mini2_path: Path):
    cache = RawVideoCache(dashcam_mini2_path)

    assert len(cache.videos) == 4
    assert [v.path.name for v in cache.videos] == SAMPLE_FILENAMES

    assert len(cache.valid_videos) == 3
    assert [v.path.name for v in cache.valid_videos] == SAMPLE_FILENAMES[:3]
