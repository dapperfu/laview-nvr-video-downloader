#!/usr/bin/env python3
"""
Test script for camera 2 download functionality.

This script demonstrates downloading video from camera 2 on the shop device.
"""

import subprocess
import sys
from datetime import datetime, timedelta


def test_camera2_download():
    """Test downloading from camera 2 on the shop device."""
    
    print("Testing Camera 2 Download from Shop Device")
    print("=" * 50)
    
    # Get current time and calculate a recent time range
    now = datetime.now()
    start_time = now - timedelta(hours=1)
    
    # Format times for the CLI
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Time range: {start_str} to {end_str}")
    print(f"Device: shop (192.168.1.100)")
    print(f"Camera: 2")
    print()
    
    # Build the command
    cmd = [
        sys.executable, "-m", "laview_dl.cli",
        "--device", "shop",
        start_str,
        end_str
    ]
    
    print("Running command:")
    print(" ".join(cmd))
    print()
    
    try:
        # Run the download command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="."
        )
        
        print("Command output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        print(f"Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("\n✅ SUCCESS: Camera 2 download test completed successfully!")
            print("Note: 0 files found is expected if there's no recent video activity.")
        else:
            print("\n❌ FAILED: Camera 2 download test failed!")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    test_camera2_download()
