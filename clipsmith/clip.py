from __future__ import annotations

from datetime import datetime as DateTime
from pathlib import Path
from typing import TYPE_CHECKING

from doit.task import Task
from pydantic import BaseModel

from .profile import BaseProfile
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

    duration_params: DurationParams

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

    __context: Context
    __inputs: list[BaseVideo]

    __operation: OperationParams
    """
    Operation to create the video corresponding to this clip.
    """

    __profile: BaseProfile

    __task: Task
    """
    Task corresponding to operation.
    """

    def __init__(
        self,
        context: Context,
        path: Path,
        inputs: list[BaseVideo],
        operation: OperationParams,
    ):
        """
        Creates a clip associated with the given context.
        """

        # TODO: derive from operation params
        metadata = VideoMetadata()

        super().__init__(path, metadata)

        self.__context = context
        self.__inputs = inputs
        self.__operation = operation

        self.__prepare_task()

    def reforge(self, path: Path, operation: OperationParams) -> Clip:
        """
        Creates a new clip from this one using the indicated operations.
        """
        return self.__context.forge(path, [self], operation)

    def __prepare_task(self, operation: OperationParams):
        """
        Prepares for creation of this clip using the given operation,
        creating a corresponding doit task and associating it with the
        context.
        """
        self.__operation = operation
