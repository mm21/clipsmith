from pathlib import Path

from clipsmith.profiles import GarminDashcamMini2
from clipsmith.video import RawVideo


def test_read(dashcam_mini2_path: Path):
    """
    Read a sample video and verify its metadata.
    """

    sample_1 = RawVideo(
        dashcam_mini2_path / "sample-1.mp4", profile=GarminDashcamMini2
    )
