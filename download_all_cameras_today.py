"""
Script to download video from all cameras between 3:30 PM and 5:00 PM today.

This script connects to a configured LaView NVR device, detects all available
cameras, and downloads video footage from each camera for the specified time
range on the current day.
"""

import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

from laview_dl.authtype import AuthType
from laview_dl.camerasdk import CameraSdk, init
from laview_dl.config import ConfigManager
from laview_dl.work import work


def get_all_cameras(
    auth_handler: Any, camera_ip: str, max_channels: int = 10
) -> List[Dict[str, Any]]:
    """
    Get all available cameras from the NVR.

    Parameters
    ----------
    auth_handler : Any
        Authentication handler for the NVR connection.
    camera_ip : str
        IP address of the NVR device.
    max_channels : int, optional
        Maximum number of channels to check, by default 10.

    Returns
    -------
    List[Dict[str, Any]]
        List of camera information dictionaries, each containing:
        - id: Camera channel ID (int)
        - name: Camera name (str)
        - enabled: Whether camera is enabled (bool)

    Notes
    -----
    First attempts to get camera info from the NVR API. If that fails,
    falls back to detecting cameras by testing video search on different
    channels.
    """
    # Try to get camera info from NVR API first
    camera_list = CameraSdk.get_camera_info(auth_handler, camera_ip)
    if camera_list:
        return camera_list

    # Fallback to detection method
    camera_list = CameraSdk.detect_available_cameras(
        auth_handler, camera_ip, max_channels
    )
    if camera_list:
        return camera_list

    # If both methods fail, return empty list
    return []


def download_from_all_cameras(
    device_name: Optional[str] = None,
    start_time: str = "3:30 PM",
    end_time: str = "5:00 PM",
) -> None:
    """
    Download video from all cameras for a specified time range today.

    Parameters
    ----------
    device_name : Optional[str], optional
        Name of the configured device to use. If None, uses the first
        configured device, by default None.
    start_time : str, optional
        Start time in natural language format (e.g., "3:30 PM"), by default
        "3:30 PM".
    end_time : str, optional
        End time in natural language format (e.g., "5:00 PM"), by default
        "5:00 PM".

    Raises
    ------
    RuntimeError
        If no devices are configured, device is not found, authentication
        fails, or no cameras are detected.

    Notes
    -----
    The script will:
    1. Load device configuration
    2. Authenticate with the NVR
    3. Detect all available cameras
    4. Download video from each camera for the specified time range today
    """
    config_manager = ConfigManager()

    # Get device configuration
    if device_name is None:
        devices = config_manager.list_devices()
        if not devices:
            raise RuntimeError(
                "No devices configured. Run 'python -m laview_dl.cli --setup' "
                "to configure a device."
            )
        device_name = devices[0]
        print(f"No device specified, using first configured device: {device_name}")

    device_config = config_manager.get_device_config(device_name)
    if not device_config:
        raise RuntimeError(
            f"Device '{device_name}' not found. "
            "Run 'python -m laview_dl.cli --setup' to configure a device."
        )

    camera_ip = device_config["ip_address"]
    timeout = device_config.get("timeout", CameraSdk.default_timeout_seconds)

    # Set environment variables if credentials are stored
    if device_config.get("username"):
        os.environ["LAVIEW_NVR_USER"] = device_config["username"]
    if device_config.get("password"):
        os.environ["LAVIEW_NVR_PASS"] = device_config["password"]

    # Set timeout
    CameraSdk.init(timeout)

    # Get credentials
    user_name = os.getenv("LAVIEW_NVR_USER")
    user_password = os.getenv("LAVIEW_NVR_PASS")

    if not user_name or not user_password:
        raise RuntimeError(
            "Username and password not found. Set credentials in device "
            "config or environment variables: LAVIEW_NVR_USER and "
            "LAVIEW_NVR_PASS"
        )

    # Authenticate
    auth_type = CameraSdk.get_auth_type(camera_ip, user_name, user_password)
    if auth_type == AuthType.UNAUTHORISED:
        raise RuntimeError("Unauthorised! Check login and password")

    auth_handler = CameraSdk.get_auth(auth_type, user_name, user_password)

    # Get all cameras
    print(f"Detecting cameras on {camera_ip}...")
    cameras = get_all_cameras(auth_handler, camera_ip)

    if not cameras:
        raise RuntimeError(
            f"No cameras detected on {camera_ip}. "
            "Please check the device connection and configuration."
        )

    print(f"Found {len(cameras)} camera(s):")
    for camera in cameras:
        print(f"  - Camera {camera['id']}: {camera['name']}")

    # Build datetime strings for today
    today = datetime.now().strftime("%Y-%m-%d")
    start_datetime_str = f"{today} {start_time}"
    end_datetime_str = f"{today} {end_time}"

    print(f"\nDownloading video from {start_datetime_str} to {end_datetime_str}")

    # Download from each camera
    for camera in cameras:
        camera_id = camera["id"]
        camera_name = camera["name"]

        if not camera.get("enabled", True):
            print(f"\nSkipping disabled camera: {camera_name} (ID: {camera_id})")
            continue

        print(f"\n{'=' * 60}")
        print(f"Processing Camera {camera_id}: {camera_name}")
        print(f"{'=' * 60}")

        try:
            # Initialize logger for this camera
            init(camera_ip, camera_id, verbose_level=0)

            # Download video
            work(camera_ip, start_datetime_str, end_datetime_str, True, camera_id)

            print(f"✓ Successfully downloaded video from Camera {camera_id}")

        except Exception as e:
            print(f"✗ Error downloading from Camera {camera_id}: {e}")
            continue

    print(f"\n{'=' * 60}")
    print("Download process completed")
    print(f"{'=' * 60}")


def main() -> None:
    """
    Main entry point for the script.

    Parses command line arguments and calls download_from_all_cameras.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Download video from all cameras between 3:30 PM and 5:00 PM today"
    )
    parser.add_argument(
        "--device",
        type=str,
        help="Name of the configured device to use (default: first configured device)",
    )
    parser.add_argument(
        "--start-time",
        type=str,
        default="3:30 PM",
        help='Start time in natural language format (default: "3:30 PM")',
    )
    parser.add_argument(
        "--end-time",
        type=str,
        default="5:00 PM",
        help='End time in natural language format (default: "5:00 PM")',
    )

    args = parser.parse_args()

    try:
        download_from_all_cameras(
            device_name=args.device,
            start_time=args.start_time,
            end_time=args.end_time,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

