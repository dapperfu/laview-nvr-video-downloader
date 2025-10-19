# LaView NVR Video Downloader

A Python package specifically designed for the **LV-T9708MHS** LaView NVR system, available at Menards. This tool automatically downloads video files from the LV-T9708MHS via ISAPI interface. It is based on Hikvision technology and provides a command-line interface for bulk video retrieval.

**⚠️ Important Note**: This tool has been **extensively tested** on the LV-T9708MHS model at IP address 192.168.1.100 with cameras 1 and 2. While it may work with other LaView NVRs that use the ISAPI interface, compatibility is not guaranteed.

## 🆕 Recent Major Updates (v2.0)

### ✨ New Features Added

- **🎯 Device Management System**: Configure and manage multiple NVR devices with easy setup
- **🗓️ Flexible Date/Time Parsing**: Support for natural language dates like "today", "yesterday", "2 days ago"
- **📅 Multiple Date Formats**: Accept "August 30, 2025", "08/30/2025", "2025-08-30", etc.
- **⚙️ Interactive Setup**: Use `--setup` command for guided device configuration
- **🔧 Device Commands**: `--list-devices`, `--remove-device` for easy management
- **📁 Persistent Configuration**: Settings stored in `~/.config/laview-nvr-video-downloader/`
- **🕐 Enhanced Time Handling**: Automatic timezone detection and UTC conversion
- **🎨 Modern CLI**: Improved user experience with better error messages and examples

### 🔄 What's Changed from Original

| Feature | Original | Enhanced Version |
|---------|----------|------------------|
| **Date Input** | Only ISO format | Natural language + multiple formats |
| **Device Management** | Manual IP entry | Interactive setup + persistent config |
| **Camera Selection** | `--camera` flag only | Device-based + legacy mode support |
| **Configuration** | Environment variables only | Config files + env vars + interactive |
| **User Experience** | Basic CLI | Rich examples + better error messages |
| **Timezone** | Manual UTC conversion | Automatic detection + conversion |

## Features

- **Multi-camera support**: Download from specific camera channels (tested with cameras 1-2)
- **Flexible time ranges**: Specify custom date/time intervals for video retrieval
- **Natural language date parsing**: Support for "today", "yesterday", "now", "2 days ago", etc.
- **Multiple date formats**: Support for "August 30, 2025", "08/30/2025", "2025-08-30", etc.
- **Authentication support**: HTTP Basic and Digest authentication
- **Automatic timezone handling**: UTC time conversion and camera timezone detection
- **Bulk download**: Efficiently download multiple video files in a single operation
- **Logging**: Comprehensive logging with configurable log levels
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Device management**: Save and manage multiple NVR configurations

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
- **Linux/macOS**: `~/.config/laview-nvr-video-downloader/devices.toml`
- **Windows**: `%APPDATA%\laview-nvr-video-downloader\devices.toml`

The configuration file uses TOML format for better readability and easier manual editing:

```toml
[shop-nvr]
device_name = "shop-nvr"
ip_address = "192.168.1.100"
camera_channel = 1
timeout = 10
username = "admin"
password = "dummy_password123"

[office-camera]
device_name = "office-camera"
ip_address = "192.168.1.101"
camera_channel = 2
timeout = 15
username = "admin"
# password = "use environment variable LAVIEW_NVR_PASS"
```

The configuration file contains:
- Device names and IP addresses
- Camera channel numbers
- Timeout settings
- Username/password (if provided during setup)

**Security Note**: Credentials are stored in plain text. Consider using environment variables for sensitive information.

**Migration**: Existing JSON configurations are automatically migrated to TOML format on first use.

### Authentication Types

The tool automatically detects and uses the appropriate authentication method:
- **HTTP Basic Authentication**: Standard username/password
- **HTTP Digest Authentication**: More secure authentication method
- **Unauthorized**: Invalid credentials or unsupported auth method

## Usage

### Setup Commands

```bash
# Configure a new device
laview-cli --setup

# List configured devices
laview-cli --list-devices

# Remove a device
laview-cli --remove-device
```

### Device-Based Commands (Recommended)

```bash
laview-cli --device DEVICE_NAME START_DATE START_TIME [END_DATE] [END_TIME]
```

### Legacy Commands (Direct IP)

```bash
laview-cli [--camera CAMERA] CAM_IP START_DATE START_TIME [END_DATE] [END_TIME]
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
| `START_DATETIME` | Start datetime | Yes | - |
| `END_DATETIME` | End datetime | No | now |

*Required when not using `--device`

### Examples

#### Using configured devices (recommended)
```bash
# Download from a configured device with flexible date formats
laview-cli --device office-nvr "August 30, 2025 08:00 AM" "August 31, 2025 08:00 AM"
laview-cli --device home-camera "today 06:00 AM" "tomorrow 06:00 AM"
laview-cli --device shop-nvr "yesterday 08:00 AM" "now"
laview-cli --device camera "8 AM yesterday" "6 PM today"

# Download from a configured device (legacy format)
laview-cli --device office-nvr "2024-04-12 00:00:00" "2024-04-12 04:00:00"

# Download from a configured device (until current time)
laview-cli --device home-camera "2024-04-12 00:00:00"
```

#### Legacy mode - direct IP address
```bash
# Download from default camera (channel 1)
laview-cli 192.168.1.100 "2024-04-12 00:00:00" "2024-04-12 04:00:00"

# Download from specific camera channel
laview-cli --camera 2 192.168.1.100 "2024-04-12 00:00:00" "2024-04-12 04:00:00"

# Download with custom credentials
LAVIEW_NVR_USER=admin LAVIEW_NVR_PASS=dummy_password123 laview-cli --camera 3 192.168.1.100 "2024-04-12 00:00:00"
```

#### Download until current time (end time not specified)
```bash
laview-cli --camera 1 192.168.1.100 "2024-04-12 00:00:00"
```

#### Download for entire day
```bash
laview-cli --camera 1 192.168.1.100 "2024-04-12 00:00:00" "2024-04-12 23:59:59"
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
laview-cli --device camera "today 06:00 AM" "now"
laview-cli --device camera "yesterday 08:00 AM" "today 08:00 AM"

# Formatted dates
laview-cli --device camera "August 30, 2025 08:00 AM" "August 31, 2025 08:00 AM"
laview-cli --device camera "08/30/2025 08:00" "08/31/2025 08:00"

# Combined natural language
laview-cli --device camera "8 AM yesterday" "6 PM today"
laview-cli --device camera "yesterday 8 AM" "tomorrow 6 PM"

# Mixed formats
laview-cli --device camera "August 30, 2025 08:00 AM" "tomorrow 06:00 PM"
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
laview-cli [options]
```

## Supported Devices

This tool has been **specifically designed and tested** for:
- **[LV-T9708MHS](https://support.laviewsecurity.com/hc/en-us/sections/115004123387-LV-T9708MHS)** - Available at Menards

### Tested Configuration
- **Model**: LV-T9708MHS
- **IP Address**: 192.168.1.100
- **Cameras**: 1, 2 (successfully tested)
- **Authentication**: HTTP Basic (admin/dummy_password123)
- **Timezone**: EDT (Eastern Daylight Time)
- **Protocol**: ISAPI over HTTP

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

---

## 🎭 A Note on Origins

*"Developed by the Russians, perfected by the AI"* - This tool traces its lineage back to the original [hikvision-downloader](https://github.com/qb60/hikvision-downloader) project by [qb60](https://github.com/qb60), which was created in 2020 for HikVision cameras. While we can't confirm the developer's nationality (GitHub profiles don't always tell the full story), the original project's robust ISAPI implementation provided the foundation for this LaView-specific enhancement.

The AI-powered improvements include:
- Natural language date parsing (because who wants to remember ISO formats?)
- Device management system (because typing IPs repeatedly is so 2020)
- Enhanced error messages (because "it broke" isn't very helpful)
- Comprehensive documentation (because RTFM should be easier)

So whether you're downloading security footage from your Menards-purchased LaView NVR or just curious about the intersection of Russian coding and AI enhancement, this tool should make your video retrieval experience much more pleasant! 🇷🇺🤖
