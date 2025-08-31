import os
from datetime import timedelta

import requests

from .authtype import AuthType
from .camerasdk import CameraSdk
from .logging import Logger
from .camerasdk import get_all_tracks
from .time_interval import TimeInterval
from .utils import download_videos


def work(camera_ip, start_datetime_str, end_datetime_str, use_utc_time, camera_channel=1):
    logger = Logger.get_logger()
    try:
        logger.info(f"Processing IP {camera_ip}.")
        logger.info(f"Processing Camera {camera_channel}.")
        logger.info(
            "{} time is used".format("UTC" if use_utc_time else "Camera's local")
        )

        user_name = os.getenv("LAVIEW_NVR_USER")
        user_password = os.getenv("LAVIEW_NVR_PASS")

        auth_type = CameraSdk.get_auth_type(camera_ip, user_name, user_password)
        if auth_type == AuthType.UNAUTHORISED:
            raise RuntimeError("Unauthorised! Check login and password")

        auth_handler = CameraSdk.get_auth(auth_type, user_name, user_password)

        if use_utc_time:
            local_time_offset = timedelta()
        else:
            local_time_offset = CameraSdk.get_time_offset(auth_handler, camera_ip)

        utc_time_interval = TimeInterval.from_string(
            start_datetime_str, end_datetime_str, local_time_offset
        ).to_utc()

        download_videos(auth_handler, camera_ip, camera_channel)

    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error: {}".format(e))

    except Exception as e:
        logger.exception(e)
