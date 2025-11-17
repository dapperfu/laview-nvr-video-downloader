import os
from datetime import timedelta

import requests

from .authtype import AuthType
from .camerasdk import CameraSdk, get_all_tracks
from .logging import Logger
from .time_interval import TimeInterval
from .utils import download_videos


def work(camera_ip, start_datetime_str, end_datetime_str, use_utc_time, camera_channel=1):
    logger = Logger.get_logger()
    try:
        logger.info(f"Processing IP {camera_ip}.")
        logger.info(f"Processing Camera {camera_channel}.")
        logger.info(
            "{} time is used".format("UTC" if use_utc_time else "Camera's local"),
        )

        # Add debug logging at different levels
        logger.gossip(f"🔍 Starting video download process for {camera_ip}")
        logger.chatter(f"📡 Connecting to camera {camera_channel} on {camera_ip}")
        logger.banter(f"🤝 Establishing communication with NVR at {camera_ip}")
        logger.talk(f"📊 Time range: {start_datetime_str} to {end_datetime_str}")
        logger.whisper(f"⚙️ Using {'UTC' if use_utc_time else 'local'} time mode")

        user_name = os.getenv("LAVIEW_NVR_USER")
        user_password = os.getenv("LAVIEW_NVR_PASS")

        logger.murmur(f"🔐 Checking authentication for user: {user_name or 'not set'}")

        auth_type = CameraSdk.get_auth_type(camera_ip, user_name, user_password)
        if auth_type == AuthType.UNAUTHORISED:
            raise RuntimeError("Unauthorised! Check login and password")

        logger.hint(f"✅ Authentication type: {auth_type}")
        auth_handler = CameraSdk.get_auth(auth_type, user_name, user_password)

        if use_utc_time:
            local_time_offset = timedelta()
        else:
            logger.clue("🕐 Getting time offset from camera...")
            local_time_offset = CameraSdk.get_time_offset(auth_handler, camera_ip)

        logger.trace(f"⏰ Local time offset: {local_time_offset}")

        utc_time_interval = TimeInterval.from_string(
            start_datetime_str, end_datetime_str, local_time_offset,
        ).to_utc()

        logger.banter(f"📅 Converted time interval to UTC: {utc_time_interval}")

        tracks = get_all_tracks(auth_handler, camera_ip, utc_time_interval, camera_channel)
        download_videos(tracks, auth_handler, camera_ip, camera_channel)

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")

    except Exception as e:
        logger.exception(e)
