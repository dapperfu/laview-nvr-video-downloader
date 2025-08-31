import logging.handlers

# Custom logging levels between INFO (20) and DEBUG (10)
# Each level is 2 points apart, giving us 9 levels total
VERBOSE_9 = 19  # "GOSSIP" - Very high-level chatter
VERBOSE_8 = 17  # "CHATTER" - High-level system chatter  
VERBOSE_7 = 15  # "BANTER" - Friendly system communication
VERBOSE_6 = 13  # "TALK" - General system talking
VERBOSE_5 = 11  # "WHISPER" - Quiet system details
VERBOSE_4 = 9   # "MURMUR" - Soft system murmurs
VERBOSE_3 = 7   # "HINT" - Subtle system hints
VERBOSE_2 = 5   # "CLUE" - System clues and breadcrumbs
VERBOSE_1 = 3   # "TRACE" - System trace information

# Register custom levels
logging.addLevelName(VERBOSE_9, "GOSSIP")
logging.addLevelName(VERBOSE_8, "CHATTER") 
logging.addLevelName(VERBOSE_7, "BANTER")
logging.addLevelName(VERBOSE_6, "TALK")
logging.addLevelName(VERBOSE_5, "WHISPER")
logging.addLevelName(VERBOSE_4, "MURMUR")
logging.addLevelName(VERBOSE_3, "HINT")
logging.addLevelName(VERBOSE_2, "CLUE")
logging.addLevelName(VERBOSE_1, "TRACE")

# Add convenience methods to Logger class
def gossip(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_9):
        self._log(VERBOSE_9, message, args, **kwargs)

def chatter(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_8):
        self._log(VERBOSE_8, message, args, **kwargs)

def banter(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_7):
        self._log(VERBOSE_7, message, args, **kwargs)

def talk(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_6):
        self._log(VERBOSE_6, message, args, **kwargs)

def whisper(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_5):
        self._log(VERBOSE_5, message, args, **kwargs)

def murmur(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_4):
        self._log(VERBOSE_4, message, args, **kwargs)

def hint(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_3):
        self._log(VERBOSE_3, message, args, **kwargs)

def clue(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_2):
        self._log(VERBOSE_2, message, args, **kwargs)

def trace(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_1):
        self._log(VERBOSE_1, message, args, **kwargs)

# Add methods to Logger class
logging.Logger.gossip = gossip
logging.Logger.chatter = chatter
logging.Logger.banter = banter
logging.Logger.talk = talk
logging.Logger.whisper = whisper
logging.Logger.murmur = murmur
logging.Logger.hint = hint
logging.Logger.clue = clue
logging.Logger.trace = trace


class Logger:
    LOGGER_NAME = "laview_video_downloader"

    @staticmethod
    def init_logger(
        write_logs, path_to_log_file, max_bytes_log_size, max_log_files_count, verbose_level=0
    ):
        logger = Logger.get_logger()
        
        # Set log level based on verbose level
        if verbose_level == 0:
            log_level = logging.INFO
        elif verbose_level == 1:
            log_level = VERBOSE_9  # GOSSIP
        elif verbose_level == 2:
            log_level = VERBOSE_7  # BANTER
        elif verbose_level == 3:
            log_level = VERBOSE_5  # WHISPER
        elif verbose_level == 4:
            log_level = VERBOSE_3  # HINT
        elif verbose_level == 5:
            log_level = VERBOSE_1  # TRACE
        else:
            log_level = logging.DEBUG  # Full debug for -vvvvv and beyond
        
        logger.setLevel(log_level)

        console_formatter = logging.Formatter(
            fmt="%(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        if write_logs:
            file_formatter = logging.Formatter(
                fmt="%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            file_handler = logging.handlers.RotatingFileHandler(
                path_to_log_file,
                maxBytes=max_bytes_log_size,
                backupCount=max_log_files_count,
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

    @staticmethod
    def get_logger():
        return logging.getLogger(Logger.LOGGER_NAME)


# ================= END logger ===================
# from src.log_wrapper import logging_wrapper
# ================= START log_wrapper ===================
def logging_wrapper(before=None, after=None, level=logging.INFO):
    def log_decorator(func):
        def wrapper_func(*args, **kwargs):
            logger = Logger.get_logger()
            
            if before is not None and logger.isEnabledFor(level):
                before(*args, **kwargs)

            result = func(*args, **kwargs)

            if after is not None and logger.isEnabledFor(level):
                after(result)

            return result

        return wrapper_func

    return log_decorator


# ================= END log_wrapper ===================
# from src.log_printer import *
# ================= START log_printer ===================


class LogPrinter:
    @staticmethod
    def get_all_tracks(_1, _2, utc_time_interval, _3=None):
        start_time_text, end_time_text = utc_time_interval.to_local_time().to_text()

        Logger.get_logger().info("Start time: {}".format(start_time_text))
        Logger.get_logger().info("End time: {}".format(end_time_text))
        Logger.get_logger().info("Getting tracks list...")

    @staticmethod
    def get_video_tracks_info(result):
        if not result:
            Logger.get_logger().error("Error occurred during getting tracks list")
            Logger.get_logger().error("Request failed")

    @staticmethod
    def download_file_after(result):
        if not result:
            Logger.get_logger().error("Download failed")

    @staticmethod
    def download_tracks(tracks, _1, _2, _3=None):
        Logger.get_logger().info("Found {} files".format(len(tracks)))

    @staticmethod
    def download_file_before(_1, _2, _3, file_name):
        Logger.get_logger().info("Downloading {}".format(file_name))



    @staticmethod
    def reboot_camera(_1, _2):
        Logger.get_logger().info("Rebooting camera...")

    @staticmethod
    def wait_until_camera_rebooted(result):
        if result:
            Logger.get_logger().info("Camera is up, continue downloading")
        else:
            Logger.get_logger().info("Camera is still down")
