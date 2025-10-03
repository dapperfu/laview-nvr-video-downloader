import argparse
import sys
from argparse import Namespace
from datetime import datetime
from typing import Optional

from .camerasdk import init, CameraSdk
from .work import work
from .config import setup_device, list_configured_devices, remove_device_setup, ConfigManager
from .date_parser import FlexibleDateParser


def parse_parameters() -> Optional[Namespace]:
    usage = """
  %(prog)s [--setup|--list-devices|--remove-device|--status] [-u] [--device DEVICE|--camera CAMERA] [CAM_IP] START_DATETIME [END_DATETIME]
  
  If END_DATETIME isn't specified use now().

  Use the time setting on the DVR.
  
  Commands:
    --setup              Configure a new device
    --list-devices       List all configured devices
    --remove-device      Remove a configured device
    --status             Test device connectivity and authentication
  
  Date/Time Formats Supported:
    - Standard: 2025-08-30 08:00:00, 08/30/2025 08:00 AM
    - Natural: today, yesterday, now, 2 days ago
    - Formatted: August 30, 2025, 08:00 AM
    - Relative: next week, last month, this year
    - Combined: "8 AM yesterday", "August 30, 2025 08:00 AM"
  """

    epilog = """
Examples:
  # Setup a new device
  laview-cli --setup
  
  # List configured devices
  laview-cli --list-devices
  
  # Remove a device
  laview-cli --remove-device
  
  # Test device connectivity and authentication
  laview-cli --status --device shop
  laview-cli --status --device office-nvr
  
  # Use a configured device with flexible date formats
  laview-cli --device office-nvr "August 30, 2025 08:00 AM" "August 31, 2025 08:00 AM"
  laview-cli --device home-camera "today 06:00 AM" "tomorrow 06:00 AM"
  laview-cli --device shop-nvr "yesterday 08:00 AM" "now"
  laview-cli --device camera "8 AM yesterday" "6 PM today"
  
  # Use IP address directly (legacy mode)
  laview-cli 10.145.17.202 "2020-04-15 00:30:00" "2020-04-15 10:59:59"
  laview-cli --camera 2 10.145.17.202 "2020-04-15 00:30:00" "2020-04-15 10:59:59"
  laview-cli --camera 3 10.145.17.202 "2020-04-15 00:30:00" "2020-04-15 10:59:59"
  LAVIEW_USER=admin LAVIEW_PASS=qwert123 laview-cli --camera 1 10.145.17.202 "2020-04-15 00:30:00"
  
        """

    parser = argparse.ArgumentParser(
        usage=usage, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Setup commands
    parser.add_argument("--setup", action="store_true", help="Configure a new device")
    parser.add_argument("--list-devices", action="store_true", help="List all configured devices")
    parser.add_argument("--remove-device", action="store_true", help="Remove a configured device")
    parser.add_argument("--status", action="store_true", help="Test device connectivity and authentication")
    
    # Device selection
    parser.add_argument("--device", help="Use a configured device by name")
    
    # Legacy arguments (only used when not using --device)
    parser.add_argument("IP", nargs="?", help="camera's IP address (required when not using --device)")
    parser.add_argument("START_DATETIME", nargs="?", help="start datetime (required when not using --device)")
    parser.add_argument(
        "END_DATETIME",
        nargs="?",
        help="end datetime",
        default="now",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=1,
        help="camera channel number (default: 1, only used when not using --device)",
    )
    
    # Verbose levels
    parser.add_argument("-v", "--verbose", action="count", default=0, 
                       help="Increase verbosity (-v: GOSSIP, -vv: BANTER, -vvv: WHISPER, -vvvv: HINT, -vvvvv: TRACE)")

    if len(sys.argv) == 1:
        parser.print_help()
        return None
    else:
        args = parser.parse_args()
        
        # Fix argument parsing for device mode
        if args.device:
            # Extract datetime arguments from sys.argv
            device_found = False
            datetime_args = []
            for arg in sys.argv:
                if arg == '--device':
                    device_found = True
                    continue
                if device_found and arg != args.device:
                    datetime_args.append(arg)
            
            # Set the datetime arguments correctly
            if len(datetime_args) >= 1:
                args.START_DATETIME = datetime_args[0]
            if len(datetime_args) >= 2:
                args.END_DATETIME = datetime_args[1]
            else:
                args.END_DATETIME = "now"
        
        return args


def validate_legacy_args(args: Namespace) -> bool:
    """Validate that required arguments are provided for legacy mode."""
    if not args.IP or not args.START_DATETIME:
        print("Error: IP and START_DATETIME are required when not using --device")
        return False
    return True


def get_device_config(device_name: str) -> Optional[dict]:
    """Get configuration for a specific device."""
    config_manager = ConfigManager()
    return config_manager.get_device_config(device_name)


def parse_datetime_strings(start_datetime: str, end_datetime: str) -> tuple[str, str]:
    """
    Parse datetime strings into formatted datetime strings.
    
    Args:
        start_datetime: Start datetime string
        end_datetime: End datetime string
        
    Returns:
        Tuple of (start_datetime_str, end_datetime_str)
    """
    try:
        # Parse start datetime
        start_dt = FlexibleDateParser.parse_datetime(start_datetime)
        start_datetime_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"Error parsing start datetime: {e}")
        print(f"Start datetime: '{start_datetime}'")
        print("Supported formats:")
        for fmt in FlexibleDateParser.get_supported_formats()[:5]:  # Show first 5 formats
            print(f"  - {fmt}")
        raise
    
    try:
        # Parse end datetime
        end_dt = FlexibleDateParser.parse_datetime(end_datetime)
        end_datetime_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"Error parsing end datetime: {e}")
        print(f"End datetime: '{end_datetime}'")
        print("Supported formats:")
        for fmt in FlexibleDateParser.get_supported_formats()[:5]:  # Show first 5 formats
            print(f"  - {fmt}")
        raise
    
    return start_datetime_str, end_datetime_str


def test_device_status(device_name: str) -> None:
    """
    Test device connectivity and authentication status.
    
    Args:
        device_name: Name of the configured device to test
    """
    import os
    from .authtype import AuthType
    
    device_config = get_device_config(device_name)
    if not device_config:
        print(f"Error: Device '{device_name}' not found.")
        print("Run 'python -m laview_dl.cli --setup' to configure a device.")
        return
    
    camera_ip = device_config["ip_address"]
    camera_channel = device_config.get("camera_channel", 1)
    timeout = device_config.get("timeout", CameraSdk.default_timeout_seconds)
    
    print(f"Testing device: {device_name}")
    print(f"IP Address: {camera_ip}")
    print(f"Camera Channel: {camera_channel}")
    print(f"Timeout: {timeout} seconds")
    print("-" * 50)
    
    # Set timeout
    CameraSdk.init(timeout)
    
    # Get credentials from device config or environment variables
    username = device_config.get("username") or os.environ.get("LAVIEW_NVR_USER")
    password = device_config.get("password") or os.environ.get("LAVIEW_NVR_PASS")
    
    if not username or not password:
        print("❌ Error: Username and password not found")
        print("Set credentials in device config or environment variables:")
        print("  LAVIEW_NVR_USER=your_username")
        print("  LAVIEW_NVR_PASS=your_password")
        return
    
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    try:
        # Test authentication
        print("Testing authentication...")
        auth_type = CameraSdk.get_auth_type(camera_ip, username, password)
        
        if auth_type == AuthType.UNAUTHORISED:
            print("❌ Authentication failed: Invalid credentials")
            return
        elif auth_type == AuthType.BASIC:
            print("✅ Authentication successful: HTTP Basic Auth")
        elif auth_type == AuthType.DIGEST:
            print("✅ Authentication successful: HTTP Digest Auth")
        
        # Test connectivity by getting system time
        print("Testing connectivity...")
        auth_handler = CameraSdk.get_auth(auth_type, username, password)
        time_offset = CameraSdk.get_time_offset(auth_handler, camera_ip)
        
        print("✅ Connectivity successful")
        print(f"Device timezone offset: {time_offset}")
        
        print("\n🎉 Device status: ONLINE and AUTHENTICATED")
        
    except Exception as e:
        print(f"❌ Error testing device: {e}")
        print("\nDevice status: OFFLINE or CONFIGURATION ERROR")


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
    
    if parameters.status:
        if not parameters.device:
            print("Error: --status requires --device to be specified")
            print("Usage: python -m laview_dl.cli --status --device DEVICE_NAME")
            return
        
        test_device_status(parameters.device)
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
        if not parameters.START_DATETIME:
            print("Error: START_DATETIME is required")
            print(f"Usage: laview-cli --device {parameters.device} START_DATETIME [END_DATETIME]")
            return
        
        try:
            # Initialize logger with verbose level
            from .camerasdk import init
            init(camera_ip, camera_channel, verbose_level=parameters.verbose)
            
            # Parse the datetime strings using flexible parser
            start_datetime_str, end_datetime_str = parse_datetime_strings(
                parameters.START_DATETIME, 
                parameters.END_DATETIME
            )
            
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
        
        # Initialize logger with verbose level
        from .camerasdk import init
        init(camera_ip, camera_channel, verbose_level=parameters.verbose)

        # Parse the datetime strings using flexible parser
        start_datetime_str, end_datetime_str = parse_datetime_strings(
            parameters.START_DATETIME, 
            parameters.END_DATETIME
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
