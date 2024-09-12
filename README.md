# LaView DVR/NVR downloading script

A script for automatic downloading video files from LaView NVRs & cameras via ISAPI interface. (Based on Hikvision).

Forked / based on https://github.com/qb60/hikvision-downloader for HikVision Cameras.

Tested on [LV-T9708MHS](https://support.laviewsecurity.com/hc/en-us/sections/115004123387-LV-T9708MHS)

1. DVR Expects time to be 'utc'. Just enter your local time you want videos from but specify the utc flag.
2. Adding a camera option was easiest making the argument a environmental variable. Specify camera

    CAMERA=3 python video_download.py -u 192.168.1.100 2024-04-12 00:00:00 2024-04-12 04:00:00
