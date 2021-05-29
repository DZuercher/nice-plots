# Authors: Dominik Zuercher, Valeria Glauser

from niceplots import parser
from niceplots import process
from niceplots import barplot
from niceplots import lineplot
from niceplots import utils
import os
import sys
import pathlib
import argparse
import platform
import subprocess


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
        rc = p.returncode
        return output.decode('utf-8').rstrip()


LOGGER = utils.init_logger(__file__)


def main():
    # For OSX > High Sierra disable additional security features that prevent
    # multithreading
    if os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] != 'YES':
        os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
        exe = find_prog("nice-plots")
        os.execve(exe, sys.argv, os.environ)

    description = "Nice plots allows you to (hopefully) easily and automatic "\
        "plots of your survey data."
    cli_args = argparse.ArgumentParser(description=description, add_help=True)
    cli_args.add_argument('--config_path', type=str, action='store',
                          default='example_config.yml',
                          help='Valid path to the configuration file')
    cli_args.add_argument('--data_path', type=str, action='store',
                          default='example_data.csv',
                          help='Valid path to the data file')
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
                          default='bars', choices=['bars', 'lines'],
                          help='Type of plots to produce')
    cli_args.add_argument('--parallel', action='store_true',
                          default=True,
                          help='If True nice-plots runs in parallel')

    LOGGER.info("Starting nice-plots")

    ARGS = cli_args.parse_args()
    LOGGER.info("CLI arguments parsed")
    LOGGER.info(f"Set configuration file path -> {ARGS.config_path}")
    LOGGER.info(f"Set data file path -> {ARGS.data_path}")
    LOGGER.info(f"Set codebook file path -> {ARGS.codebook_path}")

    # create output directory
    output_directory = os.getcwd() + "/{}".format(ARGS.output_name)
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
    LOGGER.info(f"Setting output directory to {output_directory}")

    ctx = parser.load_config(ARGS.config_path,
                             output_directory,
                             ARGS.output_name)

    LOGGER.info("Loading codebook...")
    codebook = parser.load_codebook(ctx, ARGS.codebook_path)

    LOGGER.info("Loading data...")
    data = parser.load_data(ctx, ARGS.data_path, codebook)

    parser.check_config(ctx, codebook, data)

    LOGGER.info("Processing input data...")
    plotting_data = process.process_data(data, codebook, ctx)

    LOGGER.info("Producing your plots please wait...")
    if ARGS.plot_type == 'bars':
        barplot.make_plots(plotting_data, ctx, ARGS.parallel)
    elif ARGS.plot_type == 'lines':
        lineplot.make_plots(plotting_data, ctx, ARGS.parallel)
    else:
        raise Exception(f"Plotting type {ARGS.plot_type} does not exist.")

    LOGGER.info("nice-plots finished without errors :)")


if __name__ == '__main__':
    main()
