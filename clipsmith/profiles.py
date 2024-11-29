"""
Collection of profiles from various vendors.
"""

from .profile import BaseProfile


class GarminDashcamMini2(BaseProfile):
    profile_id = "garmin-dashcam-mini2"
    datetime_rect_pct = ((80.0, 0.0), (100.0, 20.0))


ALL_PROFILES = [
    GarminDashcamMini2,
]
