from __future__ import annotations

from datetime import datetime as DateTime
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from ..video.raw import BaseVideo

if TYPE_CHECKING:
    pass


__all__ = [
    "OperationParams",
    "DurationParams",
    "ResolutionParams",
    "LogLevel",
]


class LogLevel(StrEnum):
    QUIET = "quiet"
    PANIC = "panic"
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    VERBOSE = "verbose"
    DEBUG = "debug"
    TRACE = "trace"


class BaseParams(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DurationParams(BaseParams):
    """
    Specifies duration of new clip, which may entail trimming and/or scaling.
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

    scale: float | None = None
    """
    Rescale duration with given scale factor.
    """

    target: float | None = None
    """
    Rescale duration to given value.
    """

    def model_post_init(self, __context):
        if self.scale and self.target:
            raise ValueError(
                f"Cannot provide both scale factor and target duration: scale={self.scale}, target={self.target}"
            )

        return super().model_post_init(__context)


class ResolutionParams(BaseParams):
    """
    Specifies resolution of new clip.
    """

    scale: float | None = None
    """
    Rescale resolution with given scale factor.
    """

    target: tuple[int, int] | None = None
    """
    Rescale resolution to given value.
    """

    def model_post_init(self, __context):
        if self.scale and self.target:
            raise ValueError(
                f"Cannot provide both scale factor and resolution: scale_factor={self.scale}, target={self.target}"
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

    cache: bool = False
    """
    Whether to store a cache of video metadata in input folders.
    """

    log_level: LogLevel = LogLevel.FATAL
    """
    Log level passed to ffmpeg.
    """

    # TODO: option to overwite output file if out of date, suppressing
    # interactive input by ffmpeg

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
        if scale := self.resolution_params.scale:
            pair = (
                first.resolution[0] * scale,
                first.resolution[1] * scale,
            )
        elif resolution := self.resolution_params.target:
            pair = resolution
        else:
            pair = first.resolution
        return int(pair[0]), int(pair[1])

    def _get_time_scale(self, duration_orig: float) -> float | None:
        """
        Get time scale (if any) based on target duration and original duration.
        """
        if scale := self.duration_params.scale:
            # given time scale
            return scale
        elif duration := self.duration_params.target:
            # given duration
            return duration / self._get_effective_duration(duration_orig)
        return None

    def _get_res_scale(
        self, clip_res: tuple[int, int]
    ) -> tuple[int, int] | None:
        """
        Get target resolution (if any).
        """
        if self.resolution_params.target or self.resolution_params.scale:
            return clip_res
        return None

    def _get_duration_arg(self, duration_orig: float) -> float | None:
        """
        Get -t arg, if any. Only needed if there is an end offset.
        """
        if self._trim_end:
            if scale_factor := self.duration_params.scale:
                return scale_factor * self._get_effective_duration(
                    duration_orig
                )
            elif target := self.duration_params.target:
                return target
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
