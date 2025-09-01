"""
Timestamp Extractor Module

Extracts date and time information from video files using various methods:
1. Filename parsing
2. File metadata
3. OCR from video frames (if enabled)
4. Video stream metadata
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json

try:
    from moviepy.editor import VideoFileClip
    import cv2
    import numpy as np
    from PIL import Image
    import pytesseract
    MOVIEPY_AVAILABLE = True
    OCR_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    OCR_AVAILABLE = False
    logging.warning("MoviePy/OpenCV/PIL not available. Install with: pip install moviepy opencv-python-headless pillow pytesseract")


class TimestampExtractor:
    """
    Extracts timestamps from video files using multiple methods.
    
    This class provides various methods to extract date and time information
    from video files, including filename parsing, metadata extraction, and OCR.
    """
    
    def __init__(self, enable_ocr: bool = True) -> None:
        """
        Initialize the timestamp extractor.
        
        Args:
            enable_ocr: Whether to enable OCR for timestamp extraction from frames
        """
        self.logger = logging.getLogger(__name__)
        self.enable_ocr = enable_ocr and MOVIEPY_AVAILABLE and OCR_AVAILABLE
        
        # Common timestamp patterns in filenames
        self.timestamp_patterns = [
            # YYYY-MM-DD HH:MM:SS
            r'(\d{4})-(\d{2})-(\d{2})[_\s](\d{2}):(\d{2}):(\d{2})',
            # YYYYMMDD_HHMMSS
            r'(\d{4})(\d{2})(\d{2})[_\s](\d{2})(\d{2})(\d{2})',
            # MM-DD-YYYY HH:MM:SS
            r'(\d{2})-(\d{2})-(\d{4})[_\s](\d{2}):(\d{2}):(\d{2})',
            # DD-MM-YYYY HH:MM:SS
            r'(\d{2})-(\d{2})-(\d{4})[_\s](\d{2}):(\d{2}):(\d{2})',
            # YYYY_MM_DD_HH_MM_SS
            r'(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})',
        ]
        
        self.logger.info("TimestampExtractor initialized with OCR=%s", self.enable_ocr)
    
    def extract_timestamps(self, video_path: str) -> Dict[str, Any]:
        """
        Extract timestamps from a video file using all available methods.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing timestamp extraction results
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.logger.info("Extracting timestamps from: %s", video_path)
        
        results = {
            "video_path": str(video_path),
            "filename_timestamp": None,
            "metadata_timestamp": None,
            "ocr_timestamp": None,
            "best_estimate": None,
            "confidence": "low",
            "methods_used": [],
            "errors": []
        }
        
        # Method 1: Extract from filename
        try:
            filename_timestamp = self._extract_from_filename(video_path.name)
            if filename_timestamp:
                results["filename_timestamp"] = filename_timestamp.isoformat()
                results["methods_used"].append("filename_parsing")
                self.logger.info("Found timestamp in filename: %s", filename_timestamp)
        except Exception as e:
            error_msg = f"Failed to extract timestamp from filename: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        # Method 2: Extract from file metadata
        try:
            metadata_timestamp = self._extract_from_metadata(video_path)
            if metadata_timestamp:
                results["metadata_timestamp"] = metadata_timestamp.isoformat()
                results["methods_used"].append("file_metadata")
                self.logger.info("Found timestamp in metadata: %s", metadata_timestamp)
        except Exception as e:
            error_msg = f"Failed to extract timestamp from metadata: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        # Method 3: Extract using OCR (if enabled)
        if self.enable_ocr:
            try:
                ocr_timestamp = self._extract_using_ocr(str(video_path))
                if ocr_timestamp:
                    results["ocr_timestamp"] = ocr_timestamp.isoformat()
                    results["methods_used"].append("ocr")
                    self.logger.info("Found timestamp using OCR: %s", ocr_timestamp)
            except Exception as e:
                error_msg = f"Failed to extract timestamp using OCR: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Determine best estimate
        best_estimate, confidence = self._determine_best_estimate(results)
        results["best_estimate"] = best_estimate.isoformat() if best_estimate else None
        results["confidence"] = confidence
        
        self.logger.info("Timestamp extraction completed. Best estimate: %s (confidence: %s)", 
                        best_estimate, confidence)
        
        return results
    
    def _extract_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract timestamp from filename using pattern matching.
        
        Args:
            filename: Name of the video file
            
        Returns:
            Extracted datetime or None if not found
        """
        for pattern in self.timestamp_patterns:
            match = re.search(pattern, filename)
            if match:
                groups = match.groups()
                
                # Handle different pattern formats
                if len(groups) == 6:
                    if len(groups[0]) == 4:  # YYYY-MM-DD format
                        year, month, day, hour, minute, second = groups
                    elif len(groups[0]) == 2:  # MM-DD-YYYY or DD-MM-YYYY format
                        # Try both MM-DD-YYYY and DD-MM-YYYY
                        try:
                            # Try MM-DD-YYYY first
                            month, day, year, hour, minute, second = groups
                            return datetime(int(year), int(month), int(day), 
                                          int(hour), int(minute), int(second))
                        except ValueError:
                            # Try DD-MM-YYYY
                            day, month, year, hour, minute, second = groups
                            return datetime(int(year), int(month), int(day), 
                                          int(hour), int(minute), int(second))
                    else:  # YYYYMMDD format
                        year, month, day, hour, minute, second = groups
                        return datetime(int(year), int(month), int(day), 
                                      int(hour), int(minute), int(second))
        
        return None
    
    def _extract_from_metadata(self, video_path: Path) -> Optional[datetime]:
        """
        Extract timestamp from file metadata.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Extracted datetime or None if not found
        """
        try:
            stat = video_path.stat()
            
            # Use modification time as a fallback
            return datetime.fromtimestamp(stat.st_mtime)
        except Exception as e:
            self.logger.error("Failed to extract metadata timestamp: %s", e)
            return None
    
    def _extract_using_ocr(self, video_path: str) -> Optional[datetime]:
        """
        Extract timestamp from video frames using OCR.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Extracted datetime or None if not found
        """
        if not self.enable_ocr:
            return None
        
        try:
            # Extract frames from different parts of the video
            frames = self._extract_sample_frames(video_path)
            
            for frame in frames:
                timestamp = self._extract_timestamp_from_frame(frame)
                if timestamp:
                    return timestamp
            
            return None
            
        except Exception as e:
            self.logger.error("OCR timestamp extraction failed: %s", e)
            return None
    
    def _extract_sample_frames(self, video_path: str) -> List["np.ndarray"]:
        """
        Extract sample frames from video for OCR analysis.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            List of frames as numpy arrays
        """
        frames = []
        
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            
            # Extract frames at different positions
            positions = [0.1, 0.5, 0.9]  # 10%, 50%, 90% of video
            
            for pos in positions:
                if pos < duration:
                    frame_time = pos * duration
                    frame = clip.get_frame(frame_time)
                    frames.append(frame)
            
            clip.close()
            
        except Exception as e:
            self.logger.error("Failed to extract frames: %s", e)
        
        return frames
    
    def _extract_timestamp_from_frame(self, frame: "np.ndarray") -> Optional[datetime]:
        """
        Extract timestamp from a single frame using OCR.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Extracted datetime or None if not found
        """
        try:
            # Convert frame to PIL Image
            image = Image.fromarray(frame)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            
            # Look for timestamp patterns in the extracted text
            for pattern in self.timestamp_patterns:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    if len(groups) == 6:
                        year, month, day, hour, minute, second = groups
                        return datetime(int(year), int(month), int(day), 
                                      int(hour), int(minute), int(second))
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to extract timestamp from frame: %s", e)
            return None
    
    def _determine_best_estimate(self, results: Dict[str, Any]) -> Tuple[Optional[datetime], str]:
        """
        Determine the best timestamp estimate from available methods.
        
        Args:
            results: Dictionary containing extraction results
            
        Returns:
            Tuple of (best_estimate, confidence_level)
        """
        timestamps = []
        
        # Collect all available timestamps
        if results["filename_timestamp"]:
            timestamps.append(("filename", datetime.fromisoformat(results["filename_timestamp"])))
        
        if results["metadata_timestamp"]:
            timestamps.append(("metadata", datetime.fromisoformat(results["metadata_timestamp"])))
        
        if results["ocr_timestamp"]:
            timestamps.append(("ocr", datetime.fromisoformat(results["ocr_timestamp"])))
        
        if not timestamps:
            return None, "none"
        
        # If only one timestamp available
        if len(timestamps) == 1:
            return timestamps[0][1], "low"
        
        # If multiple timestamps available, check for consistency
        if len(timestamps) >= 2:
            # Check if timestamps are consistent (within reasonable range)
            timestamps.sort(key=lambda x: x[1])
            
            # Calculate time differences
            time_diffs = []
            for i in range(1, len(timestamps)):
                diff = abs((timestamps[i][1] - timestamps[i-1][1]).total_seconds())
                time_diffs.append(diff)
            
            # If timestamps are consistent (within 1 hour), use the most reliable one
            if all(diff < 3600 for diff in time_diffs):
                # Prefer filename timestamp as it's usually most accurate
                for method, timestamp in timestamps:
                    if method == "filename":
                        return timestamp, "high"
                
                # Fall back to first available
                return timestamps[0][1], "medium"
            else:
                # Inconsistent timestamps, use the most reliable method
                for method, timestamp in timestamps:
                    if method == "filename":
                        return timestamp, "medium"
                
                return timestamps[0][1], "low"
        
        return timestamps[0][1], "low"
