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
from .utils import MAX_VIDEOS_NUMBER_IN_ONE_REQUEST

MAX_BYTES_LOG_FILE_SIZE = 100000
MAX_LOG_FILES_COUNT = 20

write_logs = True


class CameraSdk:
    default_timeout_seconds = 10
    DEVICE_ERROR_CODE = 500
    __CAMERA_AVAILABILITY_TEST_PORT = 80
    # =============================== URLS ===============================

    __TIME_URL = "/ISAPI/System/time"
    __SEARCH_VIDEO_URL = "/ISAPI/ContentMgmt/search"
    __DOWNLOAD_VIDEO_URL = "/ISAPI/ContentMgmt/download"
    __REBOOT_URL = "/ISAPI/System/reboot"
    __DEVICE_INFO_URL = "/ISAPI/System/deviceInfo"
    __CAMERA_INFO_URL = "/ISAPI/System/video/input/channels"
    __CAMERA_INFO_URL_ALT = "/ISAPI/System/video/inputs"
    __CAMERA_INFO_URL_ALT2 = "/ISAPI/System/video/input"

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
        try:
            # Handle complex timezone format like "CST+5:00:00DST01:00:00,M3.2.1/02:00:00,M11.1.1/00:00:00"
            # Extract the base offset and DST offset
            
            # Remove timezone name (CST, EST, etc.)
            timezone_text = raw_timezone
            for tz_name in ["CST", "EST", "PST", "MST", "GMT", "UTC"]:
                timezone_text = timezone_text.replace(tz_name, "")
            
            # Look for the base offset (e.g., +5:00:00)
            import re
            base_offset_match = re.search(r'([+-]\d+):(\d+):(\d+)', timezone_text)
            if not base_offset_match:
                return timedelta(0)
            
            hours = int(base_offset_match.group(1))
            minutes = int(base_offset_match.group(2))
            seconds = int(base_offset_match.group(3))
            
            # Look for DST offset (e.g., DST01:00:00)
            dst_offset_match = re.search(r'DST(\d+):(\d+):(\d+)', timezone_text)
            if dst_offset_match:
                dst_hours = int(dst_offset_match.group(1))
                dst_minutes = int(dst_offset_match.group(2))
                dst_seconds = int(dst_offset_match.group(3))
                
                # Add DST offset to base offset
                total_hours = hours + dst_hours
                total_minutes = minutes + dst_minutes
                total_seconds = seconds + dst_seconds
            else:
                total_hours = hours
                total_minutes = minutes
                total_seconds = seconds
            
            # Create timedelta (negative because we want UTC offset)
            return -timedelta(hours=total_hours, minutes=total_minutes, seconds=total_seconds)
            
        except (ValueError, IndexError, AttributeError):
            # Handle unexpected timezone formats gracefully
            return timedelta(0)  # Return zero offset for unknown formats

    @classmethod
    def get_device_info(cls, auth_handler, cam_ip):
        """Get device information from the NVR."""
        try:
            answer = cls.__make_get_request(auth_handler, cam_ip, cls.__DEVICE_INFO_URL)
            if answer and answer.ok:
                device_info_text = cls.__clear_xml_from_namespaces(answer.text)
                device_info_xml = ElementTree.fromstring(device_info_text)
                
                # Extract device information
                device_name = device_info_xml.find("deviceName")
                device_id = device_info_xml.find("deviceID")
                model = device_info_xml.find("model")
                serial_number = device_info_xml.find("serialNumber")
                mac_address = device_info_xml.find("macAddress")
                firmware_version = device_info_xml.find("firmwareVersion")
                firmware_released_date = device_info_xml.find("firmwareReleasedDate")
                
                return {
                    "deviceName": device_name.text if device_name is not None else "Unknown",
                    "deviceID": device_id.text if device_id is not None else "Unknown",
                    "model": model.text if model is not None else "Unknown",
                    "serialNumber": serial_number.text if serial_number is not None else "Unknown",
                    "macAddress": mac_address.text if mac_address is not None else "Unknown",
                    "firmwareVersion": firmware_version.text if firmware_version is not None else "Unknown",
                    "firmwareReleasedDate": firmware_released_date.text if firmware_released_date is not None else "Unknown"
                }
            else:
                return None
        except Exception:
            return None

    @classmethod
    def get_camera_info(cls, auth_handler, cam_ip):
        """Get camera information from the NVR."""
        # Try multiple possible endpoints for camera information
        endpoints = [
            cls.__CAMERA_INFO_URL,
            cls.__CAMERA_INFO_URL_ALT,
            cls.__CAMERA_INFO_URL_ALT2
        ]
        
        for endpoint in endpoints:
            try:
                answer = cls.__make_get_request(auth_handler, cam_ip, endpoint)
                if answer and answer.ok:
                    camera_info_text = cls.__clear_xml_from_namespaces(answer.text)
                    camera_info_xml = ElementTree.fromstring(camera_info_text)
                    
                    # Try different XML structures
                    channels = []
                    
                    # Try videoInputChannel elements
                    channels = camera_info_xml.findall(".//videoInputChannel")
                    if not channels:
                        # Try videoInput elements
                        channels = camera_info_xml.findall(".//videoInput")
                    if not channels:
                        # Try input elements
                        channels = camera_info_xml.findall(".//input")
                    
                    camera_list = []
                    
                    for channel in channels:
                        channel_id = channel.find("id")
                        if channel_id is None:
                            channel_id = channel.find("channelID")
                        if channel_id is None:
                            channel_id = channel.find("inputID")
                            
                        name = channel.find("name")
                        if name is None:
                            name = channel.find("channelName")
                        if name is None:
                            name = channel.find("inputName")
                            
                        enabled = channel.find("enabled")
                        if enabled is None:
                            enabled = channel.find("status")
                        
                        if channel_id is not None:
                            camera_info = {
                                "id": int(channel_id.text),
                                "name": name.text if name is not None else f"Camera {channel_id.text}",
                                "enabled": enabled.text.lower() == "true" if enabled is not None else True
                            }
                            camera_list.append(camera_info)
                    
                    if camera_list:
                        return camera_list
                        
            except Exception:
                continue
        
        return None

    @classmethod
    def detect_available_cameras(cls, auth_handler, cam_ip, max_channels=10):
        """Detect available cameras by testing video search on different channels."""
        available_cameras = []
        
        # Test channels 0-9 (0 is usually the grid view, 1-9 are individual cameras)
        # Start with channel 0 to check for grid view
        for channel in range(max_channels):
            try:
                # Create a simple search request for this channel
                search_request = Element("CMSearchDescription")
                
                # Add searchID
                search_id = SubElement(search_request, "searchID")
                search_id.text = str(uuid.uuid4())
                
                # Add trackIDList
                track_id_list = SubElement(search_request, "trackIDList")
                track_id = SubElement(track_id_list, "trackID")
                track_id.text = f"{channel:02d}01"  # Format as 2-digit number + "01"
                
                # Add timeSpanList for a recent time period
                time_span_list = SubElement(search_request, "timeSpanList")
                time_span = SubElement(time_span_list, "timeSpan")
                
                # Search for the last hour
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                one_hour_ago = now - timedelta(hours=1)
                
                start_time = SubElement(time_span, "startTime")
                start_time.text = one_hour_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                end_time = SubElement(time_span, "endTime")
                end_time.text = now.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                request_data = ElementTree.tostring(search_request, encoding="utf8", method="xml")
                
                answer = cls.__make_post_request(auth_handler, cam_ip, cls.__SEARCH_VIDEO_URL, request_data)
                
                if answer and answer.ok:
                    # If we get a successful response, this channel exists
                    camera_info = {
                        "id": channel,
                        "name": f"Camera {channel}" if channel > 0 else "Grid View",
                        "enabled": True
                    }
                    available_cameras.append(camera_info)
                    
            except Exception:
                continue
        
        return available_cameras if available_cameras else None

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
        try:
            answer = requests.get(
                url=url,
                auth=auth_handler,
                data=request_data,
                stream=True,
                timeout=cls.default_timeout_seconds,
            )
            if answer and answer.ok:
                with open(file_name, "wb") as out_file:
                    shutil.copyfileobj(answer.raw, out_file)
                answer.close()
                return True
            else:
                return False

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return False

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
        answer = cls.__make_post_request(
            auth_handler, cam_ip, cls.__SEARCH_VIDEO_URL, request_data
        )

        return answer

    @classmethod
    def create_tracks_from_info(cls, answer, local_time_offset):
        answer_text = cls.__clear_xml_from_namespaces(answer.text)
        answer_xml = ElementTree.fromstring(answer_text)

        match_list = answer_xml.find("matchList")
        if match_list is None:
            # No videos found in the specified time range
            return []
            
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
    def __make_get_request(cls, auth_handler, cam_ip, url):
        return requests.get(
            url=cls.__get_service_url(cam_ip, url),
            auth=auth_handler,
            timeout=cls.default_timeout_seconds,
        )

    @classmethod
    def __make_post_request(cls, auth_handler, cam_ip, url, request_data):
        return requests.post(
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


def init(cam_ip, camera_channel=1, verbose_level=0):
    path_to_log_file = log_file_name_pattern.format(cam_ip)

    create_directory_for(get_path_to_video_archive(cam_ip, camera_channel))

    Logger.init_logger(
        write_logs, path_to_log_file, MAX_BYTES_LOG_FILE_SIZE, MAX_LOG_FILES_COUNT, verbose_level
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
