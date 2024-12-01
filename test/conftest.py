from pathlib import Path

from pytest import fixture

pytest_plugins = ["pytest_powerpack"]

TEST_ROOT = Path(__file__).parent


@fixture
def samples_path() -> Path:
    return TEST_ROOT / "_samples"


@fixture
def dashcam_mini2_path(samples_path: Path) -> Path:
    return samples_path / "garmin-dashcam-mini2"
