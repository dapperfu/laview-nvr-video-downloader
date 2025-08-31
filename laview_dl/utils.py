import os
import time

from .logging import logging_wrapper
from .logging import LogPrinter

write_logs = True

path_to_video_archive = "video/"
CAMERA_REBOOT_TIME_SECONDS = 90
DELAY_BEFORE_CHECKING_AVAILABILITY_SECONDS = 30
DEFAULT_TIMEOUT_SECONDS = 10
DELAY_BETWEEN_DOWNLOADING_FILES_SECONDS = 1

MAX_VIDEOS_NUMBER_IN_ONE_REQUEST = 100

video_file_extension = ".mp4"


def get_path_to_video_archive(cam_ip: str, camera_channel: int = 1):
    return os.path.join(path_to_video_archive, cam_ip, f"camera{camera_channel}")


def download_videos(auth_handler, cam_ip, camera_channel=1):
    tracks = get_all_tracks(auth_handler, cam_ip, camera_channel)
    download_tracks(tracks, auth_handler, cam_ip, camera_channel)


def create_directory_for(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


@logging_wrapper(before=LogPrinter.download_tracks)
def download_tracks(tracks, auth_handler, cam_ip, camera_channel=1):
    for track in tracks:
        # TODO retry only N times
        while True:
            if download_file_with_retry(auth_handler, cam_ip, track, camera_channel):
                break

        time.sleep(DELAY_BETWEEN_DOWNLOADING_FILES_SECONDS)


def download_file_with_retry(auth_handler, cam_ip, track, camera_channel=1):
    start_time_text = track.get_time_interval().to_local_time().to_filename_text()
    file_name = os.path.join(
        get_path_to_video_archive(cam_ip, camera_channel), start_time_text + video_file_extension
    )
    url_to_download = track.url_to_download()

    create_directory_for(file_name)
    answer = download_file(auth_handler, cam_ip, url_to_download, file_name)
    if answer:
        return True
    else:
        if answer.status_code == CameraSdk.DEVICE_ERROR_CODE:
            reboot_camera(auth_handler, cam_ip)
            wait_until_camera_rebooted(cam_ip)
        return False


@logging_wrapper(
    before=LogPrinter.download_file_before, after=LogPrinter.download_file_after
)
def download_file(auth_handler, cam_ip, url_to_download, file_name):
    return CameraSdk.download_file(auth_handler, cam_ip, url_to_download, file_name)


@logging_wrapper(before=LogPrinter.reboot_camera)
def reboot_camera(auth_handler, cam_ip):
    CameraSdk.reboot_camera(auth_handler, cam_ip)


@logging_wrapper(after=LogPrinter.wait_until_camera_rebooted)
def wait_until_camera_rebooted(cam_ip):
    CameraSdk.wait_until_camera_rebooted(
        cam_ip, CAMERA_REBOOT_TIME_SECONDS, DELAY_BEFORE_CHECKING_AVAILABILITY_SECONDS
    )
