"""
NVR Analysis CLI

Command-line interface for the NVR Analysis tool that provides video analysis
capabilities including timestamp extraction, metadata extraction, and future AI features.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from .video_analyzer import VideoAnalyzer


def setup_logging(verbose: int = 0) -> None:
    """
    Setup logging configuration based on verbosity level.
    
    Args:
        verbose: Verbosity level (0-3)
    """
    log_levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.DEBUG,
    }

    logging.basicConfig(
        level=log_levels.get(verbose, logging.DEBUG),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_parameters() -> Optional[argparse.Namespace]:
    """
    Parse command line parameters.
    
    Returns:
        Parsed arguments or None if help was requested
    """
    usage = """
  %(prog)s [OPTIONS] VIDEO_FILE
  
  Analyze video files to extract timestamps, metadata, and perform AI-powered analysis.
  
  Analysis Types:
    --timestamps-only    Extract only timestamp information
    --metadata-only      Extract only metadata information
    --full-analysis      Perform complete analysis (default)
    --ai-analysis        Enable AI-powered features (future)
  
  Output Formats:
    --json               Output results in JSON format
    --summary            Output results in summary format (default)
    --verbose            Output detailed information
  """

    epilog = """
Examples:
  # Basic analysis with summary output
  python %(prog)s video.mp4
  
  # Extract only timestamps
  python %(prog)s --timestamps-only video.mp4
  
  # Extract only metadata
  python %(prog)s --metadata-only video.mp4
  
  # Full analysis with JSON output
  python %(prog)s --full-analysis --json video.mp4
  
  # Verbose output
  python %(prog)s --verbose video.mp4
  
  # Analyze multiple files
  python %(prog)s video1.mp4 video2.mp4 video3.mp4
  """

    parser = argparse.ArgumentParser(
        usage=usage,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Video file argument
    parser.add_argument(
        "video_files",
        nargs="+",
        help="Video file(s) to analyze",
    )

    # Analysis type options
    analysis_group = parser.add_mutually_exclusive_group()
    analysis_group.add_argument(
        "--timestamps-only",
        action="store_true",
        help="Extract only timestamp information",
    )
    analysis_group.add_argument(
        "--metadata-only",
        action="store_true",
        help="Extract only metadata information",
    )
    analysis_group.add_argument(
        "--full-analysis",
        action="store_true",
        help="Perform complete analysis (default)",
    )
    analysis_group.add_argument(
        "--ai-analysis",
        action="store_true",
        help="Enable AI-powered features (future)",
    )

    # Output format options
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    output_group.add_argument(
        "--summary",
        action="store_true",
        help="Output results in summary format (default)",
    )
    output_group.add_argument(
        "--verbose",
        action="store_true",
        help="Output detailed information",
    )

    # Additional options
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable OCR for timestamp extraction",
    )
    parser.add_argument(
        "--output-file",
        help="Save results to specified file",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        return None
    args = parser.parse_args()
    return args


def validate_video_files(video_files: list[str]) -> list[Path]:
    """
    Validate that video files exist and are accessible.
    
    Args:
        video_files: List of video file paths
        
    Returns:
        List of validated Path objects
        
    Raises:
        FileNotFoundError: If any video file is not found
    """
    validated_files = []

    for video_file in video_files:
        video_path = Path(video_file)

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not video_path.is_file():
            raise ValueError(f"Path is not a file: {video_path}")

        # Check if it's a video file (basic extension check)
        video_extensions = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
        if video_path.suffix.lower() not in video_extensions:
            print(f"Warning: File may not be a video file: {video_path}")

        validated_files.append(video_path)

    return validated_files


def print_summary(results: dict, video_path: Path) -> None:
    """
    Print analysis results in summary format.
    
    Args:
        results: Analysis results dictionary
        video_path: Path to the analyzed video file
    """
    print(f"\n{'='*60}")
    print(f"Analysis Results: {video_path.name}")
    print(f"{'='*60}")

    # File information
    if "file_info" in results:
        file_info = results["file_info"]
        print(f"File Size: {file_info.get('size_mb', 'Unknown')} MB")
        print(f"Created: {file_info.get('created_time', 'Unknown')}")
        print(f"Modified: {file_info.get('modified_time', 'Unknown')}")

    # Timestamp information
    if "timestamps" in results:
        timestamps = results["timestamps"]
        if timestamps.get("best_estimate"):
            print(f"Timestamp: {timestamps['best_estimate']} (confidence: {timestamps['confidence']})")
        else:
            print("Timestamp: Not found")

    # Metadata summary
    if "metadata" in results:
        metadata = results["metadata"]
        if "video_stream" in metadata and "error" not in metadata["video_stream"]:
            video_info = metadata["video_stream"]
            print(f"Duration: {video_info.get('duration_formatted', 'Unknown')}")
            print(f"Resolution: {video_info.get('resolution', 'Unknown')}")
            print(f"Frame Rate: {video_info.get('fps', 'Unknown')} fps")

        if "audio_stream" in metadata:
            audio_info = metadata["audio_stream"]
            print(f"Audio: {'Yes' if audio_info.get('has_audio') else 'No'}")

    # Errors
    if results.get("errors"):
        print(f"\nErrors: {len(results['errors'])}")
        for error in results["errors"]:
            print(f"  - {error}")


def print_json(results: dict) -> None:
    """
    Print analysis results in JSON format.
    
    Args:
        results: Analysis results dictionary
    """
    print(json.dumps(results, indent=2, default=str))


def print_verbose(results: dict, video_path: Path) -> None:
    """
    Print analysis results in verbose format.
    
    Args:
        results: Analysis results dictionary
        video_path: Path to the analyzed video file
    """
    print(f"\n{'='*80}")
    print(f"Detailed Analysis Results: {video_path.name}")
    print(f"{'='*80}")

    # Print all sections
    for section, data in results.items():
        if section == "errors" and data:
            print(f"\n❌ ERRORS ({len(data)}):")
            for error in data:
                print(f"  - {error}")
        elif section != "errors":
            print(f"\n📋 {section.upper().replace('_', ' ')}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for sub_key, sub_value in value.items():
                            print(f"    {sub_key}: {sub_value}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  {data}")


def save_results_to_file(results: dict, output_file: str) -> None:
    """
    Save analysis results to a file.
    
    Args:
        results: Analysis results dictionary
        output_file: Path to output file
    """
    try:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving results to file: {e}")


def main() -> None:
    """Main CLI entry point."""
    try:
        # Parse command line arguments
        args = parse_parameters()
        if not args:
            return

        # Setup logging
        verbose_level = 2 if args.verbose else 1
        setup_logging(verbose_level)

        # Validate video files
        try:
            video_files = validate_video_files(args.video_files)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Determine analysis type
        if args.timestamps_only:
            analysis_type = "timestamps"
        elif args.metadata_only:
            analysis_type = "metadata"
        elif args.ai_analysis:
            analysis_type = "ai"
        else:
            analysis_type = "full"

        # Determine output format
        if args.json:
            output_format = "json"
        elif args.verbose:
            output_format = "verbose"
        else:
            output_format = "summary"

        # Initialize analyzer
        enable_ocr = not args.no_ocr
        enable_ai = args.ai_analysis
        analyzer = VideoAnalyzer(enable_ocr=enable_ocr, enable_ai=enable_ai)

        # Process each video file
        all_results = []

        for video_file in video_files:
            print(f"\nAnalyzing: {video_file}")

            try:
                # Perform analysis based on type
                if analysis_type == "timestamps":
                    results = analyzer.extract_timestamps_only(str(video_file))
                elif analysis_type == "metadata":
                    results = analyzer.extract_metadata_only(str(video_file))
                else:
                    results = analyzer.analyze_video(str(video_file))

                # Add video path to results for consistency
                results["video_path"] = str(video_file)
                all_results.append(results)

                # Print results based on format
                if output_format == "json":
                    print_json(results)
                elif output_format == "verbose":
                    print_verbose(results, video_file)
                else:
                    print_summary(results, video_file)

            except Exception as e:
                error_msg = f"Failed to analyze {video_file}: {e}"
                print(f"❌ {error_msg}")
                logging.exception(error_msg)
                continue

        # Save results to file if requested
        if args.output_file and all_results:
            if len(all_results) == 1:
                save_results_to_file(all_results[0], args.output_file)
            else:
                save_results_to_file({"analyses": all_results}, args.output_file)

        # Print summary if multiple files
        if len(video_files) > 1:
            successful = len([r for r in all_results if not r.get("errors")])
            print(f"\n{'='*60}")
            print(f"Summary: {successful}/{len(video_files)} files analyzed successfully")
            print(f"{'='*60}")

    except KeyboardInterrupt:
        print("\n^-C: Analysis interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.error("Unexpected error in main", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
