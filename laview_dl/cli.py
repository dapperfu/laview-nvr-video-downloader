import argparse
import os
import sys
from argparse import Namespace
from typing import Any, List, Optional, Tuple

from .authtype import AuthType
from .camerasdk import CameraSdk
from .config import (
    ConfigManager,
    list_configured_devices,
    remove_device_setup,
    setup_device,
)
from .date_parser import FlexibleDateParser
from .work import work


def parse_camera_channels(camera_arg: str) -> list[int]:
    """
    Parse camera channel specification into a list of channel numbers.
    
    Supports comma-separated values and ranges (e.g., "1,2,4-6").
    
    Parameters
    ----------
    camera_arg : str
        Camera channel specification. Can be:
        - Single value: "1"
        - Comma-separated: "1,2,3"
        - Range: "4-6"
        - Mixed: "1,2,4-6"
    
    Returns
    -------
    list[int]
        Sorted, deduplicated list of camera channel numbers.
    
    Raises
    ------
    ValueError
        If the input contains invalid values or ranges.
    """
    if not camera_arg:
        return [1]
    
    channels: list[int] = []
    parts = camera_arg.split(",")
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        if "-" in part:
            # Handle range (e.g., "4-6")
            range_parts = part.split("-", 1)
            if len(range_parts) != 2:
                raise ValueError(f"Invalid range format: {part}")
            
            try:
                start = int(range_parts[0].strip())
                end = int(range_parts[1].strip())
            except ValueError as e:
                raise ValueError(f"Invalid range values in '{part}': {e}") from e
            
            if start < 1 or end < 1:
                raise ValueError(f"Camera channel numbers must be positive integers: {part}")
            
            if start > end:
                raise ValueError(f"Range start must be <= end: {part}")
            
            channels.extend(range(start, end + 1))
        else:
            # Handle single value
            try:
                channel = int(part)
            except ValueError as e:
                raise ValueError(f"Invalid camera channel number: {part}") from e
            
            if channel < 1:
                raise ValueError(f"Camera channel numbers must be positive integers: {part}")
            
            channels.append(channel)
    
    # Sort and deduplicate
    return sorted(list(set(channels)))


def resolve_camera_spec(
    camera_arg: str,
    auth_handler: Any,
    camera_ip: str,
) -> List[int]:
    """
    Resolve camera specification to channel IDs (uint).
    
    Supports both numeric channel specifications and camera name matching.
    Camera names are only used for input selection - they resolve to channel IDs.
    The actual download operations always use the numeric channel ID.
    
    Parameters
    ----------
    camera_arg : str
        Camera specification. Can be:
        - Numeric: "1", "1,2,3", "4-6" (channel numbers)
        - Text: "Entrance", "cam1" (camera names with partial matching)
    auth_handler : Any
        Authentication handler for NVR connection (required for name matching).
    camera_ip : str
        IP address of the NVR device (required for name matching).
    
    Returns
    -------
    List[int]
        List of camera channel IDs (uint).
    
    Raises
    ------
    ValueError
        If the input is invalid, no matches found, or multiple partial matches.
    """
    if not camera_arg:
        return [1]
    
    # Check if input is numeric (could be channel numbers)
    parts = camera_arg.split(",")
    is_numeric = True
    
    # Check if all parts are numeric (accounting for ranges)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            # Check if range parts are numeric
            range_parts = part.split("-", 1)
            try:
                int(range_parts[0].strip())
                int(range_parts[1].strip())
            except ValueError:
                is_numeric = False
                break
        else:
            try:
                int(part)
            except ValueError:
                is_numeric = False
                break
    
    # If numeric, use existing channel parsing
    if is_numeric:
        return parse_camera_channels(camera_arg)
    
    # Otherwise, treat as camera name(s) and match against NVR to get channel IDs
    camera_list = CameraSdk.get_camera_info(auth_handler, camera_ip)
    if not camera_list:
        raise ValueError(
            f"Could not retrieve camera list from NVR at {camera_ip}. "
            "Cannot match camera names. Please use numeric channel numbers instead.",
        )
    
    results: List[int] = []
    input_parts = [p.strip() for p in parts if p.strip()]
    
    for input_part in input_parts:
        # Try exact match first (case-insensitive)
        exact_matches = [
            cam for cam in camera_list
            if cam["name"].lower() == input_part.lower()
        ]
        
        if exact_matches:
            if len(exact_matches) > 1:
                raise ValueError(
                    f"Multiple cameras found with exact name '{input_part}': "
                    f"{[cam['name'] for cam in exact_matches]}",
                )
            cam = exact_matches[0]
            results.append(cam["id"])
            continue
        
        # Try partial matches (name starts with input, case-insensitive)
        partial_matches = [
            cam for cam in camera_list
            if cam["name"].lower().startswith(input_part.lower())
        ]
        
        if not partial_matches:
            available_names = [cam["name"] for cam in camera_list]
            raise ValueError(
                f"No camera found matching '{input_part}'. "
                f"Available cameras: {available_names}",
            )
        
        if len(partial_matches) > 1:
            matched_names = [cam["name"] for cam in partial_matches]
            raise ValueError(
                f"Multiple cameras match '{input_part}': {matched_names}. "
                "Please use a more specific name.",
            )
        
        # Single partial match found - use its channel ID
        cam = partial_matches[0]
        results.append(cam["id"])
    
    # Sort and deduplicate
    return sorted(list(set(results)))


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
  laview-cli --camera 1,2,4-6 10.145.17.202 "2020-04-15 00:30:00" "2020-04-15 10:59:59"
  LAVIEW_USER=admin LAVIEW_PASS=qwert123 laview-cli --camera 1 10.145.17.202 "2020-04-15 00:30:00"
  
        """

    parser = argparse.ArgumentParser(
        usage=usage, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter,
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
        "--cam",
        type=str,
        default="1",
        dest="camera",
        help="camera channel number(s) or camera name(s) - supports comma-separated values and ranges for channels (e.g., '1,2,4-6') or camera names with partial matching (e.g., 'Entrance', 'cam1') (default: 1). Can override device config when used with --device.",
    )

    # Verbose levels
    parser.add_argument("-v", "--verbose", action="count", default=0,
                       help="Increase verbosity (-v: GOSSIP, -vv: BANTER, -vvv: WHISPER, -vvvv: HINT, -vvvvv: TRACE)")

    if len(sys.argv) == 1:
        parser.print_help()
        return None
    args = parser.parse_args()

    # Fix argument parsing for device mode
    if args.device:
        # Extract datetime arguments from sys.argv, skipping known options
        datetime_args = []
        i = 1  # Skip script name (sys.argv[0])
        while i < len(sys.argv):
            arg = sys.argv[i]
            
            # Skip --device and its value
            if arg == "--device":
                i += 2  # Skip --device and device name
                continue
            
            # Skip --camera/--cam and its value
            if arg in ("--camera", "--cam"):
                i += 2  # Skip --camera/--cam and camera value
                continue
            if arg.startswith("--camera=") or arg.startswith("--cam="):
                i += 1  # Skip --camera=VALUE (single argument)
                continue
            
            # Skip --verbose/-v flags (they don't take values, but can be chained like -vvv)
            if arg in ("--verbose", "-v") or (arg.startswith("-v") and all(c == "v" for c in arg[1:])):
                i += 1
                continue
            
            # Skip other known flags that don't take values
            if arg in ("--setup", "--list-devices", "--remove-device", "--status"):
                i += 1
                continue
            
            # This is a positional argument (datetime string)
            datetime_args.append(arg)
            i += 1

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
        if auth_type == AuthType.BASIC:
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
        device_name = parameters.device
        
        # Set environment variables if credentials are stored
        if device_config.get("username"):
            os.environ["LAVIEW_NVR_USER"] = device_config["username"]

        if device_config.get("password"):
            os.environ["LAVIEW_NVR_PASS"] = device_config["password"]

        # Set timeout if configured
        timeout = device_config.get("timeout", CameraSdk.default_timeout_seconds)
        CameraSdk.init(timeout)

        # Get credentials
        user_name = os.getenv("LAVIEW_NVR_USER")
        user_password = os.getenv("LAVIEW_NVR_PASS")

        if not user_name or not user_password:
            print("Error: Username and password not found.")
            print("Set credentials in device config or environment variables: LAVIEW_NVR_USER and LAVIEW_NVR_PASS")
            return

        # Authenticate to get auth_handler for camera name resolution
        auth_type = CameraSdk.get_auth_type(camera_ip, user_name, user_password)
        if auth_type == AuthType.UNAUTHORISED:
            print("Error: Unauthorised! Check login and password")
            return

        auth_handler = CameraSdk.get_auth(auth_type, user_name, user_password)
        
        # Check if --camera/--cam flag was explicitly provided (override device config)
        # Handle both --camera VALUE and --camera=VALUE formats
        camera_override = any(
            arg.startswith("--camera") or arg.startswith("--cam") for arg in sys.argv
        )
        if camera_override:
            # Resolve camera spec (supports both numeric and name matching)
            try:
                camera_channels = resolve_camera_spec(parameters.camera, auth_handler, camera_ip)
            except ValueError as e:
                print(f"Error resolving camera specification: {e}")
                return
        else:
            # Use device's configured camera_channel (single value)
            camera_channel = device_config.get("camera_channel", 1)
            camera_channels = [camera_channel]

        # Check if we have the required arguments
        if not parameters.START_DATETIME:
            print("Error: START_DATETIME is required")
            print(f"Usage: laview-cli --device {parameters.device} START_DATETIME [END_DATETIME]")
            return

        try:
            # Parse the datetime strings using flexible parser
            start_datetime_str, end_datetime_str = parse_datetime_strings(
                parameters.START_DATETIME,
                parameters.END_DATETIME,
            )

            # Process each camera channel
            for camera_channel in camera_channels:
                try:
                    # Initialize logger with verbose level for this camera
                    from .camerasdk import init
                    init(camera_ip, camera_channel, verbose_level=parameters.verbose)

                    work(
                        camera_ip, start_datetime_str, end_datetime_str, True, camera_channel,
                        device_name=device_name,
                    )
                except KeyboardInterrupt:
                    print("^-C: Exited")
                    break
                except Exception as e:
                    print(f"Error processing camera {camera_channel}: {e}")
                    # Continue with next camera instead of stopping
                    continue
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
        parameters.utc = True
        camera_ip = parameters.IP
        
        # Parse camera channels (supports multiple cameras)
        try:
            camera_channels = parse_camera_channels(parameters.camera)
        except ValueError as e:
            print(f"Error parsing camera channels: {e}")
            return

        # Parse the datetime strings using flexible parser
        start_datetime_str, end_datetime_str = parse_datetime_strings(
            parameters.START_DATETIME,
            parameters.END_DATETIME,
        )

        # Process each camera channel
        for camera_channel in camera_channels:
            try:
                # Initialize logger with verbose level for this camera
                from .camerasdk import init
                init(camera_ip, camera_channel, verbose_level=parameters.verbose)

                work(camera_ip, start_datetime_str, end_datetime_str, parameters.utc, camera_channel)
            except KeyboardInterrupt:
                print("^-C: Exited")
                break
            except Exception as e:
                print(f"Error processing camera {camera_channel}: {e}")
                # Continue with next camera instead of stopping
                continue

    except KeyboardInterrupt:
        print("^-C: Exited")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        raise (e)


if __name__ == "__main__":
    main()
