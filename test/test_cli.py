import subprocess
import sys
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
    # click >= 8.2 treats "no subcommand given" as a usage error (exit 2) while
    # still printing help
    proc = subprocess.run(
        [sys.executable, "-m", "clipsmith.cli.main"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "Usage:" in proc.stdout


def test_fail(samples_dir: Path, output_dir: Path):
    """
    Verify doit failure via invalid filename.
    """
    invalid_output = output_dir / "EXPECTED-ERROR:"

    with raises(subprocess.CalledProcessError):
        subprocess.check_call(
            ["clipsmith", "forge", str(samples_dir), str(invalid_output)]
        )
