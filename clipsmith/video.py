from abc import ABC, abstractmethod
from datetime import datetime as DateTime
from pathlib import Path


class BaseVideo(ABC):
    @property
    @abstractmethod
    def duration(self) -> float:
        """
        Getter for duration in seconds.
        """

    @property
    @abstractmethod
    def start_datetime(self) -> DateTime | None:
        """
        Getter for timezone-unaware start datetime, if applicable.
        """

    @property
    @abstractmethod
    def end_datetime(self) -> DateTime | None:
        """
        Getter for timezone-unaware end datetime, if applicable.
        """


class RawVideo(BaseVideo):
    """
    Encapsulates a single video file.
    """

    _path: Path

    def __init__(self, path: Path):
        self._path = path
