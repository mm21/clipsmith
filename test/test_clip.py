import math
from pathlib import Path

from clipsmith.clip import DurationParams, OperationParams
from clipsmith.context import Context
from clipsmith.profiles import BaseProfile, GarminDashcamMini2
from clipsmith.video import RawVideo


def test_forge(dashcam_mini2_path: Path, output_dir: Path):
    """
    Forge a new clip by concatenating inputs.
    """

    inputs = _get_inputs(dashcam_mini2_path, GarminDashcamMini2)[:2]
    context = Context()
    operation = OperationParams()

    clip = context.forge(output_dir / "clip.mp4", inputs, operation)
    context.doit()

    assert clip.path.is_file()

    # read video and confirm it's as expectd
    video = RawVideo(clip.path)
    assert math.isclose(video.duration, 1.007 * 2)


def test_timelapse(dashcam_mini2_path: Path, output_dir: Path):
    """
    Forge a new clip by concatenating inputs and rescaling time.
    """

    inputs = _get_inputs(dashcam_mini2_path, GarminDashcamMini2)[:2]
    context = Context()
    operation = OperationParams(
        duration_params=DurationParams(time_scale=5),
        audio=False,
    )

    clip = context.forge(output_dir / "clip.mp4", inputs, operation)
    context.doit()

    assert clip.path.is_file()

    # read video and confirm it's as expectd
    video = RawVideo(clip.path)
    assert math.isclose(video.duration, 1.007 * 2 * 5)


def test_invalid(dashcam_mini2_path: Path):
    """
    Forge a new clip by concatenating inputs, with one input being
    invalid.
    """


def test_folder(dashcam_mini2_path: Path):
    """
    Forge a new clip by concatenating inputs from a folder.
    """


def _get_inputs(path: Path, profile: BaseProfile) -> list[RawVideo]:
    files = [
        "sample-1.mp4",
        "sample-2.mp4",
        "sample-3.mp4",
        "sample-invalid.mp4",
    ]
    return [RawVideo(path / file, profile=profile) for file in files]
