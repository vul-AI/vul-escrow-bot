import os
import time
import logging


def initialize_logger() -> logging.Logger:
    """
    Initializes a logger that logs to a file and the console.
    The log file name is in the format log-<unix_time>
    The logger also logs the thread_id
    """

    if not os.path.exists("logs"):
        os.mkdir("logs")
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create a format for the logs
    log_format = logging.Formatter(
        "%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Create a file handler to log to a file
    unix_time = int(time.time())
    file_handler = logging.FileHandler(f"logs/logfile-{unix_time}.log")
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    # Create a stream handler to log to the console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_format)
    logger.addHandler(stream_handler)

    return logger


logger = initialize_logger()
