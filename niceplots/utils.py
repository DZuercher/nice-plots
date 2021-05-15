# Authors: Dominik Zuercher, Valeria Glauser

import os
import logging
import sys


def init_logger(filepath, logging_level='info'):
    """
    Initializes a logger instance for a file.

    :param filepath: The path of the file for which the logging is done.
    :param logging_level: The logger level
                          (critical, error, warning, info or debug)
    :return: Logger instance
    """
    logger = logging.getLogger(os.path.basename(filepath)[:10])

    if len(logger.handlers) == 0:
        log_formatter = logging.Formatter(
            "%(asctime)s %(name)0.10s %(levelname)0.3s   %(message)s ",
            "%y-%m-%d %H:%M:%S")
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)
        logger.propagate = False
        set_logger_level(logger, logging_level)

    return logger


def set_logger_level(logger, level):
    """
    Sets the global logging level. Meassages with a logging level below will
    not be logged.

    :param logger: A logger instance.
    :param logging_level: The logger severity
                          (critical, error, warning, info or debug)
    """

    logging_levels = {'critical': logging.CRITICAL,
                      'error': logging.ERROR,
                      'warning': logging.WARNING,
                      'info': logging.INFO,
                      'debug': logging.DEBUG}

    logger.setLevel(logging_levels[level])
