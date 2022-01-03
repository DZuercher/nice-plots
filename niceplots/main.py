# Authors: Dominik Zuercher, Valeria Glauser

from niceplots import parser
from niceplots import process
from niceplots import barplot
from niceplots import lineplot
from niceplots import histogram
from niceplots import timeline
from niceplots import utils
import os
from tqdm import tqdm
import sys
import pathlib
import argparse
import platform
import subprocess
import logging
# from multiprocessing import Pool
# from functools import partial

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def init_logger(name): 
    """
    Initializes a logger instance for a file.

    :param filepath: The path of the file for which the logging is done.
    :param logging_level: The logger level
                          (critical, error, warning, info or debug)
    :return: Logger instance
    """
    logger = logging.getLogger(name)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    return logger


def set_logger_level(logger, level):
    """
    Sets the global logging level. Meassages with a logging level below will
    not be logged.

    :param logger: A logger instance.
    :param logging_level: The logger severity
                          (critical, error, warning, info or debug)
    """

    logging_levels = {0 : logging.CRITICAL,
                      1 : logging.ERROR,
                      2 : logging.WARNING,
                      3 : logging.INFO,
                      4 : logging.DEBUG}

    logger.setLevel(logging_levels[level])

def is_tool(name):
    try:
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            return False
    return True


def find_prog(prog):
    if is_tool(prog):
        cmd = "where" if platform.system() == "Windows" else "which"

        p = subprocess.Popen([cmd, prog], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        return output.decode('utf-8').rstrip()


def main_cli():
    description = "Nice plots allows you to easily and automatically produce "\
        "plots of your survey data."
    cli_args = argparse.ArgumentParser(description=description, add_help=True)
    cli_args.add_argument('--config_path', type=str, action='store',
                          default='example_config.yml',
                          help='Path to the configuration file. See examples/example_config.yml for example.')
    cli_args.add_argument('--data_path', type=str, nargs='+', action='store',
                          default=['example_data.csv'],
                          help='Path to the data file, or list of such paths (in csv format)')
    cli_args.add_argument('--time_labels', type=str, nargs='*', default=[''], action='store',
                          help='Labels for the different data sets (only used if plot_type=timeline).')
    cli_args.add_argument('--codebook_path', type=str, action='store',
                          default='example_codebook.csv',
                          help='Path to the codebook file (in csv format)')
    cli_args.add_argument('--output_name', type=str, action='store',
                          default='output1',
                          help="Name prefix for output plots. Serves also as "
                          "output directory name. NOTE: If there are configs "
                          "and codebooks in the output directory they will be "
                          "used instead of the global codebook and config files "
                          "specified by the config_path and codebook_path arguments.")
    cli_args.add_argument('--plot_type', type=str, action='store',
                          default='bars', choices=['bars', 'lines',
                                                   'histograms', 'timeline'],
                          help='Type of plots to produce. '
                          'If plot_type=timeline expects a list of data_paths and also time_labels')
    cli_args.add_argument('--format', type=str, action='store',
                          default='pdf', choices=['pdf', 'svg', 'png'],
                          help='Format of the output plots.')
    cli_args.add_argument('--clear_cache', action='store_true',
                          default=False,
                          help='Reset cache directory.')
    cli_args.add_argument('--verbosity', type=int, action='store',
                          default=3, choices=[1, 2, 3, 4],
                          help='Verbosity level (1=error, 2=warning, 3=info, 4=debug). Defaults to 3.')

    ARGS = cli_args.parse_args()
    main(plot_type=ARGS.plot_type,
         data_path=ARGS.data_path,
         config_path=ARGS.config_path,
         codebook_path=ARGS.codebook_path,
         output_name=ARGS.output_name,
         clear_cache=ARGS.clear_cache,
         format=ARGS.format,
         time_labels=ARGS.time_labels,
         verbosity=ARGS.verbosity)


def main(plot_type, data_path, config_path, codebook_path, output_name,
         clear_cache=False, format='pdf', time_labels=[""], verbosity=3):
    LOGGER = init_logger('niceplots')
    set_logger_level(LOGGER, verbosity)

    LOGGER.info("Starting nice-plots")

    if plot_type == 'timeline':
        if not len(time_labels) == len(data_path):
            raise Exception(
                "Can only make time series plot if same number "
                "of labels and data sets provided.")

    # parallel mode is deprecated
    serial = True
    if not serial:
        # For OSX > High Sierra disable additional security features
        # that prevent multithreading
        if ('OBJC_DISABLE_INITIALIZE_FORK_SAFETY' not in os.environ):
            os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
        if (os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] != 'YES'):
            os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
        LOGGER.info("Resettting environment. This can hang indefinitely on "
                    "some systems. If this is the case, switch off "
                    "multiprocessing by passing --serial")
        exe = find_prog("nice-plots")
        os.execve(exe, sys.argv, os.environ)

    LOGGER.info(f"Set configuration file path -> {config_path}")
    LOGGER.info(f"Set data file path(s) -> {data_path}")
    LOGGER.info(f"Set codebook file path -> {codebook_path}")

    # create cache directory
    cache_directory = os.path.expanduser("~/.cache/nice-plots")
    if (os.path.exists(cache_directory)) & (clear_cache):
        LOGGER.warning("RESETTING CACHE")
        os.rmdir(cache_directory)
    pathlib.Path(cache_directory).mkdir(parents=True, exist_ok=True)
    LOGGER.info(f"Using cache in: {cache_directory}")

    # create output directory
    output_directory = os.getcwd() + "/{}".format(output_name)
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
    LOGGER.info(f"Using output directory: {output_directory}")

    # Load config file
    LOGGER.info("Loading config file...")
    ctx = parser.load_config(config_path,
                             output_directory,
                             output_name)
    if isinstance(ctx, str):
        LOGGER.error(ctx)
        return
    ctx['format'] = format

    # Load codebook
    LOGGER.info("Loading codebook...")
    codebook = parser.load_codebook(ctx, codebook_path)
    if isinstance(codebook, str):
        LOGGER.error(codebook)
        return

    # Load data
    LOGGER.info("Loading data...")
    datas = {}
    for path, label in zip(data_path, time_labels):
        data = parser.load_data(ctx, path, codebook)
        if isinstance(data, str):
            LOGGER.error(data)
            return
        datas[label] = data

    # check the config file
    for data in datas.values():
        status = parser.check_config(ctx, codebook, data)
        if len(status) > 0:
            LOGGER.error(status)
            return

    LOGGER.info("Processing input data...")
    global_plotting_datas = {}
    for label, data in datas.items():
        global_plotting_datas[label] = process.process_data(data, codebook, ctx)
        if isinstance(global_plotting_datas[label], str):
            LOGGER.error(global_plotting_datas[label])
            return

    # number of question blocks -> number of plots
    n_blocks = len(global_plotting_datas[list(global_plotting_datas.keys())[0]])

    if plot_type != 'timeline':
        global_plotting_datas = global_plotting_datas[list(global_plotting_datas.keys())[0]]

    LOGGER.info("Producing plots...")
    if plot_type == 'bars':
        exec_func = getattr(barplot, 'plot_barplots')
    elif plot_type == 'lines':
        exec_func = getattr(lineplot, 'plot_lineplots')
    elif plot_type == 'histograms':
        exec_func = getattr(histogram, 'plot_histograms')
    elif plot_type == 'timeline':
        exec_func = getattr(timeline, 'plot_timelines')
    else:
        raise Exception(f"Plot type {plot_type} does not exist.")

    if not serial:
        LOGGER.debug("Running in parallel mode")
        LOGGER.warning("DEPRECATED")
        with Pool() as p:
            p.map(
                partial(exec_func, global_plotting_datas, ctx=ctx),
                list(range(len(global_plotting_datas))))
    else:
        LOGGER.debug("Running in serial mode")
        # loop over question blocks and produce one plot for each
        # question block
        for xx in tqdm(range(n_blocks)):
            exec_func(xx, global_plotting_datas, ctx)

    LOGGER.info("nice-plots finished without errors :)")


if __name__ == '__main__':
    main_cli()