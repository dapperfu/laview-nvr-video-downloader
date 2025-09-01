# NVR Analysis Tool

A Python package for analyzing video files from NVR systems, extracting metadata, timestamps, and performing AI-powered analysis including face recognition and object detection.

## Features

### Current Features
- **Timestamp Extraction**: Extract date and time information from video files using multiple methods:
  - Filename pattern matching
  - File metadata extraction
  - OCR from video frames (when enabled)
- **Metadata Extraction**: Extract comprehensive technical metadata:
  - Video codec information
  - Audio codec information
  - Resolution and frame rate
  - Duration and bitrate
  - File format details

### Planned AI Features
- **Face Recognition**: Detect and recognize faces in video frames
- **Object Detection**: Identify objects and people in video content
- **Motion Analysis**: Detect and analyze motion patterns
- **Person Tracking**: Track individuals across video frames

## Installation

### Prerequisites

The tool requires several system dependencies:

#### Ubuntu/Debian
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
```

#### macOS
```bash
# Install system dependencies using Homebrew
brew install tesseract
```

#### Windows
Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki

### Python Installation

#### From Source
```bash
# Clone the repository
git clone <repository-url>
cd nvr-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

#### Using pip
```bash
pip install nvr-analysis
```

## Usage

### Command Line Interface

The tool provides a comprehensive CLI for video analysis:

```bash
# Basic analysis with summary output
nvr-analysis video.mp4

# Extract only timestamps
nvr-analysis --timestamps-only video.mp4

# Extract only metadata
nvr-analysis --metadata-only video.mp4

# Full analysis with JSON output
nvr-analysis --full-analysis --json video.mp4

# Verbose output
nvr-analysis --verbose video.mp4

# Analyze multiple files
nvr-analysis video1.mp4 video2.mp4 video3.mp4

# Disable OCR for timestamp extraction
nvr-analysis --no-ocr video.mp4

# Save results to file
nvr-analysis --output-file results.json video.mp4
```

### Python API

You can also use the tool programmatically:

```python
from nvr_analysis import VideoAnalyzer

# Initialize analyzer
analyzer = VideoAnalyzer(enable_ocr=True, enable_ai=False)

# Analyze a video file
results = analyzer.analyze_video("video.mp4")

# Extract only timestamps
timestamp_results = analyzer.extract_timestamps_only("video.mp4")

# Extract only metadata
metadata_results = analyzer.extract_metadata_only("video.mp4")

# Print results
print(f"Timestamp: {results['timestamps']['best_estimate']}")
print(f"Duration: {results['metadata']['video_stream']['duration_formatted']}")
print(f"Resolution: {results['metadata']['video_stream']['resolution']}")
```

## Supported Video Formats

The tool supports the following video formats:
- MP4 (MPEG-4 Part 14)
- AVI (Audio Video Interleave)
- MKV (Matroska)
- MOV (QuickTime File Format)
- WMV (Windows Media Video)
- FLV (Flash Video)
- WebM (WebM multimedia container)
- M4V (Apple MPEG-4 video container)

## Timestamp Extraction Methods

The tool uses multiple methods to extract timestamps from videos:

1. **Filename Parsing**: Extracts timestamps from common filename patterns:
   - `YYYY-MM-DD HH:MM:SS`
   - `YYYYMMDD_HHMMSS`
   - `MM-DD-YYYY HH:MM:SS`
   - `DD-MM-YYYY HH:MM:SS`
   - `YYYY_MM_DD_HH_MM_SS`

2. **File Metadata**: Uses file modification time as a fallback

3. **OCR from Frames**: Extracts timestamps from video frames using OCR (requires Tesseract)

## Output Formats

### Summary Output (Default)
```
============================================================
Analysis Results: video.mp4
============================================================
File Size: 45.2 MB
Created: 2024-01-15T10:30:00
Modified: 2024-01-15T10:35:00
Timestamp: 2024-01-15T10:30:00 (confidence: high)
Duration: 2m 30s
Resolution: 1920x1080
Frame Rate: 30.0 fps
Audio: Yes
```

### JSON Output
```json
{
  "video_path": "video.mp4",
  "analysis_timestamp": "2024-01-15T10:35:00",
  "file_info": {
    "filename": "video.mp4",
    "size_bytes": 47345664,
    "size_mb": 45.2,
    "created_time": "2024-01-15T10:30:00",
    "modified_time": "2024-01-15T10:35:00"
  },
  "timestamps": {
    "filename_timestamp": "2024-01-15T10:30:00",
    "metadata_timestamp": "2024-01-15T10:35:00",
    "best_estimate": "2024-01-15T10:30:00",
    "confidence": "high",
    "methods_used": ["filename_parsing", "file_metadata"]
  },
  "metadata": {
    "video_stream": {
      "duration_seconds": 150.0,
      "duration_formatted": "2m 30s",
      "fps": 30.0,
      "width": 1920,
      "height": 1080,
      "resolution": "1920x1080",
      "aspect_ratio": 1.78,
      "bitrate_kbps": 2524.8,
      "bitrate_mbps": 2.52
    },
    "audio_stream": {
      "has_audio": true,
      "audio_fps": 44100,
      "audio_nchannels": 2
    }
  }
}
```

## Configuration

### OCR Configuration

The tool uses Tesseract OCR for timestamp extraction from video frames. You can:

- Disable OCR: `--no-ocr` flag
- Install additional language packs for better recognition
- Configure Tesseract settings in your system

### AI Features Configuration

Future AI features will be configurable through:

```python
# Enable AI features
analyzer = VideoAnalyzer(enable_ai=True)

# Configure specific AI models
analyzer.configure_ai(
    face_recognition=True,
    object_detection=True,
    motion_analysis=True
)
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd nvr-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt[dev]

# Install in development mode
pip install -e .

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=nvr_analysis

# Run specific test file
pytest tests/test_video_analyzer.py
```

### Code Quality

```bash
# Format code
black nvr_analysis/

# Lint code
ruff check nvr_analysis/

# Type checking
mypy nvr_analysis/
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Commit your changes: `git commit -am 'Add new feature'`
7. Push to the branch: `git push origin feature/new-feature`
8. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [MoviePy](https://zulko.github.io/moviepy/) for video processing
- [OpenCV](https://opencv.org/) for computer vision capabilities
- [Tesseract](https://github.com/tesseract-ocr/tesseract) for OCR functionality
- [Pillow](https://python-pillow.org/) for image processing

## Roadmap

### Version 0.2.0
- [ ] Face recognition capabilities
- [ ] Basic object detection
- [ ] Motion analysis
- [ ] Person tracking

### Version 0.3.0
- [ ] Advanced AI models integration
- [ ] Batch processing capabilities
- [ ] Web interface
- [ ] Database integration for analysis results

### Version 1.0.0
- [ ] Production-ready AI features
- [ ] Comprehensive documentation
- [ ] Performance optimizations
- [ ] Enterprise features
