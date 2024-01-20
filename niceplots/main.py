# Authors: Dominik Zuercher, Valeria Glauser
import os
from pathlib import Path
from typing import Tuple

import click
from tqdm import tqdm

from niceplots.utils.codebook import setup_codebook
from niceplots.utils.config import setup_config
from niceplots.utils.data import setup_data
from niceplots.utils.nice_logger import init_logger, set_logger_level

logger = init_logger(__file__)


def check_arguments(data_paths: Tuple[Path], data_labels: Tuple[str]) -> None:
    if len(data_labels) != len(data_paths):
        raise Exception(
            "Can only make time series plot if same number "
            "of labels and data sets provided."
        )

    for label in data_labels:
        if len(label) < 1:
            raise ValueError(
                f"All data_labels must have at least one character: {label} is too short."
            )


def main(
    data_paths: Tuple[Path],
    codebook_path: Path,
    config_path: Path,
    name: str,
    plot_type: Tuple[str],
    output_format: str,
    clear_cache: bool,
    verbosity: str,
    data_labels: Tuple[str],
    prefix: Path,
    full_rerun: bool,
) -> None:
    set_logger_level(logger, verbosity)
    logger.info("Starting nice-plots")

    check_arguments(data_paths, data_labels)

    logger.info(f"Set configuration file path -> {config_path}")
    logger.info(f"Set data file path(s) -> {config_path}")
    logger.info(f"Set codebook file path -> {config_path}")

    config = setup_config(
        prefix,
        config_path,
        name,
        verbosity,
        output_format,
        clear_cache,
        write_config=True,
        full_rerun=full_rerun,
    )

    # Load codebook
    codebook = setup_codebook(
        config, codebook_path, write_codebook=True, full_rerun=full_rerun
    )

    data_collection = setup_data(
        config,
        codebook,
        data_paths,
        data_labels,
        write_data=True,
        full_rerun=full_rerun,
    )

    plot_types = set()
    for pt in plot_type:
        if pt == "all":
            plot_types.add("barplots")
            plot_types.add("lineplots")
            plot_types.add("histograms")
            plot_types.add("timelines")
        elif pt == "barplots":
            plot_types.add("barplots")
        elif pt == "barplots":
            plot_types.add("lineplots")
        elif pt == "barplots":
            plot_types.add("histograms")
        elif pt == "barplots":
            plot_types.add("timelines")
        else:
            raise ValueError(f"Plot type {pt} is unknown")

    logger.info("Producing plots")
    for pt in plot_types:
        if plot_type == "bars":
            exec_func = barplots.plot_barplots
        elif plot_type == "lines":
            exec_func = lineplots.plot_lineplots
        elif plot_type == "histograms":
            exec_func = histograms.plot_histograms
        elif plot_type == "timelines":
            exec_func = timelines.plot_timelines
        else:
            raise Exception(f"Plot type {plot_type} does not exist.")

        logger.info(f"Producing plots of type {pt}")
        for xx in tqdm.tqdm(range(codebook.codebook.n_blocks)):
            # NOTE: all logging must write using tqdm.write()
            exec_func(xx, config, codebook, data_collection)
    logger.info("nice-plots finished without errors :)")


@click.group()
def cli():
    pass


@cli.command(
    name="run", help="Nice-plots is a tool to quickly visualize QM survey data"
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
    "--codebook",
    required=True,
    type=click.Path(path_type=Path),
    help="Path to the codebook file (in csv format)",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(path_type=Path),
    help="Path to the nice-plots configuration file. See examples/example_config.yml for example.",
)
@click.option(
    "-n",
    "--name",
    required=False,
    default="output1",
    type=str,
    help="Name for output plots. Serves also as output directory name. NOTE: If there are configs and codebooks in the output directory they will be used instead of the global codebook and config files specified by the config_path and codebook_path arguments.",
)
@click.option(
    "-t",
    "--plot_type",
    required=False,
    default=["all"],
    type=click.Choice(["bars", "lines", "histograms", "timelines", "all"]),
    multiple=True,
    help="Type of plots to produce. If type=timeline expects a list of data_paths and also time_labels",
)
@click.option(
    "-f",
    "--output_format",
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
    "--data_labels",
    required=False,
    multiple=True,
    default=["data"],
    help="Labels for the different data sets (only used if plot_type=timeline).",
)
@click.option(
    "-p",
    "--prefix",
    type=click.Path(path_type=Path),
    default=os.getcwd(),
    help="Location in which nice-plot output directories are written. Default is CWD.",
)
@click.option(
    "--full_rerun",
    type=bool,
    default=False,
    help="Ignore config, codebook and data files in target destination and directly use supplied files.",
)
def cli_main(
    data: Tuple[Path],
    codebook: Path,
    config: Path,
    name: str,
    plot_type: Tuple[str],
    output_format: str,
    clear_cache: bool,
    verbosity: str,
    data_labels: Tuple[str],
    prefix: Path,
    full_rerun: bool,
) -> None:
    main(
        data,
        codebook,
        config,
        name,
        plot_type,
        output_format,
        clear_cache,
        verbosity,
        data_labels,
        prefix,
        full_rerun,
    )


if __name__ == "__main__":
    cli()
