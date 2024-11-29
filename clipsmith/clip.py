from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from doit.task import Task
from pydantic import BaseModel

from .profile import BaseProfile, DefaultProfile
from .video import BaseVideo

if TYPE_CHECKING:
    from .context import Context


class Operation(BaseModel):
    input_path: Path
    output_path: Path
    time_scale: float | int | None = None
    res_scale: float | int | None = None


class Clip(BaseVideo):
    """
    Encapsulates a clip, which is defined by one of the following:

    - One or more existing video files
    - A video file to be created, derived from another `Clip` with specified
    operations
    """

    __path: Path
    __context: Context
    __profile: BaseProfile

    __operation: Operation | None = None
    """
    Operation to create the video(s) corresponding to this clip.
    """

    __task: Task | None = None
    """
    Task corresponding to operation.
    """

    def __init__(
        self,
        path: Path,
        context: Context | None = None,
        profile: BaseProfile | None = None,
    ):
        """
        Creates a clip associated with the given context and profile.
        """
        self.__path = path
        self.__context = context or Context()
        self.__profile = profile or DefaultProfile()

    def reforge(
        self,
        path: Path,
        time_scale: float | int | None = None,
        res_scale: float | int | None = None,
    ) -> Clip:
        """
        Creates a new clip from this one with the indicated processing.

        Adds a doit task to the associated context; user can then perform
        processing by invoking `Context.doit`.
        """
        operation = Operation(
            input_path=self.__path,
            output_path=path,
            time_scale=time_scale,
            res_scale=res_scale,
        )

        new_clip = Clip(path, context=self.__context)
        new_clip._prepare_operation(operation)

        return new_clip

    def _prepare_operation(self, operation: Operation):
        """
        Prepares for creation of this clip using the given operation,
        creating a corresponding doit task.
        """
        self.__operation = operation
