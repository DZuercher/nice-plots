import logging


class CustomFormatter(logging.Formatter):
    RED = "\033[91m"
    VIOLET = "\033[95m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    ENDC = "\033[0m"

    base_format_str = (
        "%(asctime)s - %(filename)12s:%(lineno)3d - %(levelname)7s - %(message)s"
    )

    FORMATS = {
        logging.DEBUG: VIOLET + base_format_str + ENDC,
        logging.INFO: base_format_str,
        logging.WARNING: BOLD + base_format_str + ENDC,
        logging.ERROR: BOLD + RED + base_format_str + ENDC,
        logging.CRITICAL: BOLD + RED + base_format_str + ENDC,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        new = formatter.format(record)
        return new


def init_logger(file: str) -> logging.Logger:
    """
    Initializes a logger instance for a file.
    :param file: The name of the file for which the logging is done.
    :return: Logger instance
    """
    logger = logging.getLogger(file)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    return logger


def set_logger_level(logger: logging.Logger, level: str) -> None:
    """
    Sets the global logging level. Meassages with a logging level below will
    not be logged.

    :param logger: A logger instance.
    :param logging_level: The logger severity
    """
    logging_levels = {
        "0": logging.CRITICAL,
        "1": logging.ERROR,
        "2": logging.WARNING,
        "3": logging.INFO,
        "4": logging.DEBUG,
    }

    logger.setLevel(logging_levels[level])
