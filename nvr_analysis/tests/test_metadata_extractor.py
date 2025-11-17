"""
Tests for the MetadataExtractor class.
"""

from pathlib import Path
from unittest.mock import patch

from nvr_analysis.metadata_extractor import MetadataExtractor


class TestMetadataExtractor:
    """Test cases for MetadataExtractor class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.extractor = MetadataExtractor()

    def test_init(self) -> None:
        """Test MetadataExtractor initialization."""
        extractor = MetadataExtractor()
        assert extractor is not None

    def test_extract_basic_info(self, tmp_path: Path) -> None:
        """Test basic file information extraction."""
        # Create a dummy video file
        video_file = tmp_path / "test_video.mp4"
        video_file.write_text("dummy video content")

        basic_info = self.extractor._extract_basic_info(video_file)

        assert basic_info["filename"] == "test_video.mp4"
        assert basic_info["extension"] == ".mp4"
        assert basic_info["size_bytes"] > 0
        assert basic_info["size_mb"] > 0
        assert basic_info["size_gb"] > 0
        assert "created_time" in basic_info
        assert "modified_time" in basic_info
        assert "accessed_time" in basic_info

    def test_extract_file_info_mp4(self) -> None:
        """Test file format information extraction for MP4."""
        video_path = Path("test_video.mp4")
        file_info = self.extractor._extract_file_info(video_path)

        assert file_info["format"] == "MP4"
        assert file_info["container"] == "MPEG-4 Part 14"
        assert file_info["description"] == "MPEG-4 video container"

    def test_extract_file_info_avi(self) -> None:
        """Test file format information extraction for AVI."""
        video_path = Path("test_video.avi")
        file_info = self.extractor._extract_file_info(video_path)

        assert file_info["format"] == "AVI"
        assert file_info["container"] == "Audio Video Interleave"
        assert file_info["description"] == "Microsoft AVI container"

    def test_extract_file_info_unknown(self) -> None:
        """Test file format information extraction for unknown format."""
        video_path = Path("test_video.xyz")
        file_info = self.extractor._extract_file_info(video_path)

        assert file_info["format"] == "Unknown"
        assert file_info["container"] == "Unknown"
        assert file_info["description"] == "Unknown format: .xyz"

    def test_format_duration_seconds(self) -> None:
        """Test duration formatting for seconds."""
        result = self.extractor._format_duration(30.5)
        assert result == "30.5s"

    def test_format_duration_minutes(self) -> None:
        """Test duration formatting for minutes."""
        result = self.extractor._format_duration(125.5)
        assert result == "2m 5.5s"

    def test_format_duration_hours(self) -> None:
        """Test duration formatting for hours."""
        result = self.extractor._format_duration(7325.5)  # 2h 2m 5.5s
        assert result == "2h 2m 5.5s"

    def test_get_summary(self) -> None:
        """Test metadata summary generation."""
        metadata = {
            "basic_info": {
                "filename": "test_video.mp4",
                "size_mb": 45.2,
            },
            "video_stream": {
                "duration_formatted": "2m 30s",
                "resolution": "1920x1080",
                "fps": 30.0,
            },
            "audio_stream": {
                "has_audio": True,
            },
            "file_info": {
                "format": "MP4",
            },
        }

        summary = self.extractor.get_summary(metadata)

        assert summary["filename"] == "test_video.mp4"
        assert summary["file_size"] == 45.2
        assert summary["duration"] == "2m 30s"
        assert summary["resolution"] == "1920x1080"
        assert summary["fps"] == 30.0
        assert summary["has_audio"] is True
        assert summary["format"] == "MP4"

    def test_get_summary_missing_data(self) -> None:
        """Test metadata summary generation with missing data."""
        metadata = {
            "basic_info": {},
            "video_stream": {},
            "audio_stream": {},
            "file_info": {},
        }

        summary = self.extractor.get_summary(metadata)

        assert summary["filename"] == "Unknown"
        assert summary["file_size"] == 0
        assert summary["duration"] == "Unknown"
        assert summary["resolution"] == "Unknown"
        assert summary["fps"] == "Unknown"
        assert summary["has_audio"] is False
        assert summary["format"] == "Unknown"

    @patch("nvr_analysis.metadata_extractor.MOVIEPY_AVAILABLE", False)
    def test_extract_metadata_no_moviepy(self, tmp_path: Path) -> None:
        """Test metadata extraction when MoviePy is not available."""
        # Create a dummy video file
        video_file = tmp_path / "test_video.mp4"
        video_file.write_text("dummy video content")

        results = self.extractor.extract_metadata(str(video_file))

        assert results["video_path"] == str(video_file)
        assert "basic_info" in results
        assert "video_stream" in results
        assert "audio_stream" in results
        assert "file_info" in results
        assert "errors" in results

        # Video stream should have error when MoviePy is not available
        assert "error" in results["video_stream"]
        assert results["video_stream"]["error"] == "MoviePy not available"
