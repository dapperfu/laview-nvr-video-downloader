# LaView NVR Video Downloader

A Python package specifically designed for the **LV-T9708MHS** LaView NVR system, available at Menards. This tool automatically downloads video files from the LV-T9708MHS via ISAPI interface. It is based on Hikvision technology and provides a command-line interface for bulk video retrieval.

**⚠️ Important Note**: This tool has only been tested on the LV-T9708MHS model. While it may work with other LaView NVRs that use the ISAPI interface, compatibility is not guaranteed.

## Features

- **Multi-camera support**: Download from specific camera channels
- **Flexible time ranges**: Specify custom date/time intervals for video retrieval
- **Natural language date parsing**: Support for "today", "yesterday", "now", "2 days ago", etc.
- **Multiple date formats**: Support for "August 30, 2025", "08/30/2025", "2025-08-30", etc.
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

### Quick Setup (Recommended)

Use the interactive setup command to configure your devices:

```bash
python -m laview_dl.cli --setup
```

This will prompt you for:
- Device name (e.g., "office-nvr", "home-camera")
- IP address
- Username and password (optional, can use environment variables)
- Camera channel number
- Timeout settings

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

### Device Management

List configured devices:
```bash
python -m laview_dl.cli --list-devices
```

Remove a device:
```bash
python -m laview_dl.cli --remove-device
```

### Configuration Storage

Device configurations are stored in:
- **Linux/macOS**: `~/.config/laview-nvr-video-downloader/devices.json`
- **Windows**: `%APPDATA%\laview-nvr-video-downloader\devices.json`

The configuration file contains:
- Device names and IP addresses
- Camera channel numbers
- Timeout settings
- Username/password (if provided during setup)

**Security Note**: Credentials are stored in plain text. Consider using environment variables for sensitive information.

### Authentication Types

The tool automatically detects and uses the appropriate authentication method:
- **HTTP Basic Authentication**: Standard username/password
- **HTTP Digest Authentication**: More secure authentication method
- **Unauthorized**: Invalid credentials or unsupported auth method

## Usage

### Setup Commands

```bash
# Configure a new device
python -m laview_dl.cli --setup

# List configured devices
python -m laview_dl.cli --list-devices

# Remove a device
python -m laview_dl.cli --remove-device
```

### Device-Based Commands (Recommended)

```bash
python -m laview_dl.cli --device DEVICE_NAME START_DATE START_TIME [END_DATE] [END_TIME]
```

### Legacy Commands (Direct IP)

```bash
python -m laview_dl.cli [--camera CAMERA] CAM_IP START_DATE START_TIME [END_DATE] [END_TIME]
```

### Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `--setup` | Configure a new device | No | - |
| `--list-devices` | List all configured devices | No | - |
| `--remove-device` | Remove a configured device | No | - |
| `--device DEVICE_NAME` | Use a configured device by name | No | - |
| `--camera CAMERA` | Camera channel number (legacy mode) | No | 1 |
| `CAM_IP` | Camera/NVR IP address (legacy mode) | Yes* | - |
| `START_DATE` | Start date (YYYY-MM-DD) | Yes | - |
| `START_TIME` | Start time (HH:MM:SS) | Yes | - |
| `END_DATE` | End date (YYYY-MM-DD) | No | Today |
| `END_TIME` | End time (HH:MM:SS) | No | Current time |

*Required when not using `--device`

### Examples

#### Using configured devices (recommended)
```bash
# Download from a configured device with flexible date formats
python -m laview_dl.cli --device office-nvr "August 30, 2025" "08:00 AM" "August 31, 2025" "08:00 AM"
python -m laview_dl.cli --device home-camera today "06:00 AM" tomorrow "06:00 AM"
python -m laview_dl.cli --device shop-nvr yesterday "08:00 AM" now

# Download from a configured device (legacy format)
python -m laview_dl.cli --device office-nvr 2024-04-12 00:00:00 2024-04-12 04:00:00

# Download from a configured device (until current time)
python -m laview_dl.cli --device home-camera 2024-04-12 00:00:00
```

#### Legacy mode - direct IP address
```bash
# Download from default camera (channel 1)
python -m laview_dl.cli 192.168.1.100 2024-04-12 00:00:00 2024-04-12 04:00:00

# Download from specific camera channel
python -m laview_dl.cli --camera 2 192.168.1.100 2024-04-12 00:00:00 2024-04-12 04:00:00

# Download with custom credentials
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

## Flexible Date/Time Parsing

The tool supports a wide variety of date and time formats to make it user-friendly for non-technical users:

### Natural Language
```bash
# Relative dates
today, yesterday, tomorrow
now
2 days ago, 3 weeks ago
next week, last month, this year
```

### Formatted Dates
```bash
# Full month names
"August 30, 2025", "Aug 30, 2025"
"30 August 2025", "30 Aug 2025"

# Numeric formats
"2025-08-30", "08/30/2025", "30/08/2025"
```

### Time Formats
```bash
# 24-hour format
"08:00:00", "08:00"

# 12-hour format with AM/PM
"08:00 AM", "08:00:00 AM"
"2:30 PM", "14:30"
```

### Examples
```bash
# Natural language
python -m laview_dl.cli --device camera today "06:00 AM" now
python -m laview_dl.cli --device camera yesterday "08:00 AM" today "08:00 AM"

# Formatted dates
python -m laview_dl.cli --device camera "August 30, 2025" "08:00 AM" "August 31, 2025" "08:00 AM"
python -m laview_dl.cli --device camera "08/30/2025" "08:00" "08/31/2025" "08:00"

# Mixed formats
python -m laview_dl.cli --device camera "August 30, 2025" "08:00 AM" tomorrow "06:00 PM"
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
│   ├── config.py       # Configuration management
│   ├── date_parser.py  # Flexible date/time parsing
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
