from __future__ import annotations

from datetime import datetime as DateTime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from ..video import BaseVideo

if TYPE_CHECKING:
    pass


__all__ = [
    "OperationParams",
    "DurationParams",
    "ResolutionParams",
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
