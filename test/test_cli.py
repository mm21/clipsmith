import subprocess
from pathlib import Path

from pytest import raises


def test_forge(samples_dir: Path, output_dir: Path):
    """
    Create a new clip from inputs, scaling resolution.
    """
    output = output_dir / "clip.mp4"
    assert not output.is_file()

    subprocess.check_call(
        [
            "clipsmith",
            "forge",
            "--res-target",
            "480:270",
            str(samples_dir),
            str(output),
        ]
    )
    assert output.is_file()


def test_module():
    """
    Verify invocation by module.
    """
    subprocess.check_call(["python", "-m", "clipsmith.cli.main"])


def test_fail(samples_dir: Path, output_dir: Path):
    """
    Verify doit failure via invalid filename.
    """
    invalid_output = output_dir / "EXPECTED-ERROR:"

    with raises(subprocess.CalledProcessError):
        subprocess.check_call(
            ["clipsmith", "forge", str(samples_dir), str(invalid_output)]
        )
