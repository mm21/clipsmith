from __future__ import annotations

import logging
import subprocess
import tempfile
from datetime import datetime as DateTime
from pathlib import Path
from typing import TYPE_CHECKING

from doit.task import Task
from pydantic import BaseModel, ConfigDict, Field

from ._ffmpeg import get_ffmpeg
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

    scale_factor: float | None = None
    """
    Rescale duration with given scale factor.
    """

    scale_duration: float | None = None
    """
    Rescale duration to given value.
    """

    trim_start: float | DateTime | None = None
    """
    Start offset in input file(s), specified as:
    - Number of seconds from the beginning
    - Absolute datetime (for datetime-aware inputs)
    """

    trim_end: float | DateTime | None = None
    """
    End offset in input file(s), specified as:
    - Number of seconds from the beginning
    - Absolute datetime (for datetime-aware inputs)
    """

    def model_post_init(self, __context):
        if self.scale_factor and self.scale_duration:
            raise ValueError(
                f"Cannot provide both scale factor and duration: scale_factor={self.scale_factor}, scale_duration={self.scale_duration}"
            )

        return super().model_post_init(__context)


class ResolutionParams(BaseParams):
    """
    Specifies resolution of new clip.
    """

    scale_factor: float | None = None
    """
    Rescale resolution with given scale factor.
    """

    scale_resolution: tuple[int, int] | None = None
    """
    Rescale resolution to given value.
    """

    def model_post_init(self, __context):
        if self.scale_factor and self.scale_resolution:
            raise ValueError(
                f"Cannot provide both scale factor and resolution: scale_factor={self.scale_factor}, scale_resolution={self.scale_resolution}"
            )

        return super().model_post_init(__context)


class OperationParams(BaseParams):
    """
    Specifies operations to create new clip.
    """

    duration_params: DurationParams = Field(default_factory=DurationParams)
    """
    Params to adjust duration by scaling and/or trimming.
    """

    resolution_params: ResolutionParams = Field(
        default_factory=ResolutionParams
    )
    """
    Params to adjust resolution by scaling and/or trimming.
    """

    audio: bool = True
    """
    Whether to pass through audio.
    """

    def _get_effective_duration(self, duration_orig: float) -> float:
        """
        Get duration accounting for any trimming.
        """
        if self.duration_params.trim_start or self.duration_params.trim_end:
            start = self._trim_start or 0.0
            end = self._trim_end or duration_orig
            assert isinstance(start, float) and isinstance(end, float)
            return end - start
        return duration_orig

    def _get_resolution(self, first: BaseVideo) -> tuple[int, int]:
        """
        Get target resolution based on this operation, or the first video in the
        inputs otherwise.

        TODO: find max resolution from inputs instead of using first
        """
        if scale_factor := self.resolution_params.scale_factor:
            pair = (
                first.resolution[0] * scale_factor,
                first.resolution[1] * scale_factor,
            )
        elif resolution := self.resolution_params.scale_resolution:
            pair = resolution
        else:
            pair = first.resolution
        return int(pair[0]), int(pair[1])

    def _get_time_scale(self, duration_orig: float) -> float | None:
        """
        Get time scale (if any) based on target duration and original duration.
        """
        if scale_factor := self.duration_params.scale_factor:
            # given time scale
            return scale_factor
        elif duration := self.duration_params.scale_duration:
            # given duration
            return duration / self._get_effective_duration(duration_orig)
        return None

    def _get_res_scale(
        self, clip_res: tuple[int, int]
    ) -> tuple[int, int] | None:
        """
        Get target resolution (if any).
        """
        if (
            self.resolution_params.scale_resolution
            or self.resolution_params.scale_factor
        ):
            return clip_res
        return None

    def _get_duration_arg(self, duration_orig: float) -> float | None:
        """
        Get -t arg, if any. Only needed if there is an end offset.
        """
        if self._trim_end:
            if scale_factor := self.duration_params.scale_factor:
                return scale_factor * self._get_effective_duration(
                    duration_orig
                )
            elif scale_duration := self.duration_params.scale_duration:
                return scale_duration
            else:
                return self._get_effective_duration(duration_orig)
        return None

    @property
    def _trim_start(self) -> float | None:
        """
        Get start offset.
        """
        # TODO: convert datetime to offset
        if start := self.duration_params.trim_start:
            assert isinstance(start, float)
            return start
        return None

    @property
    def _trim_end(self) -> float | None:
        """
        Get end offset.
        """
        # TODO: convert datetime to offset
        if end := self.duration_params.trim_end:
            assert isinstance(end, float)
            return end
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

            try:
                subprocess.check_call(args)
            except subprocess.CalledProcessError:
                # doit will catch any exceptions and print them, so gracefully
                # fail the task
                return False

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
        """

        # get original duration based on inputs
        duration_orig = sum(i.duration for i in self.__inputs)

        # get time scale, if any
        time_scale = self.__operation._get_time_scale(duration_orig)

        # get resolution scale, if any
        res_scale = self.__operation._get_res_scale(self.resolution)

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

        # start offset
        trim_start = self.__operation._trim_start
        start_args = ["-ss", str(trim_start)] if trim_start else []

        # duration
        dur_arg = self.__operation._get_duration_arg(duration_orig)
        dur_args = ["-t", str(dur_arg)] if dur_arg else []

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
        res_args = [f"scale={res_scale[0]}:{res_scale[1]}"] if res_scale else []

        # audio
        # TODO: properly handle audio scaling if time scaling enabled
        audio_args = [] if self.__operation.audio else ["-an"]

        # notes:
        # - with start offset, the output can be longer since ffmpeg
        #   cuts at the keyframe before the offset
        # - similarly, with end offset the output can be longer since ffmpeg
        #   cuts at the keyframe after the offset
        # - need start_args to come before input_args to avoid frozen frames
        #   at beginning of output

        return (
            [get_ffmpeg(), "-loglevel", "fatal"]
            + start_args
            + input_args
            + dur_args
            + codec_args
            + filter_args
            + time_args
            + res_args
            + audio_args
            + [self.__out_path]
        )
