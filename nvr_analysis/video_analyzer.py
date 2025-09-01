"""
Video Analyzer Module

Main video analysis coordinator that handles different types of video analysis
including timestamp extraction, metadata extraction, and future AI-powered features.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .timestamp_extractor import TimestampExtractor
from .metadata_extractor import MetadataExtractor


class VideoAnalyzer:
    """
    Main video analyzer class that coordinates different analysis tasks.
    
    This class serves as the primary interface for analyzing video files,
    extracting timestamps, metadata, and performing AI-powered analysis.
    """
    
    def __init__(self, enable_ocr: bool = True, enable_ai: bool = False) -> None:
        """
        Initialize the video analyzer.
        
        Args:
            enable_ocr: Whether to enable OCR for timestamp extraction
            enable_ai: Whether to enable AI-powered features (future use)
        """
        self.logger = logging.getLogger(__name__)
        self.enable_ocr = enable_ocr
        self.enable_ai = enable_ai
        
        # Initialize analysis components
        self.timestamp_extractor = TimestampExtractor(enable_ocr=enable_ocr)
        self.metadata_extractor = MetadataExtractor()
        
        self.logger.info("VideoAnalyzer initialized with OCR=%s, AI=%s", enable_ocr, enable_ai)
    
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a video file.
        
        Args:
            video_path: Path to the video file to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.logger.info("Starting analysis of video: %s", video_path)
        
        results = {
            "video_path": str(video_path),
            "analysis_timestamp": datetime.now().isoformat(),
            "file_info": {},
            "timestamps": {},
            "metadata": {},
            "errors": []
        }
        
        try:
            # Extract basic file information
            results["file_info"] = self._get_file_info(video_path)
            
            # Extract timestamps
            try:
                results["timestamps"] = self.timestamp_extractor.extract_timestamps(str(video_path))
            except Exception as e:
                error_msg = f"Failed to extract timestamps: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
            
            # Extract metadata
            try:
                results["metadata"] = self.metadata_extractor.extract_metadata(str(video_path))
            except Exception as e:
                error_msg = f"Failed to extract metadata: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
            
            # Future: AI-powered analysis
            if self.enable_ai:
                try:
                    results["ai_analysis"] = self._perform_ai_analysis(str(video_path))
                except Exception as e:
                    error_msg = f"Failed to perform AI analysis: {e}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"Analysis failed: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        self.logger.info("Analysis completed for video: %s", video_path)
        return results
    
    def extract_timestamps_only(self, video_path: str) -> Dict[str, Any]:
        """
        Extract only timestamps from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing timestamp extraction results
        """
        return self.timestamp_extractor.extract_timestamps(video_path)
    
    def extract_metadata_only(self, video_path: str) -> Dict[str, Any]:
        """
        Extract only metadata from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing metadata extraction results
        """
        return self.metadata_extractor.extract_metadata(video_path)
    
    def _get_file_info(self, video_path: Path) -> Dict[str, Any]:
        """
        Get basic file information.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing file information
        """
        stat = video_path.stat()
        
        return {
            "filename": video_path.name,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
        }
    
    def _perform_ai_analysis(self, video_path: str) -> Dict[str, Any]:
        """
        Perform AI-powered analysis (placeholder for future implementation).
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing AI analysis results
        """
        # Placeholder for future AI features
        return {
            "status": "not_implemented",
            "message": "AI analysis features are not yet implemented",
            "planned_features": [
                "face_recognition",
                "object_detection", 
                "motion_analysis",
                "person_tracking"
            ]
        }
