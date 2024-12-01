"""
Encapsulates a set of clips, along with task management functionality to
create them.
"""

from pathlib import Path

from doit.cmd_base import Command, TaskLoader2
from doit.doit_cmd import DoitMain
from doit.task import Task

from .clip import Clip, OperationParams
from .profile import BaseProfile
from .video import BaseVideo


class Context:
    __profile: BaseProfile | None
    """
    Optional global profile to associate with each clip.
    """
    __tasks: list[Task]

    def __init__(self, profile: BaseProfile | None = None):
        self.__profile = profile

    def forge(
        self, path: Path, inputs: list[BaseVideo], operation: OperationParams
    ) -> Clip:
        """
        Creates a new clip from the given inputs using the given operations.

        Adds a doit task to the associated context; user can then perform
        processing by invoking `Context.doit`.
        """
        return Clip(path, inputs, self, operation, self.__profile)

    def doit(self):
        """
        Invoke tasks to build all clips.
        """

        tasks = self.__tasks

        class Loader(TaskLoader2):
            def load_tasks(self, _: Command, args: list[str]):
                return tasks

        doit_main = DoitMain(task_loader=Loader())
        cmd = ["run"] + [task.name for task in tasks]

        doit_main.run(cmd)

    def _add_task(self, task: Task):
        pass
