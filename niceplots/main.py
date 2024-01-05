# Authors: Dominik Zuercher, Valeria Glauser

import os
import pathlib
from pathlib import Path
from typing import Tuple

import click
from tqdm import tqdm

from niceplots import barplot, histogram, lineplot, parser, process, timeline
from niceplots.utils.nice_logger import init_logger, set_logger_level


def main(
    config: Path,
    data: Tuple[Path],
    book: Path,
    name: str,
    type: str,
    format: str,
    clear_cache: bool,
    verbosity: str,
    time_labels: Tuple[str],
) -> None:
    logger = init_logger("niceplots")
    set_logger_level(logger, verbosity)

    logger.info("Starting nice-plots")

    if type == "timeline":
        if not len(time_labels) == len(data):
            raise Exception(
                "Can only make time series plot if same number "
                "of labels and data sets provided."
            )

    logger.info(f"Set configuration file path -> {config}")
    logger.info(f"Set data file path(s) -> {config}")
    logger.info(f"Set codebook file path -> {config}")

    # create cache directory
    cache_directory = os.path.expanduser("~/.cache/nice-plots")
    if (os.path.exists(cache_directory)) & clear_cache:
        logger.warning("RESETTING CACHE")
        os.rmdir(cache_directory)
    pathlib.Path(cache_directory).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using cache in: {cache_directory}")

    # create output directory
    output_directory = os.getcwd() + f"/{name}"
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using output directory: {output_directory}")

    # Load config file
    ctx = parser.load_config(config, output_directory, name)
    if isinstance(ctx, str):
        logger.error(ctx)
        return
    ctx["format"] = format
    logger.info("Loaded config file")

    # Load codebook
    codebook = parser.load_codebook(ctx, book)
    if isinstance(codebook, str):
        logger.error(codebook)
        return
    logger.info("Loaded codebook")

    # Load data
    datas = {}
    for path, label in zip(data, time_labels):
        d = parser.load_data(ctx, path, codebook)
        if isinstance(d, str):
            logger.error(d)
            return
        datas[label] = d
    logger.info("Loaded data")

    # check the config file
    for d in datas.values():
        status = parser.check_config(ctx, codebook, d)
        if len(status) > 0:
            logger.error(status)
            return

    logger.info("Preprocessing data")
    global_plotting_datas = {}
    for label, d in datas.items():
        global_plotting_datas[label] = process.process_data(d, codebook, ctx)
        if isinstance(global_plotting_datas[label], str):
            logger.error(global_plotting_datas[label])
            return

    # number of question blocks -> number of plots
    n_blocks = len(global_plotting_datas[list(global_plotting_datas.keys())[0]])

    if type != "timeline":
        global_plotting_datas = global_plotting_datas[
            list(global_plotting_datas.keys())[0]
        ]

    if type == "bars":
        exec_func = barplot.plot_barplots
    elif type == "lines":
        exec_func = lineplot.plot_lineplots
    elif type == "histograms":
        exec_func = histogram.plot_histograms
    elif type == "timeline":
        exec_func = timeline.plot_timelines
    else:
        raise Exception(f"Plot type {type} does not exist.")

    logger.info("Producing plots")
    # loop over question blocks and produce one plot for each
    for xx in tqdm(range(n_blocks)):
        exec_func(xx, global_plotting_datas, ctx)
    logger.info("nice-plots finished without errors :)")


@click.group()
def cli():
    pass


@cli.command(
    name="run", help="Nice-plots is a tool to quickly visualize QM survey data"
)
@click.option(
    "-c",
    "--config",
    required=True,
    type=click.Path(path_type=Path),
    help="Path to the nice-plots configuration file. See examples/example_config.yml for example.",
)
@click.option(
    "-d",
    "--data",
    required=True,
    multiple=True,
    type=click.Path(path_type=Path),
    help="Path to the data file, or list of such paths (in csv format)",
)
@click.option(
    "-b",
    "--book",
    required=True,
    type=click.Path(path_type=Path),
    help="Path to the codebook file (in csv format)",
)
@click.option(
    "-n",
    "--name",
    required=False,
    default="output1",
    type=str,
    help="Name prefix for output plots. Serves also as output directory name. NOTE: If there are configs and codebooks in the output directory they will be used instead of the global codebook and config files specified by the config_path and codebook_path arguments.",
)
@click.option(
    "-t",
    "--type",
    required=False,
    default="bars",
    type=click.Choice(["bars", "lines", "histograms", "timeline"]),
    help="Type of plots to produce. If type=timeline expects a list of data_paths and also time_labels",
)
@click.option(
    "-f",
    "--format",
    required=False,
    default="pdf",
    type=click.Choice(["pdf", "svg", "png"]),
    help="Format of the output plots.",
)
@click.option(
    "--clear_cache",
    required=False,
    is_flag=True,
    default=False,
    help="Reset cache directory before running.",
)
@click.option(
    "-v",
    "--verbosity",
    required=False,
    default="3",
    type=click.Choice(["1", "2", "3", "4"]),
    help="Verbosity level (1=error, 2=warning, 3=info, 4=debug). Defaults to 3.",
)
@click.option(
    "--time_labels",
    required=False,
    multiple=True,
    default=[""],
    help="Labels for the different data sets (only used if plot_type=timeline).",
)
def cli_main(
    config: Path,
    data: Tuple[Path],
    book: Path,
    name: str,
    type: str,
    format: str,
    clear_cache: bool,
    verbosity: str,
    time_labels: Tuple[str],
) -> None:
    main(config, data, book, name, type, format, clear_cache, verbosity, time_labels)


if __name__ == "__main__":
    cli()
