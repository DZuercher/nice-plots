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
from multiprocessing import Pool
from functools import partial


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


LOGGER = utils.init_logger(__file__)


def main():
    description = "Nice plots allows you to (hopefully) easily and automatic "\
        "plots of your survey data."
    cli_args = argparse.ArgumentParser(description=description, add_help=True)
    cli_args.add_argument('--config_path', type=str, action='store',
                          default='example_config.yml',
                          help='Valid path to the configuration file')
    cli_args.add_argument('--data_path', type=str, nargs='+', action='store',
                          default=['example_data.csv'],
                          help='Valid path to the data file, or list of such paths')
    cli_args.add_argument('--time_labels', type=str, nargs='*', default=[''], action='store',
                          help='Labels for the different data sets (only if timeline).')
    cli_args.add_argument('--codebook_path', type=str, action='store',
                          default='example_codebook.csv',
                          help='Valid path to the codebook file')
    cli_args.add_argument('--output_name', type=str, action='store',
                          default='output1',
                          help="Name prefix for output plots. Serves also as "
                          "output directory name. NOTEL If there are configs "
                          "and codebooks in the output directory they will be "
                          "used instead of the codebook and config file "
                          "specified by the CLI.")
    cli_args.add_argument('--plot_type', type=str, action='store',
                          default='bars', choices=['bars', 'lines',
                                                   'histograms', 'timeline'],
                          help='Type of plots to produce. '
                          'If timeline expects a list of data_paths and also time_labels')
    cli_args.add_argument('--serial', action='store_true',
                          default=True,
                          help='If True nice-plots runs in serial mode '
                          'instead of parallel (parallel only works on Linux). Parallel mode is deprecated.')
    cli_args.add_argument('--format', type=str, action='store',
                          default='pdf', choices=['pdf', 'svg', 'png'],
                          help='Format of the output plots.')

    LOGGER.info("Starting nice-plots")

    ARGS = cli_args.parse_args()

    if ARGS.plot_type == 'timeline':
        if not len(ARGS.time_labels) == len(ARGS.data_path):
            raise Exception(
                "Can only make time series plot if same number "
                "of labels and data sets provided.")

    LOGGER.info("CLI arguments parsed")

    if not ARGS.serial:
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

    LOGGER.info(f"Set configuration file path -> {ARGS.config_path}")
    LOGGER.info(f"Set data file path -> {ARGS.data_path}")
    LOGGER.info(f"Set codebook file path -> {ARGS.codebook_path}")

    # create cache directory
    cache_directory = os.path.expanduser("~/.cache/nice-plots")
    pathlib.Path(cache_directory).mkdir(parents=True, exist_ok=True)

    # create output directory
    output_directory = os.getcwd() + "/{}".format(ARGS.output_name)
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
    LOGGER.info(f"Setting output directory to {output_directory}")

    ctx = parser.load_config(ARGS.config_path,
                             output_directory,
                             ARGS.output_name)
    if isinstance(ctx, str):
        LOGGER.error(ctx)
        return

    ctx['format'] = ARGS.format

    LOGGER.info("Loading codebook...")
    codebook = parser.load_codebook(ctx, ARGS.codebook_path)
    if isinstance(codebook, str):
        LOGGER.error(codebook)
        return

    LOGGER.info("Loading data...")
    datas = {}
    for path, label in zip(ARGS.data_path, ARGS.time_labels):
        data = parser.load_data(ctx, path, codebook)
        if isinstance(data, str):
            LOGGER.error(data)
            return
        datas[label] = data

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

    n_blocks = len(global_plotting_datas[list(global_plotting_datas.keys())[0]])

    if ARGS.plot_type != 'timeline':
        global_plotting_datas = global_plotting_datas[list(global_plotting_datas.keys())[0]]

    LOGGER.info("Producing your plots please wait...")
    if ARGS.plot_type == 'bars':
        exec_func = getattr(barplot, 'plot_barplots')
    elif ARGS.plot_type == 'lines':
        exec_func = getattr(lineplot, 'plot_lineplots')
    elif ARGS.plot_type == 'histograms':
        exec_func = getattr(histogram, 'plot_histograms')
    elif ARGS.plot_type == 'timeline':
        exec_func = getattr(timeline, 'plot_timelines')
    else:
        raise Exception(f"Plot type {ARGS.plot_type} does not exist.")

    if not ARGS.serial:
        LOGGER.info("Running in parallel mode")
        LOGGER.warning("DEPRECATED")
        with Pool() as p:
            p.map(
                partial(exec_func, global_plotting_datas, ctx=ctx),
                list(range(len(global_plotting_datas))))
    else:
        LOGGER.info("Running in serial mode")
        # loop over question blocks and produce one plot for each
        # question block
        for xx in tqdm(range(n_blocks)):
            exec_func(xx, global_plotting_datas, ctx)

    LOGGER.info("nice-plots finished without errors :)")


if __name__ == '__main__':
    main()