#!/usr/bin/env python3
"""
Example usage of the NVR Analysis Tool

This script demonstrates how to use the nvr-analysis tool programmatically
to analyze video files and extract timestamps and metadata.
"""

import sys
from pathlib import Path

from nvr_analysis import VideoAnalyzer


def main() -> None:
    """Main example function."""
    print("NVR Analysis Tool - Example Usage")
    print("=" * 50)

    # Initialize the analyzer
    print("Initializing video analyzer...")
    analyzer = VideoAnalyzer(enable_ocr=True, enable_ai=False)

    # Example video file path (replace with actual video file)
    video_file = "example_video.mp4"

    # Check if the video file exists
    if not Path(video_file).exists():
        print(f"Error: Video file '{video_file}' not found.")
        print("Please provide a valid video file path.")
        print("\nExample usage:")
        print("  python example_usage.py path/to/your/video.mp4")
        sys.exit(1)

    print(f"Analyzing video file: {video_file}")
    print("-" * 50)

    try:
        # Perform full analysis
        print("Performing full analysis...")
        results = analyzer.analyze_video(video_file)

        # Display results
        print("\n📋 ANALYSIS RESULTS:")
        print("=" * 50)

        # File information
        if "file_info" in results:
            file_info = results["file_info"]
            print(f"📁 File: {file_info.get('filename', 'Unknown')}")
            print(f"📏 Size: {file_info.get('size_mb', 'Unknown')} MB")
            print(f"📅 Created: {file_info.get('created_time', 'Unknown')}")
            print(f"📅 Modified: {file_info.get('modified_time', 'Unknown')}")

        # Timestamp information
        if "timestamps" in results:
            timestamps = results["timestamps"]
            print("\n🕐 TIMESTAMP ANALYSIS:")
            if timestamps.get("best_estimate"):
                print(f"   Best Estimate: {timestamps['best_estimate']}")
                print(f"   Confidence: {timestamps['confidence']}")
                print(f"   Methods Used: {', '.join(timestamps.get('methods_used', []))}")
            else:
                print("   No timestamp found")

        # Metadata information
        if "metadata" in results:
            metadata = results["metadata"]
            print("\n🎬 VIDEO METADATA:")

            if "video_stream" in metadata:
                video_info = metadata["video_stream"]
                if "error" not in video_info:
                    print(f"   Duration: {video_info.get('duration_formatted', 'Unknown')}")
                    print(f"   Resolution: {video_info.get('resolution', 'Unknown')}")
                    print(f"   Frame Rate: {video_info.get('fps', 'Unknown')} fps")
                    print(f"   Bitrate: {video_info.get('bitrate_mbps', 'Unknown')} Mbps")
                else:
                    print(f"   Error: {video_info['error']}")

            if "audio_stream" in metadata:
                audio_info = metadata["audio_stream"]
                print(f"   Audio: {'Yes' if audio_info.get('has_audio') else 'No'}")

        # File format information
        if "metadata" in results and "file_info" in results["metadata"]:
            file_info = results["metadata"]["file_info"]
            print(f"   Format: {file_info.get('format', 'Unknown')}")
            print(f"   Container: {file_info.get('container', 'Unknown')}")

        # Errors
        if results.get("errors"):
            print(f"\n❌ ERRORS ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"   - {error}")

        # Example of extracting only timestamps
        print("\n🕐 TIMESTAMP-ONLY EXTRACTION:")
        print("-" * 30)
        timestamp_results = analyzer.extract_timestamps_only(video_file)
        if timestamp_results.get("best_estimate"):
            print(f"   Timestamp: {timestamp_results['best_estimate']}")
            print(f"   Confidence: {timestamp_results['confidence']}")
        else:
            print("   No timestamp found")

        # Example of extracting only metadata
        print("\n🎬 METADATA-ONLY EXTRACTION:")
        print("-" * 30)
        metadata_results = analyzer.extract_metadata_only(video_file)
        if "video_stream" in metadata_results:
            video_info = metadata_results["video_stream"]
            if "error" not in video_info:
                print(f"   Duration: {video_info.get('duration_formatted', 'Unknown')}")
                print(f"   Resolution: {video_info.get('resolution', 'Unknown')}")
            else:
                print(f"   Error: {video_info['error']}")

        print("\n✅ Analysis completed successfully!")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if video file path is provided as command line argument
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
        # Update the video_file variable in the main function
        import nvr_analysis.example_usage
        nvr_analysis.example_usage.video_file = video_file

    main()
