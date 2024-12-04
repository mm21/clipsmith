import math
from pathlib import Path

from clipsmith.clip import DurationParams, OperationParams
from clipsmith.context import Context
from clipsmith.profiles import GarminDashcamMini2
from clipsmith.video import RawVideo


def test_concat(dashcam_mini2_path: Path, output_dir: Path):
    """
    Forge a new clip by concatenating inputs.
    """

    output = output_dir / "clip.mp4"
    inputs = _get_inputs(dashcam_mini2_path, 2)
    context = Context()
    operation = OperationParams()

    if output.exists():
        output.unlink()

    clip = context.forge(output, inputs, operation)

    context.doit()

    assert clip.path.is_file()

    # read video and check
    video = RawVideo(clip.path)
    assert math.isclose(video.duration, clip.duration)


def test_concat_folder(dashcam_mini2_path: Path):
    """
    Concatenate all inputs from folder.
    """


def test_time_scale(dashcam_mini2_path: Path, output_dir: Path):
    """
    Rescale time.
    """

    output = output_dir / "clip.mp4"
    inputs = _get_inputs(dashcam_mini2_path, 1)
    context = Context()
    operation = OperationParams(
        duration_params=DurationParams(time_scale=5),
        audio=False,
    )

    if output.exists():
        output.unlink()

    clip = context.forge(output, inputs, operation)

    context.doit()

    assert clip.path.is_file()

    # read video and check
    video = RawVideo(clip.path)
    assert math.isclose(video.duration, clip.duration)


def test_time_scale_concat(dashcam_mini2_path: Path, output_dir: Path):
    """
    Rescale time and concatenate inputs.
    """


def test_res_scale(dashcam_mini2_path: Path, output_dir: Path):
    """
    Rescale resolution.
    """


def test_res_scale_concat(dashcam_mini2_path: Path, output_dir: Path):
    """
    Rescale resolution and concatenate inputs.
    """


def test_invalid(dashcam_mini2_path: Path):
    """
    Concatenate inputs, with one input being invalid.
    """


def _get_inputs(path: Path, count: int) -> list[RawVideo]:
    files = [
        "sample-1.mp4",
        "sample-2.mp4",
        "sample-3.mp4",
        "sample-invalid.mp4",
    ]
    return [
        RawVideo(path / file, profile=GarminDashcamMini2)
        for file in files[:count]
    ]
