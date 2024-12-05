from pathlib import Path

from clipsmith.clip import DurationParams, OperationParams
from clipsmith.context import Context
from clipsmith.profiles import GarminDashcamMini2
from clipsmith.video import RawVideo, RawVideoCache

from .conftest import DASHCAM_MINI2_PATH, check_clip


def test_concat(context: Context, output_dir: Path):
    """
    Forge a new clip by concatenating inputs.
    """

    output = output_dir / "clip.mp4"
    inputs = _get_inputs(2)
    operation = OperationParams()

    clip = context.forge(output, inputs, operation)

    context.doit()

    check_clip(clip, sum(i.duration for i in inputs))


def test_concat_folder(
    context: Context, output_dir: Path, dashcam_mini2_path: Path
):
    """
    Concatenate all inputs from folder.
    """

    cache = RawVideoCache(dashcam_mini2_path)

    # create clip from list of valid videos
    cache.valid_videos


def test_time_scale(context: Context, output_dir: Path):
    """
    Rescale time based on scale factor.
    """

    output = output_dir / "clip.mp4"
    inputs = _get_inputs(1)
    operation = OperationParams(
        duration_params=DurationParams(time_scale=5.0),
        audio=False,
    )

    clip = context.forge(output, inputs, operation)

    context.doit()

    check_clip(clip, sum(i.duration for i in inputs) * 5)


def test_time_duration(context: Context, output_dir: Path):
    """
    Rescale time based on target duration.
    """

    output = output_dir / "clip.mp4"
    inputs = _get_inputs(1)
    operation = OperationParams(
        duration_params=DurationParams(duration=5.0),
        audio=False,
    )

    clip = context.forge(output, inputs, operation)

    context.doit()

    check_clip(clip, 5.0)


def test_res_scale(context: Context, output_dir: Path):
    """
    Rescale resolution.
    """


def _get_inputs(count: int) -> list[RawVideo]:
    """
    Get the provided number of inputs as raw videos.
    """
    files = [
        "sample-1.mp4",
        "sample-2.mp4",
        "sample-3.mp4",
        "sample-invalid.mp4",
    ]
    return [
        RawVideo(DASHCAM_MINI2_PATH / file, profile=GarminDashcamMini2)
        for file in files[:count]
    ]
