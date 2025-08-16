import logging
import math
import shutil
from pathlib import Path

from pytest import FixtureRequest, Parser, fixture

from clipsmith.clip.clip import Clip
from clipsmith.context import Context
from clipsmith.profiles import GarminDashcamMini2
from clipsmith.video.raw import RawVideo

pytest_plugins = ["pytest_powerpack"]

TEST_ROOT = Path(__file__).parent
SAMPLES_DIR = TEST_ROOT / "_samples" / "garmin-dashcam-mini2"
TEMP_DIR = TEST_ROOT / "__temp__"

SAMPLE_FILENAMES = [
    p.name
    for p in sorted(SAMPLES_DIR.iterdir(), key=lambda p: p.name)
    if not p.name.startswith(".")
]

logging.basicConfig(level=logging.DEBUG)


def pytest_addoption(parser: Parser):
    parser.addoption(
        "--keep-temp",
        action="store_true",
        help="Place temp folders under test/__temp__ for manual inspection",
    )


@fixture
def input_dir(temp_dir: Path) -> Path:
    """
    Get temp dir in which to place inputs.
    """
    return _setup_dir(temp_dir / "__input__")


@fixture
def output_dir(temp_dir: Path) -> Path:
    """
    Get temp dir in which to place outputs.
    """
    return _setup_dir(temp_dir / "__output__")


@fixture
def temp_dir(tmp_path: Path, rel_path: Path, keep_temp: bool) -> Path:
    """
    Temp folder provided by system, or located under the test folder if
    --keep-temp is passed.
    """
    if keep_temp:
        return TEMP_DIR / rel_path
    else:
        return tmp_path


@fixture
def samples_dir() -> Path:
    return SAMPLES_DIR


@fixture
def context() -> Context:
    """
    Get a context.
    """
    return Context()


@fixture
def rel_path(request: FixtureRequest) -> Path:
    """
    Get relative path to this test for placing output folder.
    """
    fspath = Path(request.node.fspath)
    test_path = fspath.parent / fspath.stem / str(request.node.name)
    return test_path.relative_to(TEST_ROOT)


@fixture
def keep_temp(request: FixtureRequest) -> bool:
    """
    Keep temps under test folder if flag was passed.
    """
    return bool(request.config.getoption("--keep-temp"))


def check_clip(
    clip: Clip, duration_expect: float | None = None, rel_tol: float = 0.1
):
    """
    Verify the clip with approximate expected duration.
    """

    assert clip.path.is_file()

    # read raw video
    video = RawVideo(clip.path)

    # compare duration read from raw video
    assert math.isclose(video.duration, clip.duration)

    # compare approx duration
    if duration_expect is not None:
        assert math.isclose(clip.duration, duration_expect, rel_tol=rel_tol)

    # compare resolution
    assert clip.resolution == video.resolution


def get_inputs(count: int | None = None) -> list[RawVideo]:
    """
    Get the provided number of samples as raw videos.
    """
    count_ = count or len(SAMPLE_FILENAMES) - 1  # exclude invalid sample
    return [
        RawVideo(SAMPLES_DIR / file, profile=GarminDashcamMini2)
        for file in SAMPLE_FILENAMES[:count_]
    ]


def _setup_dir(setup_path: Path) -> Path:
    """
    Ensure this folder exists and is empty.
    """
    setup_path.mkdir(parents=True, exist_ok=True)

    for path in setup_path.iterdir():
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)

    return setup_path
