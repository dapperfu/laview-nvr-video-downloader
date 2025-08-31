import argparse
import sys
from argparse import Namespace
from datetime import datetime
from typing import Optional

from .camerasdk import init
from .work import work
from .config import setup_device, list_configured_devices, remove_device_setup, ConfigManager
from .date_parser import FlexibleDateParser


def parse_parameters() -> Optional[Namespace]:
    usage = """
  %(prog)s [--setup|--list-devices|--remove-device] [-u] [--device DEVICE|--camera CAMERA] [CAM_IP] START_DATE START_TIME [END_DATE END_TIME]
  
  If END_DATE and END_TIME aren't specified use now().

  Use the time setting on the DVR.
  
  Commands:
    --setup              Configure a new device
    --list-devices       List all configured devices
    --remove-device      Remove a configured device
  
  Date/Time Formats Supported:
    - Standard: 2025-08-30 08:00:00, 08/30/2025 08:00 AM
    - Natural: today, yesterday, now, 2 days ago
    - Formatted: August 30, 2025, 08:00 AM
    - Relative: next week, last month, this year
  """

    epilog = """
Examples:
  # Setup a new device
  python %(prog)s --setup
  
  # List configured devices
  python %(prog)s --list-devices
  
  # Remove a device
  python %(prog)s --remove-device
  
  # Use a configured device with flexible date formats
  python %(prog)s --device office-nvr "August 30, 2025" "08:00 AM" "August 31, 2025" "08:00 AM"
  python %(prog)s --device home-camera today "06:00 AM" tomorrow "06:00 AM"
  python %(prog)s --device shop-nvr yesterday "08:00 AM" now
  
  # Use IP address directly (legacy mode)
  python %(prog)s 10.145.17.202 2020-04-15 00:30:00 2020-04-15 10:59:59
  python %(prog)s --camera 2 10.145.17.202 2020-04-15 00:30:00 2020-04-15 10:59:59
  python %(prog)s --camera 3 10.145.17.202 2020-04-15 00:30:00 2020-04-15 10:59:59
  LAVIEW_USER=admin LAVIEW_PASS=qwert123 python %(prog)s --camera 1 10.145.17.202 2020-04-15 00:30:00
  
        """

    parser = argparse.ArgumentParser(
        usage=usage, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Setup commands
    parser.add_argument("--setup", action="store_true", help="Configure a new device")
    parser.add_argument("--list-devices", action="store_true", help="List all configured devices")
    parser.add_argument("--remove-device", action="store_true", help="Remove a configured device")
    
    # Device selection
    parser.add_argument("--device", help="Use a configured device by name")
    
    # Legacy arguments (only used when not using --device)
    parser.add_argument("IP", nargs="?", help="camera's IP address (required when not using --device)")
    parser.add_argument("START_DATE", nargs="?", help="start date of interval (required when not using --device)")
    parser.add_argument("START_TIME", nargs="?", help="start time of interval (required when not using --device)")
    parser.add_argument(
        "END_DATE",
        nargs="?",
        help="end date of interval",
        default=datetime.now().strftime("%Y-%m-%d"),
    )
    parser.add_argument(
        "END_TIME",
        nargs="?",
        help="end time of interval",
        default=datetime.now().strftime("%H:%M:%S"),
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=1,
        help="camera channel number (default: 1, only used when not using --device)",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        return None
    else:
        args = parser.parse_args()
        return args


def validate_legacy_args(args: Namespace) -> bool:
    """Validate that required arguments are provided for legacy mode."""
    if not args.IP or not args.START_DATE or not args.START_TIME:
        print("Error: IP, START_DATE, and START_TIME are required when not using --device")
        return False
    return True


def get_device_config(device_name: str) -> Optional[dict]:
    """Get configuration for a specific device."""
    config_manager = ConfigManager()
    return config_manager.get_device_config(device_name)


def parse_datetime_strings(start_date: str, start_time: str, end_date: str, end_time: str) -> tuple[str, str]:
    """
    Parse date and time strings into datetime strings.
    
    Args:
        start_date: Start date string
        start_time: Start time string
        end_date: End date string
        end_time: End time string
        
    Returns:
        Tuple of (start_datetime_str, end_datetime_str)
    """
    try:
        # Try to parse start date and time
        start_datetime = FlexibleDateParser.parse_date_time_pair(start_date, start_time)
        start_datetime_str = start_datetime.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"Error parsing start date/time: {e}")
        print(f"Start date: '{start_date}', Start time: '{start_time}'")
        print("Supported formats:")
        for fmt in FlexibleDateParser.get_supported_formats()[:5]:  # Show first 5 formats
            print(f"  - {fmt}")
        raise
    
    try:
        # Try to parse end date and time
        end_datetime = FlexibleDateParser.parse_date_time_pair(end_date, end_time)
        end_datetime_str = end_datetime.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"Error parsing end date/time: {e}")
        print(f"End date: '{end_date}', End time: '{end_time}'")
        print("Supported formats:")
        for fmt in FlexibleDateParser.get_supported_formats()[:5]:  # Show first 5 formats
            print(f"  - {fmt}")
        raise
    
    return start_datetime_str, end_datetime_str


def main():
    parameters = parse_parameters()
    if not parameters:
        return
    
    # Handle setup commands
    if parameters.setup:
        setup_device()
        return
    
    if parameters.list_devices:
        list_configured_devices()
        return
    
    if parameters.remove_device:
        remove_device_setup()
        return
    
    # Handle device-based execution
    if parameters.device:
        device_config = get_device_config(parameters.device)
        if not device_config:
            print(f"Error: Device '{parameters.device}' not found.")
            print("Run 'python -m laview_dl.cli --setup' to configure a device.")
            return
        
        # Use device configuration
        camera_ip = device_config["ip_address"]
        camera_channel = device_config.get("camera_channel", 1)
        
        # Set environment variables if credentials are stored
        if device_config.get("username"):
            import os
            os.environ["LAVIEW_NVR_USER"] = device_config["username"]
        
        if device_config.get("password"):
            import os
            os.environ["LAVIEW_NVR_PASS"] = device_config["password"]
        
        # Set timeout if configured
        if device_config.get("timeout"):
            from .camerasdk import CameraSdk
            CameraSdk.init(device_config["timeout"])
        
        # Check if we have the required arguments
        if not parameters.START_DATE or not parameters.START_TIME:
            print("Error: START_DATE and START_TIME are required")
            print(f"Usage: python -m laview_dl.cli --device {parameters.device} START_DATE START_TIME [END_DATE END_TIME]")
            return
        
        try:
            # Parse the datetime strings using flexible parser
            start_datetime_str, end_datetime_str = parse_datetime_strings(
                parameters.START_DATE, 
                parameters.START_TIME, 
                parameters.END_DATE, 
                parameters.END_TIME
            )
            
            init(camera_ip, camera_channel)
            work(camera_ip, start_datetime_str, end_datetime_str, True, camera_channel)
        except KeyboardInterrupt:
            print("^-C: Exited")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            raise e
        
        return
    
    # Handle legacy mode
    if not validate_legacy_args(parameters):
        return
    
    try:
        setattr(parameters, "utc", True)
        camera_ip = parameters.IP
        camera_channel = parameters.camera
        init(camera_ip, camera_channel)

        # Parse the datetime strings using flexible parser
        start_datetime_str, end_datetime_str = parse_datetime_strings(
            parameters.START_DATE, 
            parameters.START_TIME, 
            parameters.END_DATE, 
            parameters.END_TIME
        )

        work(camera_ip, start_datetime_str, end_datetime_str, parameters.utc, camera_channel)

    except KeyboardInterrupt:
        print("^-C: Exited")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        raise (e)


if __name__ == "__main__":
    main()
