"""
Metadata Extractor Module

Extracts technical metadata from video files including:
- Video codec information
- Audio codec information
- Resolution and frame rate
- Duration and bitrate
- File format details
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("MoviePy not available. Install with: pip install moviepy")

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV not available. Install with: pip install opencv-python-headless")


class MetadataExtractor:
    """
    Extracts technical metadata from video files.
    
    This class provides methods to extract comprehensive technical information
    from video files including codec details, resolution, frame rate, etc.
    """
    
    def __init__(self) -> None:
        """Initialize the metadata extractor."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("MetadataExtractor initialized")
    
    def extract_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing video metadata
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.logger.info("Extracting metadata from: %s", video_path)
        
        results = {
            "video_path": str(video_path),
            "basic_info": {},
            "video_stream": {},
            "audio_stream": {},
            "file_info": {},
            "errors": []
        }
        
        # Extract basic file information
        try:
            results["basic_info"] = self._extract_basic_info(video_path)
        except Exception as e:
            error_msg = f"Failed to extract basic info: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        # Extract video stream information
        try:
            results["video_stream"] = self._extract_video_stream_info(str(video_path))
        except Exception as e:
            error_msg = f"Failed to extract video stream info: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        # Extract audio stream information
        try:
            results["audio_stream"] = self._extract_audio_stream_info(str(video_path))
        except Exception as e:
            error_msg = f"Failed to extract audio stream info: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        # Extract file format information
        try:
            results["file_info"] = self._extract_file_info(video_path)
        except Exception as e:
            error_msg = f"Failed to extract file info: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        self.logger.info("Metadata extraction completed for: %s", video_path)
        return results
    
    def _extract_basic_info(self, video_path: Path) -> Dict[str, Any]:
        """
        Extract basic file information.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing basic file information
        """
        stat = video_path.stat()
        
        return {
            "filename": video_path.name,
            "extension": video_path.suffix.lower(),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "size_gb": round(stat.st_size / (1024 * 1024 * 1024), 2),
        }
    
    def _extract_video_stream_info(self, video_path: str) -> Dict[str, Any]:
        """
        Extract video stream information using MoviePy.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing video stream information
        """
        if not MOVIEPY_AVAILABLE:
            return {"error": "MoviePy not available"}
        
        try:
            clip = VideoFileClip(video_path)
            
            # Get video properties
            duration = clip.duration
            fps = clip.fps
            size = clip.size
            
            # Calculate bitrate (approximate)
            file_size = Path(video_path).stat().st_size
            bitrate = (file_size * 8) / duration if duration > 0 else 0
            
            video_info = {
                "duration_seconds": round(duration, 2),
                "duration_formatted": self._format_duration(duration),
                "fps": round(fps, 2) if fps else None,
                "width": size[0],
                "height": size[1],
                "resolution": f"{size[0]}x{size[1]}",
                "aspect_ratio": round(size[0] / size[1], 2) if size[1] > 0 else None,
                "bitrate_kbps": round(bitrate / 1000, 2),
                "bitrate_mbps": round(bitrate / 1000000, 2),
            }
            
            clip.close()
            return video_info
            
        except Exception as e:
            self.logger.error("Failed to extract video stream info: %s", e)
            return {"error": str(e)}
    
    def _extract_audio_stream_info(self, video_path: str) -> Dict[str, Any]:
        """
        Extract audio stream information using MoviePy.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing audio stream information
        """
        if not MOVIEPY_AVAILABLE:
            return {"error": "MoviePy not available"}
        
        try:
            clip = VideoFileClip(video_path)
            
            # Check if audio is present
            if hasattr(clip, 'audio') and clip.audio is not None:
                audio_info = {
                    "has_audio": True,
                    "audio_fps": clip.audio.fps if hasattr(clip.audio, 'fps') else None,
                    "audio_nchannels": clip.audio.nchannels if hasattr(clip.audio, 'nchannels') else None,
                }
            else:
                audio_info = {
                    "has_audio": False,
                }
            
            clip.close()
            return audio_info
            
        except Exception as e:
            self.logger.error("Failed to extract audio stream info: %s", e)
            return {"error": str(e)}
    
    def _extract_file_info(self, video_path: Path) -> Dict[str, Any]:
        """
        Extract file format information.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing file format information
        """
        # Common video formats and their details
        format_info = {
            ".mp4": {
                "format": "MP4",
                "container": "MPEG-4 Part 14",
                "description": "MPEG-4 video container"
            },
            ".avi": {
                "format": "AVI",
                "container": "Audio Video Interleave",
                "description": "Microsoft AVI container"
            },
            ".mkv": {
                "format": "MKV",
                "container": "Matroska",
                "description": "Matroska multimedia container"
            },
            ".mov": {
                "format": "MOV",
                "container": "QuickTime File Format",
                "description": "Apple QuickTime container"
            },
            ".wmv": {
                "format": "WMV",
                "container": "Windows Media Video",
                "description": "Microsoft Windows Media container"
            },
            ".flv": {
                "format": "FLV",
                "container": "Flash Video",
                "description": "Adobe Flash Video container"
            },
            ".webm": {
                "format": "WebM",
                "container": "WebM",
                "description": "WebM multimedia container"
            },
            ".m4v": {
                "format": "M4V",
                "container": "MPEG-4 Video",
                "description": "Apple MPEG-4 video container"
            }
        }
        
        extension = video_path.suffix.lower()
        return format_info.get(extension, {
            "format": "Unknown",
            "container": "Unknown",
            "description": f"Unknown format: {extension}"
        })
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in seconds to human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            remaining_seconds = seconds % 60
            return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"
    
    def get_summary(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the extracted metadata.
        
        Args:
            metadata: Complete metadata dictionary
            
        Returns:
            Dictionary containing metadata summary
        """
        summary = {
            "filename": metadata.get("basic_info", {}).get("filename", "Unknown"),
            "file_size": metadata.get("basic_info", {}).get("size_mb", 0),
            "duration": metadata.get("video_stream", {}).get("duration_formatted", "Unknown"),
            "resolution": metadata.get("video_stream", {}).get("resolution", "Unknown"),
            "fps": metadata.get("video_stream", {}).get("fps", "Unknown"),
            "has_audio": metadata.get("audio_stream", {}).get("has_audio", False),
            "format": metadata.get("file_info", {}).get("format", "Unknown"),
        }
        
        return summary
