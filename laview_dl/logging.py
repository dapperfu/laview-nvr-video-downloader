import logging.handlers

class Logger:
    LOGGER_NAME = "laview_video_downloader"

    @staticmethod
    def init_logger(
        write_logs, path_to_log_file, max_bytes_log_size, max_log_files_count
    ):
        logger = Logger.get_logger()
        logger.setLevel(logging.DEBUG)

        console_formatter = logging.Formatter(
            fmt="%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        if write_logs:
            file_formatter = logging.Formatter(
                fmt="%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # file_handler = logging.handlers.WatchedFileHandler(path_to_log_file)
            file_handler = logging.handlers.RotatingFileHandler(
                path_to_log_file,
                maxBytes=max_bytes_log_size,
                backupCount=max_log_files_count,
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

    @staticmethod
    def get_logger():
        return logging.getLogger(Logger.LOGGER_NAME)


# ================= END logger ===================
# from src.log_wrapper import logging_wrapper
# ================= START log_wrapper ===================
def logging_wrapper(before=None, after=None):
    def log_decorator(func):
        def wrapper_func(*args, **kwargs):
            if before is not None:
                before(*args, **kwargs)

            result = func(*args, **kwargs)

            if after is not None:
                after(result)

            return result

        return wrapper_func

    return log_decorator


# ================= END log_wrapper ===================
# from src.log_printer import *
# ================= START log_printer ===================


class LogPrinter:
    @staticmethod
    def get_all_tracks(_1, _2, utc_time_interval):
        start_time_text, end_time_text = utc_time_interval.to_local_time().to_text()

        Logger.get_logger().info("Start time: {}".format(start_time_text))
        Logger.get_logger().info("End time: {}".format(end_time_text))
        Logger.get_logger().info("Getting tracks list...")

    @staticmethod
    def get_video_tracks_info(result):
        if not result:
            error_message = CameraSdk.get_error_message_from(result)
            Logger.get_logger().error("Error occurred during getting tracks list")
            Logger.get_logger().error(error_message)

    @staticmethod
    def download_tracks(tracks, _1, _2):
        Logger.get_logger().info("Found {} files".format(len(tracks)))

    @staticmethod
    def download_file_before(_1, _2, _3, file_name):
        Logger.get_logger().info("Downloading {}".format(file_name))

    @staticmethod
    def download_file_after(result):
        if not result:
            error_message = CameraSdk.get_error_message_from(result)
            Logger.get_logger().error(error_message)

    @staticmethod
    def reboot_camera(_1, _2):
        Logger.get_logger().info("Rebooting camera...")

    @staticmethod
    def wait_until_camera_rebooted(result):
        if result:
            Logger.get_logger().info("Camera is up, continue downloading")
        else:
            Logger.get_logger().info("Camera is still down")
