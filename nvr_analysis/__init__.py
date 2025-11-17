"""
NVR Analysis Tool

A Python package for analyzing video files from NVR systems, extracting metadata,
timestamps, and performing AI-powered analysis including face recognition and
object detection.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .metadata_extractor import MetadataExtractor
from .timestamp_extractor import TimestampExtractor
from .video_analyzer import VideoAnalyzer

__all__ = [
    "VideoAnalyzer",
    "TimestampExtractor",
    "MetadataExtractor",
]
