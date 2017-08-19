import datetime
import logging

PROGRAM_NAME = "AstroReduce" # TODO: Use a global
CURRENT_DATE_TIME = datetime.datetime.now().strftime("%y-%m-%dT%H:%M:%S")

logger = None


def init_logging():
    global logger
    logger = logging.getLogger(PROGRAM_NAME + " Log")
    fh = logging.FileHandler("reduce-" + CURRENT_DATE_TIME.replace("-", "").replace("T", "at").replace(":", "") + ".log")
    ch = logging.StreamHandler()
    log_format_file = logging.Formatter("%(asctime)s::%(levelname)s -- %(message)s")
    log_format_console = logging.Formatter("%(levelname)s -- %(message)s")
    fh.setFormatter(log_format_file)
    ch.setFormatter(log_format_console)
    logger.setLevel(logging.DEBUG)
    ch.setLevel(logging.WARNING)
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.info("================================================")
    logger.info(PROGRAM_NAME + " Log")
    logger.info(CURRENT_DATE_TIME)
    logger.info("================================================")


def get_logger():
    global logger
    return logger
