"""
Tests for the CLI module.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from nvr_analysis.cli import (
    parse_parameters,
    print_json,
    print_summary,
    print_verbose,
    save_results_to_file,
    validate_video_files,
)


class TestCLI:
    """Test cases for CLI module."""

    def test_parse_parameters_help(self) -> None:
        """Test parameter parsing with help request."""
        with patch.object(sys, "argv", ["nvr-analysis"]):
            result = parse_parameters()
            assert result is None

    def test_parse_parameters_basic(self) -> None:
        """Test basic parameter parsing."""
        with patch.object(sys, "argv", ["nvr-analysis", "video.mp4"]):
            args = parse_parameters()
            assert args is not None
            assert args.video_files == ["video.mp4"]
            assert not args.timestamps_only
            assert not args.metadata_only
            assert not args.full_analysis
            assert not args.ai_analysis
            assert not args.json
            assert not args.summary
            assert not args.verbose
            assert not args.no_ocr
            assert args.output_file is None

    def test_parse_parameters_timestamps_only(self) -> None:
        """Test parameter parsing with timestamps-only flag."""
        with patch.object(sys, "argv", ["nvr-analysis", "--timestamps-only", "video.mp4"]):
            args = parse_parameters()
            assert args is not None
            assert args.timestamps_only is True
            assert args.video_files == ["video.mp4"]

    def test_parse_parameters_metadata_only(self) -> None:
        """Test parameter parsing with metadata-only flag."""
        with patch.object(sys, "argv", ["nvr-analysis", "--metadata-only", "video.mp4"]):
            args = parse_parameters()
            assert args is not None
            assert args.metadata_only is True
            assert args.video_files == ["video.mp4"]

    def test_parse_parameters_json_output(self) -> None:
        """Test parameter parsing with JSON output flag."""
        with patch.object(sys, "argv", ["nvr-analysis", "--json", "video.mp4"]):
            args = parse_parameters()
            assert args is not None
            assert args.json is True
            assert args.video_files == ["video.mp4"]

    def test_parse_parameters_verbose_output(self) -> None:
        """Test parameter parsing with verbose output flag."""
        with patch.object(sys, "argv", ["nvr-analysis", "--verbose", "video.mp4"]):
            args = parse_parameters()
            assert args is not None
            assert args.verbose is True
            assert args.video_files == ["video.mp4"]

    def test_parse_parameters_multiple_files(self) -> None:
        """Test parameter parsing with multiple video files."""
        with patch.object(sys, "argv", ["nvr-analysis", "video1.mp4", "video2.mp4", "video3.mp4"]):
            args = parse_parameters()
            assert args is not None
            assert args.video_files == ["video1.mp4", "video2.mp4", "video3.mp4"]

    def test_validate_video_files_single(self, tmp_path: Path) -> None:
        """Test video file validation with single file."""
        # Create a dummy video file
        video_file = tmp_path / "test_video.mp4"
        video_file.write_text("dummy content")

        validated_files = validate_video_files([str(video_file)])

        assert len(validated_files) == 1
        assert validated_files[0] == video_file

    def test_validate_video_files_multiple(self, tmp_path: Path) -> None:
        """Test video file validation with multiple files."""
        # Create dummy video files
        video_file1 = tmp_path / "test_video1.mp4"
        video_file1.write_text("dummy content 1")
        video_file2 = tmp_path / "test_video2.mp4"
        video_file2.write_text("dummy content 2")

        validated_files = validate_video_files([str(video_file1), str(video_file2)])

        assert len(validated_files) == 2
        assert video_file1 in validated_files
        assert video_file2 in validated_files

    def test_validate_video_files_not_found(self) -> None:
        """Test video file validation with non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_video_files(["nonexistent_video.mp4"])

    def test_validate_video_files_not_file(self, tmp_path: Path) -> None:
        """Test video file validation with directory instead of file."""
        # Create a directory
        video_dir = tmp_path / "video_dir"
        video_dir.mkdir()

        with pytest.raises(ValueError, match="Path is not a file"):
            validate_video_files([str(video_dir)])

    def test_validate_video_files_warning_unknown_extension(self, tmp_path: Path) -> None:
        """Test video file validation with unknown extension."""
        # Create a file with unknown extension
        video_file = tmp_path / "test_video.xyz"
        video_file.write_text("dummy content")

        # Should not raise an exception, but should print a warning
        validated_files = validate_video_files([str(video_file)])

        assert len(validated_files) == 1
        assert validated_files[0] == video_file

    def test_print_summary(self) -> None:
        """Test summary output printing."""
        results = {
            "file_info": {
                "size_mb": 45.2,
                "created_time": "2024-01-15T10:30:00",
                "modified_time": "2024-01-15T10:35:00",
            },
            "timestamps": {
                "best_estimate": "2024-01-15T10:30:00",
                "confidence": "high",
            },
            "metadata": {
                "video_stream": {
                    "duration_formatted": "2m 30s",
                    "resolution": "1920x1080",
                    "fps": 30.0,
                },
                "audio_stream": {
                    "has_audio": True,
                },
            },
            "errors": ["Test error"],
        }

        video_path = Path("test_video.mp4")

        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_summary(results, video_path)
            output = mock_stdout.getvalue()

        # Check that key information is present
        assert "test_video.mp4" in output
        assert "45.2 MB" in output
        assert "2024-01-15T10:30:00" in output
        assert "high" in output
        assert "2m 30s" in output
        assert "1920x1080" in output
        assert "30.0 fps" in output
        assert "Yes" in output
        assert "Test error" in output

    def test_print_json(self) -> None:
        """Test JSON output printing."""
        results = {
            "test_key": "test_value",
            "nested": {"key": "value"},
        }

        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_json(results)
            output = mock_stdout.getvalue()

        # Check that output is valid JSON
        import json
        parsed = json.loads(output)
        assert parsed["test_key"] == "test_value"
        assert parsed["nested"]["key"] == "value"

    def test_print_verbose(self) -> None:
        """Test verbose output printing."""
        results = {
            "file_info": {
                "size_mb": 45.2,
            },
            "timestamps": {
                "best_estimate": "2024-01-15T10:30:00",
            },
            "errors": ["Test error"],
        }

        video_path = Path("test_video.mp4")

        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_verbose(results, video_path)
            output = mock_stdout.getvalue()

        # Check that verbose information is present
        assert "test_video.mp4" in output
        assert "FILE INFO" in output
        assert "TIMESTAMPS" in output
        assert "ERRORS" in output
        assert "45.2" in output
        assert "2024-01-15T10:30:00" in output
        assert "Test error" in output

    def test_save_results_to_file(self, tmp_path: Path) -> None:
        """Test saving results to file."""
        results = {
            "test_key": "test_value",
            "nested": {"key": "value"},
        }

        output_file = tmp_path / "results.json"

        save_results_to_file(results, str(output_file))

        # Check that file was created and contains correct data
        assert output_file.exists()

        import json
        with open(output_file) as f:
            saved_results = json.load(f)

        assert saved_results["test_key"] == "test_value"
        assert saved_results["nested"]["key"] == "value"

    def test_save_results_to_file_error(self) -> None:
        """Test saving results to file with error."""
        results = {"test": "data"}

        # Try to save to a directory (should fail)
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            save_results_to_file(results, "/tmp")  # Directory, not file
            output = mock_stdout.getvalue()

        assert "Error saving results to file" in output
