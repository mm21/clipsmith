from __future__ import annotations

import logging
import subprocess
import tempfile
from datetime import datetime as DateTime
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from doit.task import Task
from pydantic import BaseModel

from ._ffmpeg import FFMPEG_PATH
from .video import BaseVideo, VideoMetadata

if TYPE_CHECKING:
    from .context import Context


class EndpointParams(BaseModel):
    offset: float | None = None
    """
    Offset in seconds.
    """

    datetime: DateTime | None = None
    """
    Datetime.
    """


class DurationParams(BaseModel):
    """
    Specifies duration of new clip.
    """

    duration: float | None = None
    """
    Explicitly provided duration.
    """

    time_scale: float | None = None
    """
    Derive duration from source with provided scale factor.
    """

    start: EndpointParams | None = None
    """
    Start of output video relative to input.
    """

    end: EndpointParams | None = None
    """
    End of output video relative to input.
    """


class OperationParams(BaseModel):
    """
    Specifies operations to create new clip.
    """

    duration_params: DurationParams | None = None

    res_scale: float | int | str | None = None
    """
    Resolution scale factor or absolute resolution as `x:y`.
    """

    audio: bool = True
    """
    Whether to pass through audio.
    """


class Clip(BaseVideo):
    """
    Encapsulates a clip, which is defined by one of the following:

    - One or more existing video files
    - A video file to be created, derived from another `Clip` with specified
    operations
    """

    _inputs: list[BaseVideo]
    """
    Normalized list of valid inputs, for debugging only.
    """

    _operation: OperationParams
    """
    Operation to create the video corresponding to this clip, 
    for debugging only.
    """

    __context: Context
    """
    Context associated with clip.
    """

    __task: Task
    """
    Doit task corresponding to operation.
    """

    def __init__(
        self,
        path: Path,
        inputs: BaseVideo | list[BaseVideo],
        operation: OperationParams,
        context: Context,
    ):
        """
        Creates a clip associated with the given context.
        """

        inputs_ = inputs if isinstance(inputs, Iterable) else [inputs]
        valid_inputs = [v for v in inputs_ if v.valid]
        assert len(valid_inputs), f"No valid inputs from {inputs}"

        duration_orig = sum(i.duration for i in valid_inputs)
        duration_scaled, time_scale = _get_time_params(operation, duration_orig)
        resolution = _get_resolution(operation, valid_inputs[0])

        # TODO: handle offset from video start, if given
        # - subtract offset from duration
        # - add offset to valid_inputs[0].datetime
        # - use -t arg to trim time

        metadata = VideoMetadata(
            valid=True,
            duration=duration_scaled or duration_orig,
            resolution=resolution,
            datetime=valid_inputs[0].datetime,
        )

        super().__init__(path, metadata)

        self.__context = context
        self.__task = self.__prepare_task(operation, valid_inputs, time_scale)

        self._inputs = valid_inputs
        self._operation = operation

    def reforge(self, path: Path, operation: OperationParams) -> Clip:
        """
        Creates a new clip from this one using the indicated operations.
        """
        return self.__context.forge(path, [self], operation)

    def _get_task(self) -> Task:
        """
        Get the doit task previously created.
        """
        return self.__task

    def __prepare_task(
        self,
        operation: OperationParams,
        inputs: list[BaseVideo],
        time_scale: float | None,
    ) -> Task:
        """
        Prepare for creation of this clip using the given operation,
        creating a corresponding doit task.
        """

        input_paths = [i.path.resolve() for i in inputs]
        res_scale = operation.res_scale
        out_path = str(self.path.resolve())

        if len(input_paths) == 1:
            # single input, use -i arg
            input_args = ["-i", str(input_paths[0])]
        else:
            # multiple inputs, use temp file containing list of files

            temp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            )
            temp.writelines([f"file '{str(file)}'\n" for file in input_paths])

            temp.flush()
            temp.close()

            input_args = [
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                temp.name,
            ]

        # these ffmpeg params are mutually exclusive
        if time_scale or res_scale:
            # enable video filters (scaling, cropping, etc)
            codec_args = []
            filter_args = ["-filter:v"]
        else:
            # use copy codec
            codec_args = ["-c", "copy"]
            filter_args = []

        # time scaling
        time_args = [f"setpts={time_scale}*PTS"] if time_scale else []

        # resolution scaling
        res_args = (
            [f"scale={self.resolution[0]}:{self.resolution[1]}"]
            if res_scale
            else []
        )

        # audio
        # TODO: properly handle audio scaling if time scaling enabled
        audio_args = [] if operation.audio else ["-an"]

        args = (
            [FFMPEG_PATH]
            + input_args
            + codec_args
            + filter_args
            + time_args
            + res_args
            + audio_args
            + [out_path]
        )

        def action():
            # TODO: get args on the fly since actual durations might
            # not be as expected (due to time scaling)
            # - use self.__inputs, self.__operation
            logging.debug(f"Invoking ffmpeg: {' '.join(args)}")
            subprocess.check_call(args)

            # TODO: read newly created file and update duration

        return Task(
            str(self.path),
            [action],
            file_dep=[str(i.path) for i in inputs],
            targets=[out_path],
        )


def _get_time_params(
    operation: OperationParams, duration_orig: float
) -> tuple[float | None, float | None]:
    """
    Get target duration and time scale based on operation.
    """
    if duration_params := operation.duration_params:
        if duration_params.time_scale:
            # given time scale
            return (
                duration_params.time_scale * duration_orig,
                duration_params.time_scale,
            )
        elif duration_params.duration:
            # given duration
            return (
                duration_params.duration,
                duration_orig / duration_params.duration,
            )

    return None, None


def _get_resolution(
    operation: OperationParams, first: BaseVideo
) -> tuple[int, int]:
    """
    Get target resolution based on the operation, or the first video in the
    inputs otherwise.

    TODO: find max resolution from inputs
    """
    if res_scale := operation.res_scale:
        if isinstance(res_scale, str):
            split = res_scale.split(":")
            assert len(split) == 2, f"Invalid resolution: {res_scale}"

            x, y = map(int, split)
        else:
            x, y = int(first.resolution[0] / res_scale), int(
                first.resolution[1] / res_scale
            )

        return (x, y)
    else:
        return first.resolution
