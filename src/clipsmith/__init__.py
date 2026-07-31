"""
ClipSmith: Utility to work with video clips, especially suited for creating timelapses
from dashcam footage.
"""

__submodules__ = ["context", "clip", "video"]

# isort: off
# <AUTOGEN_INIT>
from .context import (
    Context,
)
from .clip import (
    Clip,
    OperationParams,
    DurationParams,
    ResolutionParams,
    LogLevel,
)
from .video import (
    BaseVideo,
    RawVideoMetadata,
    RawVideo,
)

__all__ = [
    "Context",
    "Clip",
    "OperationParams",
    "DurationParams",
    "ResolutionParams",
    "LogLevel",
    "BaseVideo",
    "RawVideoMetadata",
    "RawVideo",
]
# </AUTOGEN_INIT>
