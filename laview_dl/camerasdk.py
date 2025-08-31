import os
import re
import shutil
import socket
import time
import uuid
from datetime import timedelta
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

import requests
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth

from .authtype import AuthType
from .logging import Logger, logging_wrapper, LogPrinter
from .track import Track
from .utils import create_directory_for
from .utils import DEFAULT_TIMEOUT_SECONDS
from .utils import get_path_to_video_archive

MAX_BYTES_LOG_FILE_SIZE = 100000
MAX_LOG_FILES_COUNT = 20

write_logs = True


class CameraSdk:
    default_timeout_seconds = 10
    DEVICE_ERROR_CODE = 500
    __CAMERA_AVAILABILITY_TEST_PORT = 80
    # =============================== URLS ===============================

    __TIME_URL = "/ISAPI/System/time"
    __SEARCH_VIDEO_URL = "/ISAPI/ContentMgmt/search/"
    __DOWNLOAD_VIDEO_URL = "/ISAPI/ContentMgmt/download"
    __REBOOT_URL = "/ISAPI/System/reboot"

    # =============================== URLS ===============================

    @classmethod
    def init(cls, default_timeout_seconds):
        cls.default_timeout_seconds = default_timeout_seconds

    @classmethod
    def get_error_message_from(cls, answer):
        answer_text = cls.__clear_xml_from_namespaces(answer.text)
        answer_xml = ElementTree.fromstring(answer_text)

        answer_status_element = answer_xml.find("statusString")
        answer_substatus_element = answer_xml.find("subStatusCode")

        if answer_status_element is not None and answer_substatus_element is not None:
            status = answer_status_element.text
            substatus = answer_substatus_element.text
            message = "Error {} {}: {} - {}".format(
                answer.status_code, answer.reason, status, substatus
            )
        else:
            message = answer_text

        return message

    @classmethod
    def reboot_camera(cls, auth_handler, cam_ip):
        answer = requests.put(
            cls.__get_service_url(cam_ip, cls.__REBOOT_URL),
            auth=auth_handler,
            data=[],
            timeout=cls.default_timeout_seconds,
        )
        if not answer:
            raise RuntimeError(cls.get_error_message_from(answer))

    @classmethod
    def get_auth_type(cls, cam_ip, user_name, password):
        auth_handler = HTTPBasicAuth(user_name, password)
        request = cls.__make_get_request(auth_handler, cam_ip, cls.__TIME_URL)
        if request.ok:
            return AuthType.BASIC

        auth_handler = HTTPDigestAuth(user_name, password)
        request = cls.__make_get_request(auth_handler, cam_ip, cls.__TIME_URL)
        if request.ok:
            return AuthType.DIGEST

        return AuthType.UNAUTHORISED

    @classmethod
    def get_time_offset(cls, auth_handler, cam_ip):
        answer = cls.__make_get_request(auth_handler, cam_ip, cls.__TIME_URL)
        if answer:
            time_info_text = cls.__clear_xml_from_namespaces(answer.text)
            time_info_xml = ElementTree.fromstring(time_info_text)
            timezone_raw = time_info_xml.find("timeZone")
            time_offset = cls.parse_timezone(timezone_raw.text)
            return time_offset
        else:
            raise RuntimeError(cls.get_error_message_from(answer))

    @staticmethod
    def parse_timezone(raw_timezone):
        timezone_text = raw_timezone.replace("CST", "")
        time_offset_parts = timezone_text.split(":")
        hours = int(time_offset_parts[0])
        minutes = int(time_offset_parts[1])
        seconds = int(time_offset_parts[2])

        if hours < 0:
            minutes = -minutes
            seconds = -seconds

        return -timedelta(hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def get_auth(auth_type, name, password):
        if auth_type == AuthType.BASIC:
            return HTTPBasicAuth(name, password)
        elif auth_type == AuthType.DIGEST:
            return HTTPDigestAuth(name, password)
        else:
            return None

    @classmethod
    def download_file(cls, auth_handler, cam_ip, file_uri, file_name):
        download_request = Element("downloadRequest")

        # Add playbackURI
        playback_uri = SubElement(download_request, "playbackURI")
        playback_uri.text = file_uri

        request_data = ElementTree.tostring(
            download_request, encoding="utf8", method="xml"
        )

        url = cls.__get_service_url(cam_ip, cls.__DOWNLOAD_VIDEO_URL)
        answer = requests.get(
            url=url,
            auth=auth_handler,
            data=request_data,
            stream=True,
            timeout=cls.default_timeout_seconds,
        )
        if answer:
            with open(file_name, "wb") as out_file:
                shutil.copyfileobj(answer.raw, out_file)
            answer.close()

        return answer

    @classmethod
    def wait_until_camera_rebooted(
        cls,
        cam_ip,
        camera_reboot_time_seconds,
        delay_before_checking_availability_seconds,
    ):
        time.sleep(delay_before_checking_availability_seconds)

        duration = (
            camera_reboot_time_seconds - delay_before_checking_availability_seconds
        )
        tmax = time.time() + duration
        while time.time() < tmax:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(cls.default_timeout_seconds)
            try:
                s.connect((cam_ip, int(cls.__CAMERA_AVAILABILITY_TEST_PORT)))
                s.shutdown(socket.SHUT_RDWR)
                return True
            except OSError:
                time.sleep(1)
            finally:
                s.close()
        return False

    @classmethod
    def get_video_tracks_info(cls, auth_handler, cam_ip, utc_time_interval, max_videos, camera_channel=1):
        # Create the root element
        cm_search_description = Element("CMSearchDescription")

        # Add searchID
        search_id = SubElement(cm_search_description, "searchID")
        search_id.text = str(uuid.uuid4())  # Generate a unique search ID

        # Add trackIDList
        track_id_list = SubElement(cm_search_description, "trackIDList")
        track_id = SubElement(track_id_list, "trackID")
        track_id.text = f"{camera_channel}01"

        # Add timeSpanList
        time_span_list = SubElement(cm_search_description, "timeSpanList")
        time_span = SubElement(time_span_list, "timeSpan")

        start_time_tz_text, end_time_tz_text = utc_time_interval.to_tz_text()

        start_time_element = SubElement(time_span, "startTime")
        start_time_element.text = start_time_tz_text

        end_time_element = SubElement(time_span, "endTime")
        end_time_element.text = end_time_tz_text

        # Add maxResults
        max_results = SubElement(cm_search_description, "maxResults")
        max_results.text = str(max_videos)

        # Add searchResultPosition
        search_result_position = SubElement(
            cm_search_description, "searchResultPostion"
        )
        search_result_position.text = "0"

        # Add metadataList
        metadata_list = SubElement(cm_search_description, "metadataList")
        metadata_descriptor = SubElement(metadata_list, "metadataDescriptor")
        metadata_descriptor.text = "//recordType.meta.std-cgi.com"

        request_data = ElementTree.tostring(
            cm_search_description, encoding="utf8", method="xml"
        )
        answer = cls.__make_get_request(
            auth_handler, cam_ip, cls.__SEARCH_VIDEO_URL, request_data
        )

        return answer

    @classmethod
    def create_tracks_from_info(cls, answer, local_time_offset):
        answer_text = cls.__clear_xml_from_namespaces(answer.text)
        answer_xml = ElementTree.fromstring(answer_text)

        match_list = answer_xml.find("matchList")
        match_items = match_list.findall("searchMatchItem")

        tracks = []
        for match_item in match_items:
            media_descriptor = match_item.find("mediaSegmentDescriptor")
            playback_uri = media_descriptor.find("playbackURI")
            new_track = Track(playback_uri.text, local_time_offset)
            tracks.append(new_track)

        return tracks

    @staticmethod
    def __get_service_url(cam_ip, relative_url):
        return "http://" + cam_ip + relative_url

    @staticmethod
    def __clear_xml_from_namespaces(xml_text):
        return re.sub(' xmlns="[^"]+"', "", xml_text, count=0)

    @classmethod
    def __make_get_request(cls, auth_handler, cam_ip, url, request_data=None):
        return requests.get(
            url=cls.__get_service_url(cam_ip, url),
            auth=auth_handler,
            data=request_data,
            timeout=cls.default_timeout_seconds,
        )

    @staticmethod
    def __replace_subelement_with(parent, new_subelement):
        subelement_tag = new_subelement.tag
        subelement = parent.find(subelement_tag)
        parent.remove(subelement)

        parent.append(new_subelement)
        return parent

    @staticmethod
    def __replace_subelement_body_with(parent, subelement_tag, new_body_text):
        subelement = parent.find(subelement_tag)
        subelement.clear()
        inner_element = ElementTree.fromstring(new_body_text)
        subelement.append(inner_element)
        return parent


log_file_name_pattern = "{}.log"


def init(cam_ip, camera_channel=1):
    path_to_log_file = log_file_name_pattern.format(cam_ip)

    create_directory_for(get_path_to_video_archive(cam_ip, camera_channel))

    Logger.init_logger(
        write_logs, path_to_log_file, MAX_BYTES_LOG_FILE_SIZE, MAX_LOG_FILES_COUNT
    )

    CameraSdk.init(DEFAULT_TIMEOUT_SECONDS)

@logging_wrapper(before=LogPrinter.get_all_tracks)
def get_all_tracks(auth_handler, cam_ip, utc_time_interval, camera_channel=1):
    tracks = []
    while True:
        answer = get_video_tracks_info(auth_handler, cam_ip, utc_time_interval, camera_channel)
        local_time_offset = utc_time_interval.local_time_offset
        if answer:
            new_tracks = CameraSdk.create_tracks_from_info(answer, local_time_offset)
            tracks += new_tracks
            if len(new_tracks) < MAX_VIDEOS_NUMBER_IN_ONE_REQUEST:
                break

            last_track = tracks[-1]
            utc_time_interval.start_time = last_track.get_time_interval().end_time
        else:
            tracks = []
            break

    return tracks


@logging_wrapper(after=LogPrinter.get_video_tracks_info)
def get_video_tracks_info(auth_handler, cam_ip, utc_time_interval, camera_channel=1):
    return CameraSdk.get_video_tracks_info(
        auth_handler, cam_ip, utc_time_interval, MAX_VIDEOS_NUMBER_IN_ONE_REQUEST, camera_channel
    )
