import os
import subprocess
import time
from datetime import datetime

from .logging import LogPrinter, logging_wrapper

write_logs = True

path_to_video_archive = "video/"
CAMERA_REBOOT_TIME_SECONDS = 90
DELAY_BEFORE_CHECKING_AVAILABILITY_SECONDS = 30
DEFAULT_TIMEOUT_SECONDS = 10
DELAY_BETWEEN_DOWNLOADING_FILES_SECONDS = 1
DELAY_AFTER_TIMEOUT_SECONDS = 5

MAX_VIDEOS_NUMBER_IN_ONE_REQUEST = 50  # Reduced from 100 for better stability

video_file_extension = ".mp4"


def get_path_to_video_archive(cam_ip: str, camera_channel: int = 1):
    return os.path.join(path_to_video_archive, cam_ip, f"camera{camera_channel}")


def download_videos(tracks, auth_handler, cam_ip, camera_channel=1):
    download_tracks(tracks, auth_handler, cam_ip, camera_channel)


def create_directory_for(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def set_video_exif_metadata(file_path: str, start_datetime: datetime) -> bool:
    """
    Set Exif metadata tags for a video file using exiftool.

    Parameters
    ----------
    file_path : str
        Path to the video file.
    start_datetime : datetime
        Datetime object representing the start time of the video.

    Returns
    -------
    bool
        True if exiftool successfully set the metadata, False otherwise.

    Notes
    -----
    Sets the following Exif tags to the start date/time:
    - CreateDate
    - ModifyDate
    - TrackCreateDate
    - TrackModifyDate
    - MediaCreateDate
    - MediaModifyDate

    The datetime is formatted as "YYYY:MM:DD HH:MM:SS" for exiftool.
    """
    if not os.path.exists(file_path):
        return False

    # Format datetime for exiftool: "YYYY:MM:DD HH:MM:SS"
    date_str = start_datetime.strftime("%Y:%m:%d %H:%M:%S")

    try:
        # Use exiftool to set all date/time tags
        subprocess.run(
            [
                "exiftool",
                "-overwrite_original",
                f"-CreateDate={date_str}",
                f"-ModifyDate={date_str}",
                f"-TrackCreateDate={date_str}",
                f"-TrackModifyDate={date_str}",
                f"-MediaCreateDate={date_str}",
                f"-MediaModifyDate={date_str}",
                file_path,
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except subprocess.CalledProcessError:
        # exiftool failed, but don't fail the download
        return False
    except FileNotFoundError:
        # exiftool not installed, silently skip
        return False
    except subprocess.TimeoutExpired:
        # exiftool timed out, but don't fail the download
        return False


@logging_wrapper(before=LogPrinter.download_tracks)
def download_tracks(tracks, auth_handler, cam_ip, camera_channel=1):
    for track in tracks:
        # TODO retry only N times
        while True:
            if download_file_with_retry(auth_handler, cam_ip, track, camera_channel):
                break
            time.sleep(DELAY_AFTER_TIMEOUT_SECONDS)

        time.sleep(DELAY_BETWEEN_DOWNLOADING_FILES_SECONDS)


def download_file_with_retry(auth_handler, cam_ip, track, camera_channel=1):
    from .camerasdk import CameraSdk

    time_interval = track.get_time_interval().to_local_time()
    start_time_text = time_interval.to_filename_text()
    file_name = os.path.join(
        get_path_to_video_archive(cam_ip, camera_channel), start_time_text + video_file_extension,
    )
    url_to_download = track.url_to_download()

    create_directory_for(file_name)
    answer = download_file(auth_handler, cam_ip, url_to_download, file_name)
    if answer:
        # Set Exif metadata using the start time of the video
        set_video_exif_metadata(file_name, time_interval.start_time)
        return True
    if answer.status_code == CameraSdk.DEVICE_ERROR_CODE:
        reboot_camera(auth_handler, cam_ip)
        wait_until_camera_rebooted(cam_ip)
    return False


@logging_wrapper(
    before=LogPrinter.download_file_before, after=LogPrinter.download_file_after,
)
def download_file(auth_handler, cam_ip, url_to_download, file_name):
    from .camerasdk import CameraSdk
    return CameraSdk.download_file(auth_handler, cam_ip, url_to_download, file_name)


@logging_wrapper(before=LogPrinter.reboot_camera)
def reboot_camera(auth_handler, cam_ip):
    from .camerasdk import CameraSdk
    CameraSdk.reboot_camera(auth_handler, cam_ip)


@logging_wrapper(after=LogPrinter.wait_until_camera_rebooted)
def wait_until_camera_rebooted(cam_ip):
    from .camerasdk import CameraSdk
    CameraSdk.wait_until_camera_rebooted(
        cam_ip, CAMERA_REBOOT_TIME_SECONDS, DELAY_BEFORE_CHECKING_AVAILABILITY_SECONDS,
    )
