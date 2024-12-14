import shutil
import subprocess
from pathlib import Path

from pytest import raises

from .conftest import DASHCAM_MINI2_PATH


def test_forge(output_dir: Path, dashcam_mini2_path: Path, tmp_path: Path):
    """
    Create a new clip from inputs, scaling resolution.
    """

    # copy samples to temp path to write cache
    inputs = shutil.copytree(dashcam_mini2_path, tmp_path / "inputs")
    output = output_dir / "clip.mp4"

    assert not output.is_file()

    subprocess.check_call(
        [
            "clipsmith",
            "forge",
            "--res-target",
            "480:270",
            "--cache",
            str(inputs),
            str(output),
        ]
    )
    assert output.is_file()


def test_module():
    """
    Verify invocation by module.
    """
    subprocess.check_call(["python", "-m", "clipsmith.cli.main"])


def test_fail(output_dir: Path):
    """
    Verify doit failure via invalid filename.
    """

    inputs = DASHCAM_MINI2_PATH
    invalid_output = output_dir / "EXPECTED-ERROR:"

    with raises(subprocess.CalledProcessError):
        subprocess.check_call(["clipsmith", "forge", inputs, invalid_output])
