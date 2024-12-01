"""
Encapsulates a set of clips, along with task management functionality to
create them.
"""

from pathlib import Path

from doit.cmd_base import Command, TaskLoader2
from doit.doit_cmd import DoitMain
from doit.task import Task

from .clip import Clip, OperationParams
from .video import BaseVideo


class Context:
    """
    Container in which to store pending tasks to create targets associated
    with `Clip`s. Perform the clip processing by invoking `Context.doit()`.
    """

    __tasks: list[Task]

    def __init__(self):
        self.__tasks = []

    def forge(
        self,
        path: Path,
        inputs: BaseVideo | list[BaseVideo],
        operation: OperationParams,
    ) -> Clip:
        """
        Creates a new clip from the given input(s) using the given operations.

        Adds a `doit` task to the associated context; user can then perform
        processing by invoking `Context.doit`.

        :param path: Path to output file
        :param inputs: One or more input videos, which may be a `RawVideo` or another `Clip`
        :param operation: Parameters to apply to input
        """
        clip = Clip(path, inputs, operation, self)
        self.__tasks.append(clip._get_task())

        return clip

    def doit(self):
        """
        Invoke tasks to build all clips.
        """

        tasks = self.__tasks

        class Loader(TaskLoader2):
            def load_tasks(self, cmd: Command, args: list[str]):
                return tasks

        doit_main = DoitMain(task_loader=Loader())
        cmd = ["run"] + [task.name for task in tasks]

        doit_main.run(cmd)
