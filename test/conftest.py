import logging
import math
import shutil
from pathlib import Path

from pytest import FixtureRequest, fixture

from clipsmith.clip import Clip
from clipsmith.context import Context
from clipsmith.video import RawVideo

pytest_plugins = ["pytest_powerpack"]

TEST_ROOT = Path(__file__).parent
OUTPUT_PATH = TEST_ROOT / "__out__"
SAMPLES_PATH = TEST_ROOT / "_samples"
DASHCAM_MINI2_PATH = SAMPLES_PATH / "garmin-dashcam-mini2"


logging.basicConfig(level=logging.DEBUG)


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

    # clean all files in it
    for path in output_path.iterdir():
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)

    return output_path


@fixture
def context() -> Context:
    """
    Get a context.
    """
    return Context()


def check_clip(clip: Clip, duration_expect: float):
    """
    Verify the clip with approximate expected duration.
    """

    assert clip.path.is_file()

    # read raw video and compare
    video = RawVideo(clip.path)
    assert math.isclose(video.duration, clip.duration)

    # compare against approx duration
    assert math.isclose(clip.duration, duration_expect, rel_tol=0.1)
