"""
LaView NVR Video Downloader

A tool for downloading video recordings from LaView NVR devices.
"""

from . import (
    authtype,
    camerasdk,
    cli,
    config,
    date_parser,
    logging,
    time_interval,
    track,
    utils,
    work,
)

__version__ = "1.0.0"
__all__ = [
    "authtype",
    "camerasdk",
    "cli",
    "config",
    "date_parser",
    "logging",
    "time_interval",
    "track",
    "utils",
    "work",
]
