# LaView NVR Video Downloader

A Python package specifically designed for the **LV-T9708MHS** LaView NVR system, available at Menards. This tool automatically downloads video files from the LV-T9708MHS via ISAPI interface. It is based on Hikvision technology and provides a command-line interface for bulk video retrieval.

**⚠️ Important Note**: This tool has only been tested on the LV-T9708MHS model. While it may work with other LaView NVRs that use the ISAPI interface, compatibility is not guaranteed.

## Features

- **Multi-camera support**: Download from specific camera channels
- **Flexible time ranges**: Specify custom date/time intervals for video retrieval
- **Authentication support**: HTTP Basic and Digest authentication
- **Automatic timezone handling**: UTC time conversion and camera timezone detection
- **Bulk download**: Efficiently download multiple video files in a single operation
- **Logging**: Comprehensive logging with configurable log levels
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/laview-nvr-video-downloader.git
cd laview-nvr-video-downloader

# Install the package
pip install -e .
```

### Install dependencies only

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Set your LaView NVR credentials as environment variables:

```bash
export LAVIEW_NVR_USER="admin"
export LAVIEW_NVR_PASS="your_password"
```

Or set them inline when running commands:

```bash
LAVIEW_NVR_USER=admin LAVIEW_NVR_PASS=your_password python -m laview_dl.cli [options]
```

### Authentication Types

The tool automatically detects and uses the appropriate authentication method:
- **HTTP Basic Authentication**: Standard username/password
- **HTTP Digest Authentication**: More secure authentication method
- **Unauthorized**: Invalid credentials or unsupported auth method

## Usage

### Basic Command Format

```bash
python -m laview_dl.cli [--camera CAMERA] CAM_IP START_DATE START_TIME [END_DATE] [END_TIME]
```

### Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `--camera CAMERA` | Camera channel number | No | 1 |
| `CAM_IP` | Camera/NVR IP address | Yes | - |
| `START_DATE` | Start date (YYYY-MM-DD) | Yes | - |
| `START_TIME` | Start time (HH:MM:SS) | Yes | - |
| `END_DATE` | End date (YYYY-MM-DD) | No | Today |
| `END_TIME` | End time (HH:MM:SS) | No | Current time |

### Examples

#### Download from default camera (channel 1)
```bash
python -m laview_dl.cli 192.168.1.100 2024-04-12 00:00:00 2024-04-12 04:00:00
```

#### Download from specific camera channel
```bash
python -m laview_dl.cli --camera 2 192.168.1.100 2024-04-12 00:00:00 2024-04-12 04:00:00
```

#### Download with custom credentials
```bash
LAVIEW_NVR_USER=admin LAVIEW_NVR_PASS=qwert123 python -m laview_dl.cli --camera 3 192.168.1.100 2024-04-12 00:00:00
```

#### Download until current time (end time not specified)
```bash
python -m laview_dl.cli --camera 1 192.168.1.100 2024-04-12 00:00:00
```

#### Download for entire day
```bash
python -m laview_dl.cli --camera 1 192.168.1.100 2024-04-12 00:00:00 2024-04-12 23:59:59
```

## Important Notes

### Time Handling
- **UTC Time**: The DVR expects time to be in UTC format
- **Local Time**: Enter your local time for the desired video period
- **Automatic Conversion**: The tool automatically converts local time to UTC
- **Timezone Detection**: Camera timezone is automatically detected for accurate time conversion

### Camera Selection
- Camera selection is done via the `--camera` command line argument
- Channel numbers typically start from 1
- Default camera is channel 1 if not specified

## Troubleshooting

### Common Issues

#### Connection Errors
```
Connection error: [Errno 111] Connection refused
```
- Verify the camera IP address is correct
- Check if the camera is accessible from your network
- Ensure port 80 (HTTP) is open

#### Authentication Errors
```
Unauthorised! Check login and password
```
- Verify your username and password
- Check if the user has appropriate permissions
- Ensure the credentials are set in environment variables

#### Camera Not Found
```
Error 500 4: Camera not found
```
- Verify the camera channel number exists
- Check if the camera is online and accessible
- Try different channel numbers

### Debug Mode

Enable verbose logging by setting the log level:

```bash
export LAVIEW_LOG_LEVEL=DEBUG
python -m laview_dl.cli [options]
```

## Supported Devices

This tool has been **specifically designed and tested** for:
- **[LV-T9708MHS](https://support.laviewsecurity.com/hc/en-us/sections/115004123387-LV-T9708MHS)** - Available at Menards

**⚠️ Compatibility Notice**: This tool has only been tested on the LV-T9708MHS model. While it may work with other LaView NVRs that use the ISAPI interface, compatibility is not guaranteed. If you're using a different model, please test thoroughly and report any issues.

## Development

### Project Structure

```
laview-nvr-video-downloader/
├── laview_dl/           # Main package
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── camerasdk.py    # Camera SDK implementation
│   ├── work.py         # Main work logic
│   ├── authtype.py     # Authentication types
│   ├── logging.py      # Logging configuration
│   ├── time_interval.py # Time handling utilities
│   ├── track.py        # Video track management
│   └── utils.py        # Utility functions
├── tests/              # Test suite
├── requirements.txt    # Python dependencies
├── setup.py           # Package configuration
└── README.md          # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Forked from [hikvision-downloader](https://github.com/qb60/hikvision-downloader) for HikVision Cameras
- Based on ISAPI protocol implementation
- Community contributions and testing

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and questions:
- Check the troubleshooting section above
- Review existing GitHub issues
- Create a new issue with detailed information about your problem
- Include device model, error messages, and steps to reproduce
