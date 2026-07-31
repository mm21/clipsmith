"""
Collection of profiles from various vendors.
"""

from .profile import BaseProfile

__all__ = [
    "GarminDashcamMini2",
]


class GarminDashcamMini2(BaseProfile):
    profile_id = "garmin-dashcam-mini2"
    datetime_rect = ((80.0, 0.0), (100.0, 20.0))


ALL_PROFILES = [
    GarminDashcamMini2,
]
