"""
ClipSmith: Utility to work with video clips, especially suited for creating 
timelapses from dashcam footage.
"""

from pyrollup import rollup

from .clip import *  # noqa
from .context import *  # noqa
from .video import *  # noqa

__all__ = rollup(context, clip, video)
