"""
Tests for the VideoAnalyzer class.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from nvr_analysis.video_analyzer import VideoAnalyzer


class TestVideoAnalyzer:
    """Test cases for VideoAnalyzer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analyzer = VideoAnalyzer(enable_ocr=False, enable_ai=False)

    def test_init(self) -> None:
        """Test VideoAnalyzer initialization."""
        analyzer = VideoAnalyzer(enable_ocr=True, enable_ai=True)
        assert analyzer.enable_ocr is True
        assert analyzer.enable_ai is True

        analyzer = VideoAnalyzer(enable_ocr=False, enable_ai=False)
        assert analyzer.enable_ocr is False
        assert analyzer.enable_ai is False

    def test_get_file_info(self, tmp_path: Path) -> None:
        """Test file information extraction."""
        # Create a dummy video file
        video_file = tmp_path / "test_video.mp4"
        video_file.write_text("dummy video content")

        file_info = self.analyzer._get_file_info(video_file)

        assert file_info["filename"] == "test_video.mp4"
        assert file_info["extension"] == ".mp4"
        assert file_info["size_bytes"] > 0
        assert "size_mb" in file_info
        assert "created_time" in file_info
        assert "modified_time" in file_info

    def test_analyze_video_file_not_found(self) -> None:
        """Test analysis with non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.analyzer.analyze_video("nonexistent_video.mp4")

    @patch("nvr_analysis.video_analyzer.MOVIEPY_AVAILABLE", False)
    def test_analyze_video_no_moviepy(self, tmp_path: Path) -> None:
        """Test analysis when MoviePy is not available."""
        # Create a dummy video file
        video_file = tmp_path / "test_video.mp4"
        video_file.write_text("dummy video content")

        results = self.analyzer.analyze_video(str(video_file))

        assert results["video_path"] == str(video_file)
        assert "analysis_timestamp" in results
        assert "file_info" in results
        assert "timestamps" in results
        assert "metadata" in results
        assert "errors" in results

    def test_extract_timestamps_only(self) -> None:
        """Test timestamp-only extraction."""
        # This is a basic test - in a real scenario, you'd need actual video files
        # or mock the dependencies

    def test_extract_metadata_only(self) -> None:
        """Test metadata-only extraction."""
        # This is a basic test - in a real scenario, you'd need actual video files
        # or mock the dependencies

    def test_perform_ai_analysis(self) -> None:
        """Test AI analysis placeholder."""
        results = self.analyzer._perform_ai_analysis("dummy_video.mp4")

        assert results["status"] == "not_implemented"
        assert "message" in results
        assert "planned_features" in results
        assert "face_recognition" in results["planned_features"]
        assert "object_detection" in results["planned_features"]
