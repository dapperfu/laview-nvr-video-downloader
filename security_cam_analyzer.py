#!/usr/bin/env python3
"""
Security Camera Video Analyzer

A standalone tool for analyzing security camera videos, validating timestamps,
and extracting metadata from video files.
"""

import argparse
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import cv2
    import easyocr
    import moviepy
    import numpy as np
    import pytesseract
    from moviepy import VideoFileClip
    from PIL import Image
    MOVIEPY_AVAILABLE = True
    OCR_AVAILABLE = True
except ImportError as e:
    MOVIEPY_AVAILABLE = False
    OCR_AVAILABLE = False
    logging.warning(f"MoviePy/OCR not available: {e}. Install with: pip install moviepy opencv-python-headless pillow pytesseract easyocr")


class VideoTimestampValidator:
    """Validates video timestamps by extracting frames and analyzing timestamps."""

    def __init__(self, enable_ocr: bool = True):
        """
        Initialize the video timestamp validator.
        
        Args:
            enable_ocr: Whether to enable OCR for timestamp extraction
        """
        self.enable_ocr = enable_ocr and MOVIEPY_AVAILABLE
        self.logger = logging.getLogger(__name__)

    def validate_video_timestamps(self, video_path: str, expected_start_time: datetime,
                                expected_end_time: datetime) -> Dict[str, Any]:
        """
        Validate that a video's timestamps match the expected times.
        
        Args:
            video_path: Path to the video file
            expected_start_time: Expected start time from filename
            expected_end_time: Expected end time from filename
            
        Returns:
            Dictionary with validation results
        """
        if not self.enable_ocr:
            return {
                "valid": False,
                "error": "OCR not available - MoviePy or dependencies not installed",
            }

        try:
            # Extract frames from start and end of video
            start_frame = self._extract_frame(video_path, 0.1)  # 0.1 seconds in
            end_frame = self._extract_frame(video_path, -0.1)   # 0.1 seconds from end

            if start_frame is None or end_frame is None:
                return {
                    "valid": False,
                    "error": "Failed to extract frames from video",
                }

            # Extract timestamps from frames
            start_timestamp = self._extract_timestamp_from_frame(start_frame)
            end_timestamp = self._extract_timestamp_from_frame(end_frame)

            if start_timestamp is None or end_timestamp is None:
                return {
                    "valid": False,
                    "error": "Failed to extract timestamps from video frames",
                    "start_frame_available": start_frame is not None,
                    "end_frame_available": end_frame is not None,
                }

            # Compare with expected times
            start_match = self._compare_timestamps(start_timestamp, expected_start_time)
            end_match = self._compare_timestamps(end_timestamp, expected_end_time)

            return {
                "valid": start_match and end_match,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "expected_start": expected_start_time,
                "expected_end": expected_end_time,
                "start_match": start_match,
                "end_match": end_match,
                "start_delta": (start_timestamp - expected_start_time).total_seconds() if start_timestamp else None,
                "end_delta": (end_timestamp - expected_end_time).total_seconds() if end_timestamp else None,
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {e!s}",
            }

    def _extract_frame(self, video_path: str, time_offset: float) -> Optional["np.ndarray"]:
        """
        Extract a frame from the video at the specified time offset.
        
        Args:
            video_path: Path to the video file
            time_offset: Time offset in seconds (negative for end of video)
            
        Returns:
            Frame as numpy array or None if extraction failed
        """
        try:
            from moviepy import VideoFileClip
            with VideoFileClip(video_path) as clip:
                duration = clip.duration

                if time_offset < 0:
                    # Extract from end of video
                    frame_time = duration + time_offset
                else:
                    # Extract from beginning of video
                    frame_time = time_offset

                # Ensure frame_time is within valid range
                frame_time = max(0, min(frame_time, duration - 0.1))

                # Extract frame
                frame = clip.get_frame(frame_time)
                return frame

        except Exception as e:
            self.logger.error(f"Failed to extract frame from {video_path}: {e}")
            return None

    def _extract_timestamp_from_frame(self, frame: "np.ndarray") -> Optional[datetime]:
        """
        Extract timestamp from a video frame using OCR.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Extracted datetime or None if extraction failed
        """
        try:
            # Convert frame to PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            pil_image = Image.fromarray(frame_rgb)

            # Look for timestamp patterns in the image
            # This is a simplified approach - in practice, you'd want more sophisticated OCR
            timestamp = self._find_timestamp_in_image(pil_image)

            if timestamp:
                return self._parse_timestamp_string(timestamp)

            return None

        except Exception as e:
            self.logger.error(f"Failed to extract timestamp from frame: {e}")
            return None

    def _find_timestamp_in_image(self, image: "Image.Image") -> Optional[str]:
        """
        Find timestamp text in an image using OCR.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            Extracted timestamp string or None
        """
        if not OCR_AVAILABLE:
            return None

        try:
            # Convert PIL image to numpy array for OpenCV
            img_array = np.array(image)

            # Try EasyOCR first (more accurate for text)
            try:
                reader = easyocr.Reader(["en"])
                results = reader.readtext(img_array)

                # Look for timestamp patterns in OCR results
                for (bbox, text, confidence) in results:
                    if confidence > 0.5:  # Only consider high confidence results
                        # Look for timestamp patterns
                        timestamp = self._extract_timestamp_from_text(text)
                        if timestamp:
                            return timestamp
            except Exception as e:
                self.logger.debug(f"EasyOCR failed: {e}")

            # Fallback to Tesseract
            try:
                # Configure Tesseract for better text recognition
                custom_config = r"--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789/: -"
                text = pytesseract.image_to_string(image, config=custom_config)

                # Look for timestamp patterns in Tesseract results
                timestamp = self._extract_timestamp_from_text(text)
                if timestamp:
                    return timestamp

            except Exception as e:
                self.logger.debug(f"Tesseract failed: {e}")

            return None

        except Exception as e:
            self.logger.error(f"OCR processing failed: {e}")
            return None

    def _extract_timestamp_from_text(self, text: str) -> Optional[str]:
        """
        Extract timestamp from OCR text.
        
        Args:
            text: Text extracted from image
            
        Returns:
            Timestamp string or None
        """
        # Common timestamp patterns
        timestamp_patterns = [
            # 2025-08-24 12:39:20
            r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",
            # 08/24/2025 12:39:20
            r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}",
            # 24/08/2025 12:39:20
            r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}",
            # 2025-08-24 12:39
            r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}",
            # 08/24/2025 12:39
            r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}",
        ]

        for pattern in timestamp_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _parse_timestamp_string(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse a timestamp string into a datetime object.
        
        Args:
            timestamp_str: Timestamp string from OCR
            
        Returns:
            Parsed datetime or None
        """
        # Common timestamp formats found in NVR videos
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%m/%d/%Y %H:%M",
            "%d/%m/%Y %H:%M",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        return None

    def _compare_timestamps(self, actual: datetime, expected: datetime,
                           tolerance_seconds: int = 60) -> bool:
        """
        Compare actual and expected timestamps with tolerance.
        
        Args:
            actual: Actual timestamp from video
            expected: Expected timestamp from filename
            tolerance_seconds: Tolerance in seconds
            
        Returns:
            True if timestamps match within tolerance
        """
        if actual is None or expected is None:
            return False

        delta = abs((actual - expected).total_seconds())
        return delta <= tolerance_seconds

    def validate_video_directory(self, video_dir: str, device_timezone_offset: Optional[float] = None) -> Dict[str, Any]:
        """
        Validate all videos in a directory.
        
        Args:
            video_dir: Directory containing video files
            device_timezone_offset: Device timezone offset in hours
            
        Returns:
            Dictionary with validation results for all videos
        """
        results = {
            "total_videos": 0,
            "valid_videos": 0,
            "invalid_videos": 0,
            "errors": [],
            "details": [],
        }

        video_dir_path = Path(video_dir)
        if not video_dir_path.exists():
            results["errors"].append(f"Directory does not exist: {video_dir}")
            return results

        # Find all video files
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
        video_files = []

        for ext in video_extensions:
            video_files.extend(video_dir_path.glob(f"*{ext}"))

        results["total_videos"] = len(video_files)

        for video_file in video_files:
            try:
                # Extract expected times from filename
                expected_times = self._extract_times_from_filename(video_file.name)
                if expected_times is None:
                    results["errors"].append(f"Could not parse filename: {video_file.name}")
                    results["invalid_videos"] += 1
                    continue

                expected_start, expected_end = expected_times

                # Validate video
                validation_result = self.validate_video_timestamps(
                    str(video_file), expected_start, expected_end,
                )

                validation_result["filename"] = video_file.name
                results["details"].append(validation_result)

                if validation_result["valid"]:
                    results["valid_videos"] += 1
                else:
                    results["invalid_videos"] += 1

            except Exception as e:
                results["errors"].append(f"Error processing {video_file.name}: {e}")
                results["invalid_videos"] += 1

        return results

    def _extract_times_from_filename(self, filename: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Extract start and end times from a video filename.
        
        Args:
            filename: Video filename (e.g., "2025-08-24_12_39_20.mp4")
            
        Returns:
            Tuple of (start_time, end_time) or None if parsing failed
        """
        # Common filename patterns
        patterns = [
            # 2025-08-24_12_39_20.mp4
            r"(\d{4}-\d{2}-\d{2})_(\d{2})_(\d{2})_(\d{2})",
            # 20250824_123920.mp4
            r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})",
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    if len(match.groups()) == 4:
                        # First pattern: 2025-08-24_12_39_20
                        date_str = match.group(1)
                        hour = int(match.group(2))
                        minute = int(match.group(3))
                        second = int(match.group(4))

                        start_time = datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}:{second:02d}",
                                                      "%Y-%m-%d %H:%M:%S")

                        # Estimate end time (assuming 5-minute segments)
                        from datetime import timedelta
                        end_time = start_time + timedelta(seconds=300)

                    elif len(match.groups()) == 6:
                        # Second pattern: 20250824_123920
                        year = int(match.group(1))
                        month = int(match.group(2))
                        day = int(match.group(3))
                        hour = int(match.group(4))
                        minute = int(match.group(5))
                        second = int(match.group(6))

                        start_time = datetime(year, month, day, hour, minute, second)
                        from datetime import timedelta
                        end_time = start_time + timedelta(seconds=300)

                    return start_time, end_time

                except ValueError:
                    continue

        return None


def main():
    """Main function for the security camera analyzer."""
    parser = argparse.ArgumentParser(
        description="Security Camera Video Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate videos in a directory
  python security_cam_analyzer.py validate /path/to/videos
  
  # Analyze a single video file
  python security_cam_analyzer.py analyze video.mp4
  
  # Extract frames from a video
  python security_cam_analyzer.py extract-frames video.mp4 --output-dir frames/
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate video timestamps")
    validate_parser.add_argument("video_dir", help="Directory containing video files")
    validate_parser.add_argument("--tolerance", type=int, default=60,
                               help="Tolerance in seconds for timestamp comparison (default: 60)")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single video file")
    analyze_parser.add_argument("video_file", help="Video file to analyze")

    # Extract frames command
    extract_parser = subparsers.add_parser("extract-frames", help="Extract frames from video")
    extract_parser.add_argument("video_file", help="Video file to extract frames from")
    extract_parser.add_argument("--output-dir", default="frames", help="Output directory for frames")
    extract_parser.add_argument("--interval", type=float, default=1.0,
                              help="Frame extraction interval in seconds (default: 1.0)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "validate":
        validate_videos(args.video_dir, args.tolerance)
    elif args.command == "analyze":
        analyze_video(args.video_file)
    elif args.command == "extract-frames":
        extract_frames(args.video_file, args.output_dir, args.interval)


def validate_videos(video_dir: str, tolerance: int = 60):
    """Validate video timestamps in a directory."""
    print(f"Validating videos in: {video_dir}")
    print("-" * 50)

    validator = VideoTimestampValidator()
    results = validator.validate_video_directory(video_dir)

    # Print results
    print("\nValidation Results:")
    print(f"Total videos: {results['total_videos']}")
    print(f"Valid videos: {results['valid_videos']}")
    print(f"Invalid videos: {results['invalid_videos']}")

    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"][:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(results["errors"]) > 10:
            print(f"  ... and {len(results['errors']) - 10} more errors")

    if results["details"]:
        print("\nDetailed Results:")
        for detail in results["details"][:10]:  # Show first 10 results
            status = "✅" if detail["valid"] else "❌"
            print(f"  {status} {detail['filename']}")
            if not detail["valid"] and "error" in detail:
                print(f"    Error: {detail['error']}")

        if len(results["details"]) > 10:
            print(f"  ... and {len(results['details']) - 10} more videos")


def analyze_video(video_file: str):
    """Analyze a single video file."""
    print(f"Analyzing video: {video_file}")
    print("-" * 50)

    if not os.path.exists(video_file):
        print(f"Error: Video file does not exist: {video_file}")
        return

    if not MOVIEPY_AVAILABLE:
        print("Error: MoviePy not available. Install with: pip install moviepy opencv-python-headless pillow")
        return

    try:
        from moviepy import VideoFileClip
        with VideoFileClip(video_file) as clip:
            print(f"Duration: {clip.duration:.2f} seconds")
            print(f"FPS: {clip.fps}")
            print(f"Size: {clip.size}")
            print(f"Audio: {'Yes' if clip.audio else 'No'}")

            # Extract expected times from filename
            validator = VideoTimestampValidator()
            expected_times = validator._extract_times_from_filename(os.path.basename(video_file))

            if expected_times:
                start_time, end_time = expected_times
                print(f"Expected start time: {start_time}")
                print(f"Expected end time: {end_time}")

                # Validate timestamps
                validation_result = validator.validate_video_timestamps(video_file, start_time, end_time)
                print(f"Timestamp validation: {'✅ Valid' if validation_result['valid'] else '❌ Invalid'}")
                if not validation_result["valid"] and "error" in validation_result:
                    print(f"  Error: {validation_result['error']}")
            else:
                print("Could not parse expected times from filename")

    except Exception as e:
        print(f"Error analyzing video: {e}")


def extract_frames(video_file: str, output_dir: str, interval: float):
    """Extract frames from a video file."""
    print(f"Extracting frames from: {video_file}")
    print(f"Output directory: {output_dir}")
    print(f"Interval: {interval} seconds")
    print("-" * 50)

    if not os.path.exists(video_file):
        print(f"Error: Video file does not exist: {video_file}")
        return

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    try:
        from moviepy import VideoFileClip
        with VideoFileClip(video_file) as clip:
            duration = clip.duration
            print(f"Video duration: {duration:.2f} seconds")

            frame_count = 0
            for time in range(0, int(duration), int(interval)):
                frame = clip.get_frame(time)
                frame_filename = os.path.join(output_dir, f"frame_{time:06d}.jpg")

                # Save frame as JPEG
                import cv2
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(frame_filename, frame_bgr)

                frame_count += 1
                if frame_count % 10 == 0:
                    print(f"Extracted {frame_count} frames...")

            print(f"Extracted {frame_count} frames to {output_dir}")

    except Exception as e:
        print(f"Error extracting frames: {e}")


if __name__ == "__main__":
    main()
