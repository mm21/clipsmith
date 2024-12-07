from pathlib import Path

from clipsmith.clip import (
    Clip,
    DurationParams,
    OperationParams,
    ResolutionParams,
)
from clipsmith.context import Context
from clipsmith.profiles import GarminDashcamMini2
from clipsmith.video import RawVideo

from .conftest import DASHCAM_MINI2_FILENAMES, DASHCAM_MINI2_PATH, check_clip


def test_concat(context: Context, output_dir: Path):
    """
    Forge a new clip by concatenating inputs.
    """

    inputs = _get_inputs(2)

    clip = context.forge(output_dir / "clip.mp4", inputs)
    context.doit()

    check_clip(clip, sum(i.duration for i in inputs))


def test_concat_folder(
    context: Context, output_dir: Path, dashcam_mini2_path: Path
):
    """
    Concatenate all inputs from folder.
    """

    clip = context.forge(output_dir / "clip.mp4", dashcam_mini2_path)
    context.doit()

    check_clip(clip)


def test_time_scale(context: Context, output_dir: Path):
    """
    Rescale time based on scale factor.
    """

    inputs = _get_inputs(1)
    operation = OperationParams(
        duration_params=DurationParams(scale=5.0),
        audio=False,
    )

    clip = context.forge(output_dir / "clip.mp4", inputs, operation)
    context.doit()

    check_clip(clip, sum(i.duration for i in inputs) * 5)


def test_time_duration(context: Context, output_dir: Path):
    """
    Rescale time based on target duration.
    """

    inputs = _get_inputs(1)
    operation = OperationParams(
        duration_params=DurationParams(duration=5.0),
        audio=False,
    )

    clip = context.forge(output_dir / "clip.mp4", inputs, operation)
    context.doit()

    check_clip(clip, 5.0)


def test_res_scale(context: Context, output_dir: Path):
    """
    Rescale resolution.
    """

    input_video = _get_inputs(1)[0]

    def check(clip: Clip):
        assert input_video.resolution == (
            clip.resolution[0] * 2,
            clip.resolution[1] * 2,
        )
        check_clip(clip, input_video.duration)

    # scale factor
    operation = OperationParams(resolution_params=ResolutionParams(scale=0.5))

    # absolute resolution
    operation = OperationParams(
        resolution_params=ResolutionParams(resolution=(480, 270))
    )

    clip1 = context.forge(output_dir / "clip1.mp4", input_video, operation)
    clip2 = context.forge(output_dir / "clip2.mp4", input_video, operation)

    context.doit()

    check(clip1)
    check(clip2)


def test_reforge(context: Context, output_dir: Path):
    """
    Reforge a forged clip.
    """

    inputs = _get_inputs(2)

    # concatenate
    clip = context.forge(output_dir / "clip.mp4", inputs)

    # rescale
    clip2 = clip.reforge(
        output_dir / "clip2.mp4",
        OperationParams(duration_params=DurationParams(duration=5.0)),
    )

    context.doit()

    check_clip(clip, sum(i.duration for i in inputs))
    check_clip(clip2, 5.0)


def _get_inputs(count: int) -> list[RawVideo]:
    """
    Get the provided number of inputs as raw videos.
    """
    return [
        RawVideo(DASHCAM_MINI2_PATH / file, profile=GarminDashcamMini2)
        for file in DASHCAM_MINI2_FILENAMES[:count]
    ]
