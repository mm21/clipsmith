import shutil
import time
from pathlib import Path
from typing import Any

from pytest import raises

from clipsmith import (
    Clip,
    Context,
    DurationParams,
    OperationParams,
    RawVideo,
    ResolutionParams,
)
from clipsmith.clip.operation import BaseParams
from clipsmith.profiles import GarminDashcamMini2

from .conftest import DASHCAM_MINI2_FILENAMES, DASHCAM_MINI2_PATH, check_clip


def test_concat(context: Context, output_dir: Path):
    """
    Forge a new clip by concatenating inputs.
    """

    inputs = _get_inputs(2)

    clip = context.forge(output_dir / "clip.mp4", inputs)
    context.doit()

    check_clip(clip, sum(i.duration for i in inputs))

    # verify __repr__
    print(
        f"Checked clip: {clip}, datetime_start={clip.datetime_start}, datetime_end={clip.datetime_end}, datetime_range={clip.datetime_range}"
    )

    # verify creation of clip w/existing file
    context.forge(clip.path, inputs[0].path)


def test_concat_folder(
    context: Context, output_dir: Path, dashcam_mini2_path: Path, tmp_path: Path
):
    """
    Concatenate all inputs from folder.
    """

    # copy samples to temp path, with subfolder to test recursion
    samples_root = shutil.copytree(dashcam_mini2_path, tmp_path / "samples")
    shutil.copytree(dashcam_mini2_path, samples_root / "nested")

    clip = context.forge(output_dir / "clip.mp4", samples_root)
    context.doit()

    check_clip(clip)


def test_time_scale(context: Context, output_dir: Path):
    """
    Rescale time based on scale factor.
    """

    SCALE_FACTOR = 2.0

    inputs = _get_inputs(1)
    operation = OperationParams(
        duration_params=DurationParams(scale=SCALE_FACTOR),
        audio=False,
    )

    clip = context.forge(output_dir / "clip.mp4", inputs, operation)
    context.doit()

    check_clip(clip, sum(i.duration for i in inputs) * SCALE_FACTOR)


def test_time_duration(context: Context, output_dir: Path):
    """
    Rescale time based on target duration.
    """

    inputs = _get_inputs(1)
    operation = OperationParams(
        duration_params=DurationParams(target=5.0),
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

    SCALE_FACTOR = 2.0

    inputs = _get_inputs(3)
    dur_approx = sum(i.duration for i in inputs)

    operation1 = OperationParams(
        duration_params=DurationParams(
            trim_start=START,
            trim_end=END,
        )
    )
    dur1_approx = END - START

    operation2 = OperationParams(
        duration_params=DurationParams(
            trim_start=START,
        )
    )
    dur2_approx = dur_approx - START

    operation3 = OperationParams(
        duration_params=DurationParams(
            trim_end=END,
        )
    )
    dur3_approx = END

    operation4 = OperationParams(
        duration_params=DurationParams(
            target=SCALE_FACTOR,
            trim_start=START,
            trim_end=END,
        )
    )
    dur4_approx = (END - START) * SCALE_FACTOR

    operation5 = OperationParams(
        duration_params=DurationParams(
            scale=SCALE_FACTOR,
            trim_start=START,
        )
    )
    dur5_approx = (dur_approx - START) * SCALE_FACTOR

    operation6 = OperationParams(
        duration_params=DurationParams(
            scale=SCALE_FACTOR,
            trim_end=END,
        )
    )
    dur6_approx = END * SCALE_FACTOR

    clip1 = context.forge(output_dir / "clip1.mp4", inputs, operation1)
    clip2 = context.forge(output_dir / "clip2.mp4", inputs, operation2)
    clip3 = context.forge(output_dir / "clip3.mp4", inputs, operation3)
    clip4 = context.forge(output_dir / "clip4.mp4", inputs, operation4)
    clip5 = context.forge(output_dir / "clip5.mp4", inputs, operation5)
    clip6 = context.forge(output_dir / "clip6.mp4", inputs, operation6)

    context.doit()

    # trimming is not as precise
    rel_tol = 0.2

    check_clip(clip1, dur1_approx, rel_tol=rel_tol)
    check_clip(clip2, dur2_approx, rel_tol=rel_tol)
    check_clip(clip3, dur3_approx, rel_tol=rel_tol)
    check_clip(clip4, dur4_approx, rel_tol=rel_tol)
    check_clip(clip5, dur5_approx, rel_tol=rel_tol)
    check_clip(clip6, dur6_approx, rel_tol=rel_tol)


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
    operation1 = OperationParams(resolution_params=ResolutionParams(scale=0.5))

    # absolute resolution
    operation2 = OperationParams(
        resolution_params=ResolutionParams(target=(480, 270))
    )

    clip1 = context.forge(output_dir / "clip1.mp4", input_video, operation1)
    clip2 = context.forge(output_dir / "clip2.mp4", input_video, operation2)

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
        OperationParams(duration_params=DurationParams(target=5.0)),
    )

    context.doit()

    check_clip(clip, sum(i.duration for i in inputs))
    check_clip(clip2, 5.0)


def test_validate(context: Context, output_dir: Path):
    """
    Test validations.
    """

    invalid_params: list[tuple[BaseParams, dict[str, Any]]] = [
        (DurationParams, {"scale": 1.0, "target": 1.0}),
        (
            ResolutionParams,
            {"scale": 1.0, "target": (640, 480)},
        ),
    ]

    # invalid params
    for params in invalid_params:
        with raises(ValueError):
            params_cls, kwargs = params
            params_cls(**kwargs)

    clip = context.forge(output_dir / "EXPECTED-ERROR:", _get_inputs(1))

    # try to access duration when not set yet
    with raises(ValueError):
        clip.duration

    # invoke error when invoking doit task (invalid filename)
    with raises(ChildProcessError):
        context.doit()

    # try to lookup nonexistent command
    from clipsmith._ffmpeg import _get_command

    with raises(RuntimeError):
        _get_command(f"nonexistent-cmd-{time.time()}")


def _get_inputs(count: int) -> list[RawVideo]:
    """
    Get the provided number of inputs as raw videos.
    """
    return [
        RawVideo(DASHCAM_MINI2_PATH / file, profile=GarminDashcamMini2)
        for file in DASHCAM_MINI2_FILENAMES[:count]
    ]
