from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from doit.task import Task

from .._ffmpeg import get_ffmpeg
from ..video.base import BaseVideo
from .operation import OperationParams

if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "Clip",
]


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
        Creates a clip associated with the given context. Assumes all inputs
        are valid, if applicable.
        """
        assert len(inputs), f"No input videos passed"
        assert all(
            inputs[i].resolution == inputs[i - 1].resolution
            for i, _ in enumerate(inputs)
        ), f"Inconsistent input resolutions not currently supported: {inputs}"
        assert (
            output.parent.is_dir()
        ), f"Output parent folder does not exist: {output}"

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
    def inputs(self) -> list[BaseVideo]:
        """
        Get input videos.
        """
        return self.__inputs

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

    @property
    def __out_path(self) -> str:
        """
        Get absolute path to output file.
        """
        return str(self.path.resolve())

    def __prepare_task(
        self,
        inputs: list[BaseVideo],
    ) -> Task:
        """
        Prepare doit task for creation of this clip from its inputs.
        """

        def action():
            args = self.__get_args()

            logging.info(f"Invoking ffmpeg: '{' '.join(args)}'")

            try:
                subprocess.check_call(args)
            except subprocess.CalledProcessError:
                # doit will catch any exceptions and print them, so gracefully
                # fail the task
                return False

            # get duration from newly written file
            assert self.path.exists()
            self._extract_duration()

            logging.info(f"Forged clip: '{self.__out_path}'")

        return Task(
            str(self.path),
            [action],
            file_dep=[str(i.path) for i in inputs],
            targets=[self.__out_path],
            verbosity=2,
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
            [get_ffmpeg(), "-loglevel", self.__operation.log_level]
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
