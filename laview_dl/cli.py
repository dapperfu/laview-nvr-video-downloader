import argparse
import sys
from argparse import Namespace
from datetime import datetime
from typing import Optional

from .camerasdk import init
from .work import work


def parse_parameters() -> Optional[Namespace]:
    usage = """
  %(prog)s [-u] CAM_IP START_DATE START_TIME END_DATE END_TIME
  
  If END_DATE and END_TIME aren't specified use now().

  Use the time setting on the DVR.
  """

    epilog = """
Examples:
  python %(prog)s 10.145.17.202 2020-04-15 00:30:00 2020-04-15 10:59:59
  CAMERA=2 python %(prog)s 10.145.17.202 2020-04-15 00:30:00 2020-04-15 10:59:59
  LAVIEW_USER=admin LAVIEW_PASS=qwert123 python %(prog)s 10.145.17.202 2020-04-15 00:30:0
  
        """

    parser = argparse.ArgumentParser(
        usage=usage, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("IP", help="camera's IP address")
    parser.add_argument("START_DATE", help="start date of interval")
    parser.add_argument("START_TIME", help="start time of interval")
    parser.add_argument(
        "END_DATE",
        nargs="?",
        help="end date of interval",
        default=datetime.now().strftime("%Y-%m-%d"),
    )
    parser.add_argument(
        "END_TIME",
        nargs="?",
        help="end time of interval",
        default=datetime.now().strftime("%H:%M:%S"),
    )

    if len(sys.argv) == 1:
        parser.print_help()
        return None
    else:
        args = parser.parse_args()
        return args


def main():
    parameters = parse_parameters()
    if parameters:
        try:
            setattr(parameters, "utc", True)
            camera_ip = parameters.IP
            init(camera_ip)

            start_datetime_str = parameters.START_DATE + " " + parameters.START_TIME
            end_datetime_str = str(parameters.END_DATE + " " + parameters.END_TIME)

            work(camera_ip, start_datetime_str, end_datetime_str, parameters.utc)

        except KeyboardInterrupt:
            print("^-C: Exited")

        except Exception as e:
            raise (e)


if __name__ == "__main__":
    main()
