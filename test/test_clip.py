from pathlib import Path
from typing import Any

from pytest import raises

from clipsmith.clip import (
    BaseParams,
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
        duration_params=DurationParams(scale_factor=5.0),
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
        duration_params=DurationParams(scale_duration=5.0),
        audio=False,
    )

    clip = context.forge(output_dir / "clip.mp4", inputs, operation)
    context.doit()

    check_clip(clip, 5.0)


def test_time_offsets(context: Context, output_dir: Path):
    """
    Trim input using start/time offsets along with scale factors.
    """

    START = 1.0
    END = 2.0

    inputs = _get_inputs(3)

    operation1 = OperationParams(
        duration_params=DurationParams(
            trim_start=START,
            trim_end=END,
        )
    )
    operation2 = OperationParams(
        duration_params=DurationParams(
            trim_start=START,
        )
    )
    operation3 = OperationParams(
        duration_params=DurationParams(
            trim_end=END,
        )
    )
    operation4 = OperationParams(
        duration_params=DurationParams(
            scale_duration=5.0,
            trim_start=START,
            trim_end=END,
        )
    )
    operation5 = OperationParams(
        duration_params=DurationParams(
            scale_factor=5.0,
            trim_start=START,
        )
    )
    operation6 = OperationParams(
        duration_params=DurationParams(
            scale_duration=5.0,
            trim_end=END,
        )
    )

    clip1 = context.forge(output_dir / "clip1.mp4", inputs, operation1)
    clip2 = context.forge(output_dir / "clip2.mp4", inputs, operation2)
    clip3 = context.forge(output_dir / "clip3.mp4", inputs, operation3)
    clip4 = context.forge(output_dir / "clip4.mp4", inputs, operation4)
    clip5 = context.forge(output_dir / "clip5.mp4", inputs, operation5)
    clip6 = context.forge(output_dir / "clip6.mp4", inputs, operation6)

    context.doit()

    # trimming is not as precise
    check_clip(clip1, 1.0, rel_tol=0.2)
    check_clip(clip2, 2.0, rel_tol=0.2)
    check_clip(clip3, 2.0, rel_tol=0.2)
    check_clip(clip4, 5.0, rel_tol=0.2)
    check_clip(clip5, 10.0, rel_tol=0.2)
    check_clip(clip6, 5.0, rel_tol=0.2)


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
    operation = OperationParams(
        resolution_params=ResolutionParams(scale_factor=0.5)
    )

    # absolute resolution
    operation = OperationParams(
        resolution_params=ResolutionParams(scale_resolution=(480, 270))
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
        OperationParams(duration_params=DurationParams(scale_duration=5.0)),
    )

    context.doit()

    check_clip(clip, sum(i.duration for i in inputs))
    check_clip(clip2, 5.0)


def test_params():
    """
    Test params validation.
    """

    invalid_params: list[tuple[BaseParams, dict[str, Any]]] = [
        (DurationParams, {"scale_factor": 1.0, "scale_duration": 1.0}),
        (
            ResolutionParams,
            {"scale_factor": 1.0, "scale_resolution": (640, 480)},
        ),
    ]

    for params in invalid_params:
        with raises(ValueError):
            params_cls, kwargs = params
            params_cls(**kwargs)


def _get_inputs(count: int) -> list[RawVideo]:
    """
    Get the provided number of inputs as raw videos.
    """
    return [
        RawVideo(DASHCAM_MINI2_PATH / file, profile=GarminDashcamMini2)
        for file in DASHCAM_MINI2_FILENAMES[:count]
    ]
