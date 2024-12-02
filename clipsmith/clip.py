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

    __inputs: list[BaseVideo]
    """
    Normalized list of inputs.
    """

    __operation: OperationParams
    """
    Operation to create the video corresponding to this clip.
    """

    __context: Context
    """
    Context associated with clip.
    """

    __time_scale: float | int | None
    """
    Time scale, if any.
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
        time_scale = self.__get_time_scale(duration)
        resolution = self.__get_resolution(operation, valid_inputs[0])

        if time_scale:
            duration *= time_scale

        metadata = VideoMetadata(
            valid=True, duration=duration, resolution=resolution
        )

        super().__init__(path, metadata)

        self.__inputs = valid_inputs
        self.__operation = operation
        self.__context = context
        self.__time_scale = time_scale
        self.__task = self.__prepare_task()

    def reforge(self, path: Path, operation: OperationParams) -> Clip:
        """
        Creates a new clip from this one using the indicated operations.
        """
        return self.__context.forge(path, [self], operation)

    def _get_task(self) -> Task:
        return self.__task

    def __get_time_scale(self, duration: float) -> float | int | None:
        if duration_params := self.__operation.duration_params:
            if duration_params.duration:
                return duration_params.duration / duration
            elif duration_params.time_scale:
                return duration_params.time_scale

        return None

    def __get_resolution(
        self, operation: OperationParams, first: BaseVideo
    ) -> tuple[int, int]:
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

    def __prepare_task(self) -> Task:
        """
        Prepare for creation of this clip using the given operation,
        creating a corresponding doit task.
        """

        inputs = [i.path.resolve() for i in self.__inputs]

        # collect needed info
        time_scale = self.__time_scale
        res_scale = self.__operation.res_scale
        out_path = str(self.path.resolve())

        if len(inputs) == 1:
            # single input, use -i arg
            input_args = ["-i", inputs[0]]
        else:
            # multiple inputs, use temp file containing list of files
            input_args = [
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                self.__create_file_list(inputs),
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
        audio_args = [] if self.__operation.audio else ["-an"]

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
            str(self.__path),
            [action],
            file_dep=[str(i) for i in inputs],
            targets=[out_path],
        )

    def __create_file_list(self, inputs: list[Path]) -> str:
        """
        Create a list of files in a temp folder.
        """

        temp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt")

        for file in inputs:
            temp.write(f"file '{str(file)}'\n")

        temp.flush()
        return str(temp)
