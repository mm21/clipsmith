from __future__ import annotations

from datetime import datetime as DateTime
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from doit.task import Task
from pydantic import BaseModel

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

    res_scale: float | int | None = None
    """
    Resolution scale factor.
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

        # TODO: derive from other operation params (explicit duration, etc)
        time_scale = (
            (operation.duration_params.time_scale or 1)
            if operation.duration_params
            else 1
        )
        duration = sum(i.duration for i in inputs_) * time_scale

        metadata = VideoMetadata(valid=True, duration=duration)

        super().__init__(path, metadata)

        self.__inputs = inputs_
        self.__operation = operation
        self.__context = context
        self.__task = self.__prepare_task()

    def reforge(self, path: Path, operation: OperationParams) -> Clip:
        """
        Creates a new clip from this one using the indicated operations.
        """
        return self.__context.forge(path, [self], operation)

    def _get_task(self) -> Task:
        return self.__task

    def __prepare_task(self) -> Task:
        """
        Prepares for creation of this clip using the given operation,
        creating a corresponding doit task.
        """

        # TODO: prepare doit task w/ffmpeg command
        # - get ffmpeg params from inputs, operation, metadata
        # - inputs: normalize to list of valid files, create temp .txt
        # and pass to ffmpeg
