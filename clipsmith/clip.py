from __future__ import annotations

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

    duration: float | int | None = None
    """
    Explicitly provided duration.
    """

    time_scale: float | int | None = None
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

        duration = sum(i.duration for i in valid_inputs)
        time_scale = _get_time_scale(operation, duration)
        resolution = _get_resolution(operation, valid_inputs[0])

        # TODO: handle offset from video start, if given
        # - subtract offset from duration
        # - add offset to valid_inputs[0].datetime

        if time_scale:
            duration *= time_scale

        metadata = VideoMetadata(
            valid=True,
            duration=duration,
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
        time_scale: float | int | None,
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
            input_args = [
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                _create_file_list(input_paths),
            ]

        codec_args = ["-c", "copy"]

        # enable video filters (scaling, cropping, etc) if needed
        filter_args = ["-filter:v"] if time_scale or res_scale else []

        # time scaling
        time_args = [f"setpts={time_scale}*PTS"] if time_scale else []

        # resolution scaling
        if res_scale:
            res_args = [f"scale={self.resolution[0]}:{self.resolution[1]}"]
        else:
            res_args = []

        # audio
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
            subprocess.check_call(args)

        return Task(
            str(self.path),
            [action],
            file_dep=[str(i) for i in inputs],
            targets=[out_path],
        )


def _get_time_scale(
    operation: OperationParams, duration: float
) -> float | int | None:
    """
    Get target time scale based on operation and duration.
    """
    if duration_params := operation.duration_params:
        if duration_params.time_scale:
            # explicitly given time scale
            return duration_params.time_scale
        elif duration_params.duration:
            # derive from duration
            return duration_params.duration / duration

    return None


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


def _create_file_list(inputs: list[Path]) -> str:
    """
    Create a list of files in a temp folder.
    """

    temp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt")

    for file in inputs:
        temp.write(f"file '{str(file)}'\n")

    temp.flush()
    return str(temp)
