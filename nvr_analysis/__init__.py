"""
NVR Analysis Tool

A Python package for analyzing video files from NVR systems, extracting metadata,
timestamps, and performing AI-powered analysis including face recognition and
object detection.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .video_analyzer import VideoAnalyzer
from .timestamp_extractor import TimestampExtractor
from .metadata_extractor import MetadataExtractor

__all__ = [
    "VideoAnalyzer",
    "TimestampExtractor", 
    "MetadataExtractor",
]
