import subprocess
from pathlib import Path

from .conftest import DASHCAM_MINI2_PATH


def test_forge(output_dir: Path):
    """
    Create a new clip from inputs, scaling resolution.
    """

    inputs = DASHCAM_MINI2_PATH
    output = output_dir / "clip.mp4"

    assert not output.is_file()

    subprocess.check_call(
        [
            "clipsmith",
            "forge",
            "--res-target",
            "480:270",
            str(inputs),
            str(output),
        ]
    )
    assert output.is_file()
