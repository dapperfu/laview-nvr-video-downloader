"""
Configuration management for laview-nvr-video-downloader.

This module handles device configuration storage and retrieval using TOML files.
Supports both TOML and JSON formats for backward compatibility.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomli_w  # For writing TOML files
    import tomllib  # Built-in in Python 3.11+ for reading
    TOML_AVAILABLE = True
    TOML_READER = tomllib
    TOML_WRITER = tomli_w
except ImportError:
    try:
        import toml  # Fallback to external toml library
        TOML_AVAILABLE = True
        TOML_READER = toml
        TOML_WRITER = toml
    except ImportError:
        TOML_AVAILABLE = False
        TOML_READER = None
        TOML_WRITER = None


class ConfigManager:
    """Manages configuration for laview-nvr-video-downloader devices."""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files. 
                       Defaults to ~/.config/laview-nvr-video-downloader
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.config/laview-nvr-video-downloader")

        self.config_dir = Path(config_dir)
        # Use TOML as primary format, with JSON fallback
        self.config_file = self.config_dir / "devices.toml"
        self.json_config_file = self.config_dir / "devices.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def get_device_config(self, device_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific device.
        
        Args:
            device_name: Name of the device to retrieve configuration for
            
        Returns:
            Device configuration dictionary or None if not found
        """
        config = self._load_config()
        return config.get(device_name)

    def set_device_config(self, device_name: str, config_data: Dict[str, Any]) -> None:
        """
        Set configuration for a specific device.
        
        Args:
            device_name: Name of the device
            config_data: Configuration data to store
        """
        config = self._load_config()
        config[device_name] = config_data
        self._save_config(config)

    def list_devices(self) -> list[str]:
        """
        List all configured device names.
        
        Returns:
            List of device names
        """
        config = self._load_config()
        return list(config.keys())

    def remove_device(self, device_name: str) -> bool:
        """
        Remove configuration for a specific device.
        
        Args:
            device_name: Name of the device to remove
            
        Returns:
            True if device was removed, False if not found
        """
        config = self._load_config()
        if device_name in config:
            del config[device_name]
            self._save_config(config)
            return True
        return False

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file. Supports TOML and JSON formats."""
        # Try TOML first (preferred format)
        if self.config_file.exists() and TOML_AVAILABLE:
            try:
                with open(self.config_file, "rb") as f:
                    return TOML_READER.load(f)
            except (OSError, Exception):
                pass

        # Fallback to JSON if TOML fails or not available
        if self.json_config_file.exists():
            try:
                with open(self.json_config_file, encoding="utf-8") as f:
                    config = json.load(f)
                    # Migrate to TOML format
                    self._migrate_to_toml(config)
                    return config
            except (OSError, json.JSONDecodeError):
                pass

        return {}

    def _migrate_to_toml(self, config: Dict[str, Any]) -> None:
        """Migrate JSON configuration to TOML format."""
        if TOML_AVAILABLE and config:
            try:
                with open(self.config_file, "wb") as f:
                    TOML_WRITER.dump(config, f)
                # Backup the old JSON file
                if self.json_config_file.exists():
                    backup_file = self.json_config_file.with_suffix(".json.backup")
                    self.json_config_file.rename(backup_file)
            except Exception:
                # If migration fails, keep using JSON
                pass

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file. Uses TOML format if available."""
        if TOML_AVAILABLE:
            with open(self.config_file, "wb") as f:
                TOML_WRITER.dump(config, f)
        else:
            # Fallback to JSON if TOML not available
            with open(self.json_config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)


def prompt_for_device_config() -> Dict[str, Any]:
    """
    Prompt user for device configuration details.
    
    Returns:
        Dictionary containing device configuration
    """
    print("=== LaView NVR Video Downloader Setup ===")
    print()

    # Get device name
    while True:
        device_name = input("Enter device name (e.g., 'office-nvr', 'home-camera'): ").strip()
        if device_name:
            break
        print("Device name cannot be empty. Please try again.")

    # Get IP address
    while True:
        ip_address = input("Enter device IP address: ").strip()
        if ip_address:
            break
        print("IP address cannot be empty. Please try again.")

    # Get username
    username = input("Enter username (or press Enter to use environment variable LAVIEW_NVR_USER): ").strip()

    # Get password
    password = input("Enter password (or press Enter to use environment variable LAVIEW_NVR_PASS): ").strip()

    # Get camera channel
    while True:
        camera_channel_input = input("Enter camera channel number (default: 1): ").strip()
        if not camera_channel_input:
            camera_channel = 1
            break
        try:
            camera_channel = int(camera_channel_input)
            if camera_channel > 0:
                break
            print("Camera channel must be a positive integer.")
        except ValueError:
            print("Please enter a valid number.")

    # Get timeout
    while True:
        timeout_input = input("Enter timeout in seconds (default: 10): ").strip()
        if not timeout_input:
            timeout = 10
            break
        try:
            timeout = int(timeout_input)
            if timeout > 0:
                break
            print("Timeout must be a positive integer.")
        except ValueError:
            print("Please enter a valid number.")

    config = {
        "device_name": device_name,
        "ip_address": ip_address,
        "camera_channel": camera_channel,
        "timeout": timeout,
    }

    # Only store credentials if provided
    if username:
        config["username"] = username
    if password:
        config["password"] = password

    return config


def setup_device() -> None:
    """Run the device setup process."""
    config_manager = ConfigManager()

    try:
        config = prompt_for_device_config()
        device_name = config["device_name"]

        # Check if device already exists
        existing_config = config_manager.get_device_config(device_name)
        if existing_config:
            overwrite = input(f"Device '{device_name}' already exists. Overwrite? (y/N): ").strip().lower()
            if overwrite not in ["y", "yes"]:
                print("Setup cancelled.")
                return

        # Save configuration
        config_manager.set_device_config(device_name, config)

        print(f"\nDevice '{device_name}' configured successfully!")
        print(f"Configuration saved to: {config_manager.config_file}")
        print("\nYou can now use this device with:")
        print(f"  python -m laview_dl.cli --device {device_name} START_DATE START_TIME [END_DATE END_TIME]")

    except KeyboardInterrupt:
        print("\nSetup cancelled.")
    except Exception as e:
        print(f"Error during setup: {e}")


def list_configured_devices() -> None:
    """List all configured devices."""
    config_manager = ConfigManager()
    devices = config_manager.list_devices()

    if not devices:
        print("No devices configured.")
        print("Run 'python -m laview_dl.cli --setup' to configure a device.")
        return

    print("Configured devices:")
    print()

    for device_name in devices:
        config = config_manager.get_device_config(device_name)
        print(f"  {device_name}:")
        print(f"    IP: {config.get('ip_address', 'N/A')}")
        print(f"    Camera: {config.get('camera_channel', 'N/A')}")
        print(f"    Timeout: {config.get('timeout', 'N/A')}s")
        if config.get("username"):
            print(f"    Username: {config['username']}")
        else:
            print("    Username: (from LAVIEW_NVR_USER env var)")
        print()


def remove_device_setup() -> None:
    """Remove a configured device."""
    config_manager = ConfigManager()
    devices = config_manager.list_devices()

    if not devices:
        print("No devices configured.")
        return

    print("Configured devices:")
    for i, device_name in enumerate(devices, 1):
        print(f"  {i}. {device_name}")

    try:
        choice = input("\nEnter device number to remove (or 'cancel'): ").strip()
        if choice.lower() in ["cancel", "c"]:
            print("Operation cancelled.")
            return

        device_index = int(choice) - 1
        if 0 <= device_index < len(devices):
            device_name = devices[device_index]
            confirm = input(f"Are you sure you want to remove '{device_name}'? (y/N): ").strip().lower()
            if confirm in ["y", "yes"]:
                if config_manager.remove_device(device_name):
                    print(f"Device '{device_name}' removed successfully.")
                else:
                    print(f"Failed to remove device '{device_name}'.")
            else:
                print("Operation cancelled.")
        else:
            print("Invalid device number.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
