"""
Tests for the TimestampExtractor class.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from nvr_analysis.timestamp_extractor import TimestampExtractor


class TestTimestampExtractor:
    """Test cases for TimestampExtractor class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.extractor = TimestampExtractor(enable_ocr=False)

    def test_init(self) -> None:
        """Test TimestampExtractor initialization."""
        extractor = TimestampExtractor(enable_ocr=True)
        assert extractor.enable_ocr is True

        extractor = TimestampExtractor(enable_ocr=False)
        assert extractor.enable_ocr is False

    def test_extract_from_filename_patterns(self) -> None:
        """Test timestamp extraction from various filename patterns."""
        test_cases = [
            ("video_2024-01-15_10:30:00.mp4", datetime(2024, 1, 15, 10, 30, 0)),
            ("video_20240115_103000.mp4", datetime(2024, 1, 15, 10, 30, 0)),
            ("video_01-15-2024_10:30:00.mp4", datetime(2024, 1, 15, 10, 30, 0)),
            ("video_15-01-2024_10:30:00.mp4", datetime(2024, 1, 15, 10, 30, 0)),
            ("video_2024_01_15_10_30_00.mp4", datetime(2024, 1, 15, 10, 30, 0)),
        ]

        for filename, expected in test_cases:
            result = self.extractor._extract_from_filename(filename)
            assert result == expected

    def test_extract_from_filename_no_match(self) -> None:
        """Test timestamp extraction with no matching pattern."""
        filename = "video_without_timestamp.mp4"
        result = self.extractor._extract_from_filename(filename)
        assert result is None

    def test_extract_from_metadata(self, tmp_path: Path) -> None:
        """Test timestamp extraction from file metadata."""
        # Create a dummy file
        test_file = tmp_path / "test_video.mp4"
        test_file.write_text("dummy content")

        result = self.extractor._extract_from_metadata(test_file)

        assert isinstance(result, datetime)
        assert result.year > 2000  # Should be a recent date

    def test_determine_best_estimate_single_timestamp(self) -> None:
        """Test best estimate determination with single timestamp."""
        results = {
            "filename_timestamp": "2024-01-15T10:30:00",
            "metadata_timestamp": None,
            "ocr_timestamp": None,
        }

        best_estimate, confidence = self.extractor._determine_best_estimate(results)

        assert best_estimate == datetime(2024, 1, 15, 10, 30, 0)
        assert confidence == "low"

    def test_determine_best_estimate_multiple_consistent(self) -> None:
        """Test best estimate determination with multiple consistent timestamps."""
        results = {
            "filename_timestamp": "2024-01-15T10:30:00",
            "metadata_timestamp": "2024-01-15T10:31:00",  # 1 minute difference
            "ocr_timestamp": None,
        }

        best_estimate, confidence = self.extractor._determine_best_estimate(results)

        # Should prefer filename timestamp
        assert best_estimate == datetime(2024, 1, 15, 10, 30, 0)
        assert confidence == "high"

    def test_determine_best_estimate_inconsistent(self) -> None:
        """Test best estimate determination with inconsistent timestamps."""
        results = {
            "filename_timestamp": "2024-01-15T10:30:00",
            "metadata_timestamp": "2024-01-16T10:30:00",  # 1 day difference
            "ocr_timestamp": None,
        }

        best_estimate, confidence = self.extractor._determine_best_estimate(results)

        # Should prefer filename timestamp but with medium confidence
        assert best_estimate == datetime(2024, 1, 15, 10, 30, 0)
        assert confidence == "medium"

    def test_determine_best_estimate_no_timestamps(self) -> None:
        """Test best estimate determination with no timestamps."""
        results = {
            "filename_timestamp": None,
            "metadata_timestamp": None,
            "ocr_timestamp": None,
        }

        best_estimate, confidence = self.extractor._determine_best_estimate(results)

        assert best_estimate is None
        assert confidence == "none"

    @patch("nvr_analysis.timestamp_extractor.MOVIEPY_AVAILABLE", False)
    def test_extract_timestamps_no_moviepy(self, tmp_path: Path) -> None:
        """Test timestamp extraction when MoviePy is not available."""
        # Create a dummy video file
        video_file = tmp_path / "test_video_2024-01-15_10:30:00.mp4"
        video_file.write_text("dummy video content")

        results = self.extractor.extract_timestamps(str(video_file))

        assert results["video_path"] == str(video_file)
        assert results["filename_timestamp"] == "2024-01-15T10:30:00"
        assert results["ocr_timestamp"] is None
        assert "best_estimate" in results
        assert "confidence" in results
        assert "methods_used" in results
        assert "errors" in results
