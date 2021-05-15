# Authors: Dominik Zuercher, Valeria Glauser

from niceplots import parser
from niceplots import process
from niceplots import plotting
from niceplots import lineplot
from niceplots import utils
import os
import pathlib
import argparse

LOGGER = utils.init_logger(__file__)


def main():
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
    cli_args.add_argument('--debug', action='store_true',
                          default=False, help='Debug mode')

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
    ctx['debug'] = ARGS.debug

    codebook = parser.load_codebook(ctx, ARGS.codebook_path)

    data = parser.load_data(ctx, ARGS.data_path)

    plotting_data = process.process_data(data, codebook, ctx)
    if ARGS.plot_type == 'bars':
        plotting.make_plots(plotting_data, ctx)
    elif ARGS.plot_type == 'lines':
        lineplot.make_plots(plotting_data, ctx)
    else:
        raise Exception(f"Plotting type {ARGS.plot_type} does not exist.")

    LOGGER.info("nice-plots finished without errors :)")


if __name__ == '__main__':
    main()
