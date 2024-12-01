import math
from pathlib import Path

from clipsmith.profiles import GarminDashcamMini2
from clipsmith.video import RawVideo


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
