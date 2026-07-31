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
    DurationParams,
    LogLevel,
    OperationParams,
    ResolutionParams,
)
from .video import (
    BaseVideo,
    RawVideo,
    RawVideoMetadata,
)

__all__ = [
    "BaseVideo",
    "Clip",
    "Context",
    "DurationParams",
    "LogLevel",
    "OperationParams",
    "RawVideo",
    "RawVideoMetadata",
    "ResolutionParams",
]
# </AUTOGEN_INIT>
