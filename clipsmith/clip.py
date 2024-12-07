from __future__ import annotations

import logging
import subprocess
import tempfile
from datetime import datetime as DateTime
from pathlib import Path
from typing import TYPE_CHECKING

from doit.task import Task
from pydantic import BaseModel, ConfigDict

from ._ffmpeg import FFMPEG_PATH
from .video import BaseVideo

if TYPE_CHECKING:
    from .context import Context


__all__ = [
    "OffsetParams",
    "DurationParams",
    "OperationParams",
    "Clip",
]


class BaseParams(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DurationParams(BaseParams):
    """
    Specifies duration of new clip, which may entail trimming and/or scaling.
    """

    duration: float | None = None
    """
    Rescale duration to given value, using effective duration if 
    input is trimmed.
    """

    scale: float | None = None
    """
    Rescale duration with given scale factor, using effective duration if 
    input is trimmed.
    """

    # TODO: handle datetime

    trim_start: float | DateTime | None = None
    """
    Start of output video relative to input, given as offset in seconds
    or absolute datetime.
    """

    trim_end: float | DateTime | None = None
    """
    End of output video relative to input, given as offset in seconds
    or absolute datetime.
    """


class ResolutionParams(BaseParams):
    resolution: tuple[int, int] | None = None
    """
    Rescale resolution to given value, using effective input resolution
    if input is trimmed.
    """

    scale: float | None = None
    """
    Rescale resolution with given scale factor.
    """

    trim: tuple[tuple[int, int], tuple[int, int]] | None = None
    """
    Area of input video to include in output, given as (upper left corner,
    lower right corner).
    """


class OperationParams(BaseParams):
    """
    Specifies operations to create new clip.
    """

    duration_params: DurationParams | None = None
    """
    Params to adjust duration by scaling and/or trimming.
    """

    resolution_params: ResolutionParams | None = None
    """
    Params to adjust resolution by scaling and/or trimming.
    """

    audio: bool = True
    """
    Whether to pass through audio.
    """

    @property
    def _has_resolution_scale(self) -> bool:
        """
        Whether this operation scales resolution.
        """
        if resolution_params := self.resolution_params:
            return bool(resolution_params.resolution or resolution_params.scale)
        return False

    def _get_resolution(self, first: BaseVideo) -> tuple[int, int]:
        """
        Get target resolution based on this operation, or the first video in the
        inputs otherwise.

        TODO: find max resolution from inputs instead of using first
        """
        if resolution_params := self.resolution_params:
            if resolution := resolution_params.resolution:
                pair = resolution
            if scale := resolution_params.scale:
                pair = (
                    scale
                    if isinstance(scale, tuple)
                    else (
                        first.resolution[0] * scale,
                        first.resolution[1] * scale,
                    )
                )
            return int(pair[0]), int(pair[1])
        else:
            return first.resolution

    def _get_time_scale(self, duration_orig: float) -> float | None:
        """
        Get target duration and time scale.
        """
        if duration_params := self.duration_params:
            if duration_params.scale:
                # given time scale
                return duration_params.scale
            elif duration_params.duration:
                # given duration
                return duration_params.duration / duration_orig
        return None


class Clip(BaseVideo):
    """
    Encapsulates a clip, which is defined by one of the following:

    - One or more existing video files
    - A video file to be created, derived from another `Clip` with specified
    operations
    """

    __context: Context
    """
    Context associated with clip.
    """

    __inputs: list[BaseVideo]
    """
    List of inputs.
    """

    __operation: OperationParams
    """
    Operation to create the video corresponding to this clip.
    """

    __task: Task
    """
    Doit task corresponding to operation.
    """

    def __init__(
        self,
        output: Path,
        inputs: list[BaseVideo],
        operation: OperationParams,
        context: Context,
    ):
        """
        Creates a clip associated with the given context.
        """
        assert len(inputs), f"No input videos passed"
        assert all(
            inputs[i].resolution == inputs[i - 1].resolution
            for i, _ in enumerate(inputs)
        ), f"Inconsistent input resolutions not currently supported: {inputs}"

        resolution = operation._get_resolution(inputs[0])

        super().__init__(
            output,
            resolution=resolution,
            datetime_start=inputs[0].datetime_start,
        )

        # get duration from file if it exists
        if self.path.exists():
            self._extract_duration()

        self.__context = context
        self.__inputs = inputs
        self.__operation = operation
        self.__task = self.__prepare_task(inputs)

    @property
    def __out_path(self) -> str:
        """
        Get absolute path to output file.
        """
        return str(self.path.resolve())

    def reforge(self, output: Path, operation: OperationParams) -> Clip:
        """
        Creates a new clip from this one using the indicated operations.
        """
        return self.__context.forge(output, self, operation)

    def _get_task(self) -> Task:
        """
        Get the doit task previously created.
        """
        return self.__task

    def __prepare_task(
        self,
        inputs: list[BaseVideo],
    ) -> Task:
        """
        Prepare doit task for creation of this clip from its inputs.
        """

        def action():
            args = self.__get_args()

            logging.debug(f"Invoking ffmpeg: {' '.join(args)}")
            subprocess.check_call(args)

            # get duration from newly written file
            assert self.path.exists()
            self._extract_duration()

        return Task(
            str(self.path),
            [action],
            file_dep=[str(i.path) for i in inputs],
            targets=[self.__out_path],
        )

    def __get_args(self) -> list[str]:
        """
        Get ffmpeg args.

        TODO: handle offset from video start, if given
        - subtract offset from duration
        - add offset to datetime_start
        - use -t arg to trim time
        """

        # get time scale, if any
        time_scale = self.__operation._get_time_scale(
            sum(i.duration for i in self.__inputs)
        )

        # get resolution scale, if any
        has_res_scale = self.__operation._has_resolution_scale

        # get full path to all inputs
        input_paths = [i.path.resolve() for i in self.__inputs]

        if len(input_paths) == 1:
            # single input, use -i arg
            input_args = ["-i", str(input_paths[0])]
        else:
            # multiple inputs, use temp file containing list of files

            temp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            )
            temp.writelines([f"file '{str(file)}'\n" for file in input_paths])
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
        if time_scale or has_res_scale:
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
            if has_res_scale
            else []
        )

        # audio
        # TODO: properly handle audio scaling if time scaling enabled
        audio_args = [] if self.__operation.audio else ["-an"]

        return (
            [FFMPEG_PATH, "-loglevel", "error"]
            + input_args
            + codec_args
            + filter_args
            + time_args
            + res_args
            + audio_args
            + [self.__out_path]
        )
