from pathlib import Path

from pytest import FixtureRequest, fixture

pytest_plugins = ["pytest_powerpack"]

TEST_ROOT = Path(__file__).parent
OUTPUT_PATH = TEST_ROOT / "__out__"


@fixture
def samples_path() -> Path:
    return TEST_ROOT / "_samples"


@fixture
def dashcam_mini2_path(samples_path: Path) -> Path:
    return samples_path / "garmin-dashcam-mini2"


@fixture
def output_dir(request: FixtureRequest) -> Path:
    # get path to this test
    fspath = Path(request.node.fspath)
    testcase_path = fspath.parent / fspath.stem / str(request.node.name)

    # get output path and ensure it exists
    output_path = OUTPUT_PATH / testcase_path.relative_to(TEST_ROOT)
    output_path.mkdir(parents=True, exist_ok=True)

    return output_path
