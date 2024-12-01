"""
Encapsulates parameters from which to get additional information from a
video file, e.g. the location of the date/time stamp.
"""


class BaseProfile:
    profile_id: str

    datetime_rect: tuple[tuple[float, float], tuple[float, float]] | None = None
    """
    Location of datetime as tuple of upper-left coordinate and size, both
    specified in terms of percents. 
    """


class DefaultProfile(BaseProfile):
    """
    Profile used if none specified.
    """

    profile_id = "default"
