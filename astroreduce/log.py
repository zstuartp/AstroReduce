import datetime
import logging

from . import env

PROGRAM_NAME = "AstroReduce" # TODO: Use a global
CURRENT_DATE_TIME = datetime.datetime.now().strftime("%y-%m-%dT%H:%M:%S")

logger = None
ch = None


def _log_var_change(key: str="", value: str="False"):
    logger.debug("Local environment set: " + key + "=" + value)


def _set_verbose_hook(key: str="VERBOSE", value: str="False"):
    """ Enable verbose console output """
    if value == "True":
        ch.setLevel(logging.INFO)
    else:
        ch.setLevel(logging.WARNING)


def init_logging():
    global logger
    global ch

    logger = logging.getLogger(PROGRAM_NAME + " Log")
    fh = logging.FileHandler("reduce-" + CURRENT_DATE_TIME.replace("-", "").replace("T", "at").replace(":", "") + ".log")
    ch = logging.StreamHandler()
    log_format_file = logging.Formatter("%(asctime)s::%(levelname)s -- %(message)s")
    log_format_console = logging.Formatter("%(levelname)s -- %(message)s")
    fh.setFormatter(log_format_file)
    ch.setFormatter(log_format_console)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    logger.addHandler(fh)

    env.add_hook("VERBOSE", _set_verbose_hook)
    _set_verbose_hook("VERBOSE", env.get("VERBOSE"))
    env.add_hook("", _log_var_change)

    logger.info("================================================")
    logger.info(PROGRAM_NAME + " Log")
    logger.info(CURRENT_DATE_TIME)
    logger.info("================================================")


def get_logger():
    global logger
    return logger
