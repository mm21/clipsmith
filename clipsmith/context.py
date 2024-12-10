"""
Encapsulates a set of clips, along with task management functionality to
create them.
"""

from pathlib import Path
from typing import Iterable

from doit.cmd_base import Command, TaskLoader2
from doit.doit_cmd import DoitMain
from doit.task import Task

from .clip import Clip, OperationParams
from .video import BaseVideo, RawVideo, RawVideoCache


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
        output: Path,
        inputs: Path | BaseVideo | Iterable[Path | BaseVideo],
        operation: OperationParams | None = None,
    ) -> Clip:
        """
        Creates a new clip from the given input(s) using the given operations.

        Adds a `doit` task to the associated context; user can then perform
        processing by invoking `Context.doit`.

        If any folder is passed as input, it is recursively traversed
        depth-first to form a list of input videos.

        :param output: Path to output file
        :param inputs: Path to one or more inputs, which may be a video or folder of videos
        :param operation: Parameters to apply to input
        """

        def process_input(path: Path) -> list[BaseVideo]:
            if path.is_file():
                return [RawVideo(path)]
            else:
                videos: list[BaseVideo] = []

                # add videos from this folder
                cache = RawVideoCache(path)
                videos += cache.valid_videos

                # add videos from subfolders
                folders = [
                    p
                    for p in path.iterdir()
                    if p.is_dir() and not p.name.startswith(".")
                ]
                for folder in sorted(folders, key=lambda f: f.name):
                    videos += process_input(folder)

                return videos

        inputs_ = inputs if isinstance(inputs, Iterable) else [inputs]
        input_videos: list[BaseVideo] = []

        for i in inputs_:
            if isinstance(i, BaseVideo):
                input_videos.append(i)
            else:
                assert isinstance(i, Path)
                assert i.exists()
                input_videos += process_input(i)

        clip = Clip(output, input_videos, operation or OperationParams(), self)
        self.__tasks.append(clip._get_task())

        return clip

    def doit(self):
        """
        Invoke tasks to build all clips.

        :raises ChildProcessError: If any ffmpeg invocations failed
        """

        tasks = self.__tasks

        class Loader(TaskLoader2):
            def load_tasks(self, cmd: Command, pos_args: list[str]):
                return tasks

            def load_doit_config(self):
                return {}

        doit_main = DoitMain(task_loader=Loader(), config_filenames=())
        cmd = ["run"] + [task.name for task in tasks]

        ret = doit_main.run(cmd)
        if ret != 0:
            raise ChildProcessError("Failed to run doit tasks")
