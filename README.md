# LaView DVR/NVR downloading script

A script for automatic downloading video files from LaView NVRs & cameras via ISAPI interface. (Based on Hikvision).

Forked / based on https://github.com/qb60/hikvision-downloader for HikVision Cameras.

Tested on [LV-T9708MHS](https://support.laviewsecurity.com/hc/en-us/sections/115004123387-LV-T9708MHS)

1. DVR Expects time to be 'utc'. Just enter your local time you want videos from but specify the utc flag.
2. Camera selection is now done via the `--camera` command line argument. Specify which camera channel to download from:

    python -m laview_dl.cli --camera 3 192.168.1.100 2024-04-12 00:00:00 2024-04-12 04:00:00

## Usage

```bash
python -m laview_dl.cli [--camera CAMERA] CAM_IP START_DATE START_TIME END_DATE END_TIME
```

### Arguments:
- `--camera CAMERA`: Camera channel number (default: 1)
- `CAM_IP`: Camera/NVR IP address
- `START_DATE`: Start date (YYYY-MM-DD)
- `START_TIME`: Start time (HH:MM:SS)
- `END_DATE`: End date (YYYY-MM-DD, optional, defaults to today)
- `END_TIME`: End time (HH:MM:SS, optional, defaults to now)

### Examples:
```bash
# Download from camera 1 (default)
python -m laview_dl.cli 192.168.1.100 2024-04-12 00:00:00 2024-04-12 04:00:00

# Download from camera 2
python -m laview_dl.cli --camera 2 192.168.1.100 2024-04-12 00:00:00 2024-04-12 04:00:00

# Download from camera 3 with custom credentials
LAVIEW_NVR_USER=admin LAVIEW_NVR_PASS=qwert123 python -m laview_dl.cli --camera 3 192.168.1.100 2024-04-12 00:00:00
```
