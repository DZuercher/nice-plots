# Authors: Dominik Zuercher, Valeria Glauser
import ast
from enum import Enum
from typing import Any

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from niceplots.utils.codebook import CodeBook
from niceplots.utils.config import Configuration
from niceplots.utils.data import Data, DataCollection
from niceplots.utils.nice_logger import init_logger
from niceplots.utils.plotting_utils import WrapText

logger = init_logger(__file__)

N_UNITS_LEGEND = 1
MARGIN_FACTOR = 1.1


class HistogramType(Enum):
    Single = 1
    Multi = 2
    Skip = 3


def plot_histograms(
    config: Configuration, codebook: CodeBook, data_collection: DataCollection
) -> None:
    for data_name in data_collection.data_object_names:
        data = getattr(data_collection, data_name)
        blocks = codebook.blocks[~np.isnan(codebook.blocks)]
        for block in blocks:
            plot_histogram(block, data, config, codebook)


def plot_histogram(
    block: int, data: Data, config: Configuration, codebook: CodeBook
) -> None:
    """
    HISTOGRAMS:
    If a question block contains only a single question plot a bar in a histogram for each answer (per group).
    If a question block contains multiple questions with 2 possible answers, interpret as binary (1=Yes, 0=No) and
    plot a bar in a histogram for each question (per group).

    A summary of the total number of participants that answered (n) and the number of participants that chose no answer (E)
    is provided.

    Y-Layout: The only physical size input for the vertical direction is the height of a single bar (height_bar, in inches).
    Additionally, height_rel_pad_questions controls the relative spacing between group bar bundles

    The physical height of the plot is calculated from the number of questions, groups,
    relative spacings and the desired physical size of the bars.

                       ---
                        |       _
                        |       | Bar for group 1, Question 1
                        |       -
                        |       |  Bar for group 2, Question 1
                        |       -
                        |
                        |         height_rel_pad_questions (relative spacing between bars between different questions)
                        |
                        |       _
                        |       | Bar for group 1, Question 2
                        |       -
                        |       |  Bar for group 2, Question 2
                        |       -
                        |
                       ---

    X-Layout: For each component of the histogram the physical width is
    required as an input in inches. The total physical width is the sum of all components.
    Text is wrapped automatically to the correct width.

        width_labels    width_pad    width_plot
    |                     | |                       |
    |                     | |                       |
    |                     | |                       |
    |                     | |                       |
    |                     | |                       |
    |                     | |                       |
    |                     | |                       |
    |                     | |                       |
    """
    # calculate some general properties that are constant within one block
    codebook_block = codebook.codebook[codebook.codebook.block == block]
    variables = codebook_block["variable"]
    n_variables = len(variables)
    groups = list(config.data.groups.keys())
    value_map = (
        None
        if codebook_block.iloc[0]["value_map"] == ""
        else ast.literal_eval(codebook_block.iloc[0]["value_map"])
    )
    # check if this kind of item can be made into a single histogram/multi-histogram
    hist_type = get_histogram_type(n_variables, value_map)

    if hist_type == HistogramType.Skip:
        return

    if hist_type == HistogramType.Single:
        n_bars = len(value_map.keys()) if value_map is not None else 0
    else:
        n_bars = n_variables

    fig, axes = get_layout(config, n_bars, N_UNITS_LEGEND, groups)
    geometry = get_geometry(config, groups)

    hist_data, hist_data_abs, n_answers, n_no_answers = get_histogram_data(
        hist_type, groups, value_map, data, codebook_block, n_variables
    )

    plot_bars(config, hist_data, geometry, axes, n_bars, groups)
    add_bar_label(fig, config, n_bars, axes, groups, hist_data, geometry, hist_data_abs)
    add_labels(codebook_block, value_map, hist_type, axes, n_bars, fig, config)
    add_summary(fig, axes, config, n_bars, groups, n_answers, n_no_answers)
    add_legend(axes[0], config, groups)

    # save plot
    fig.savefig(
        f"{config.output_directory}/{config.output_name}_histogram_{int(block)}.{config.plotting.format}",
        transparent=False,
        bbox_inches="tight",
    )
    plt.close()


def add_legend(ax: Axes, config: Configuration, groups: list[str]) -> None:
    if len(groups) > 0:
        patches = []
        for ii, group in enumerate(groups):
            if group == "nice_plots_default_group":
                continue
            patches.append(Patch(color=config.histograms.colors[ii], label=group))
        ax.legend(
            handles=patches,
            ncol=2,
            bbox_to_anchor=(0, 1),
            loc="lower left",
            frameon=False,
            prop=config.histograms.font_legend,
        )


def add_summary(
    fig: Figure,
    axes: list[Axes],
    config: Configuration,
    n_bars: int,
    groups: list[str],
    n_answers: int,
    n_no_answers: int,
) -> None:
    summary = WrapText(
        x=config.histograms.layout["width_labels"]
        + config.histograms.layout["width_pad"]
        + config.histograms.layout["width_plot"]
        - config.histograms.layout["width_summary"]
        - config.histograms.layout["pad_summary_right"],
        y=(
            n_bars
            * (len(groups) + config.histograms.layout["height_rel_pad_questions"])
        )
        * config.histograms.layout["height_bar"]
        - config.histograms.layout["pad_summary_top"],
        text=f"n = {int(n_answers)}\nE = {int(n_no_answers)}",
        horizontalalignment="left",
        verticalalignment="top",
        fontproperties=config.histograms.font_summary,
        x_units="inches",
        y_units="inches",
        width_units="inches",
        width=config.histograms.layout["width_summary"],
        figure=fig,
        ax=axes[0],
    )
    fig.add_artist(summary)


def add_labels(
    codebook: pd.DataFrame,
    value_map: Any | None,
    hist_type: HistogramType,
    axes: list[Axes],
    n_bars: int,
    fig: Figure,
    config: Configuration,
) -> None:
    if hist_type == HistogramType.Single:
        labels = list(value_map.values()) if value_map is not None else []
    else:
        labels = list(codebook.label)
    for id_v in range(n_bars):
        ax = axes[id_v]
        label = WrapText(
            x=config.histograms.layout["width_labels"],
            y=0.0,
            text=labels[id_v],
            horizontalalignment="right",
            verticalalignment="center",
            fontproperties=config.histograms.font_labels,
            x_units="inches",
            y_units="data",
            width_units="inches",
            width=config.histograms.layout["width_labels"],
            figure=fig,
            ax=ax,
        )
        fig.add_artist(label)


def add_bar_label(
    fig: Figure,
    config: Configuration,
    n_bars: int,
    axes: list[Axes],
    groups: list[str],
    hist_data: dict,
    geometry: dict,
    hist_data_abs: dict,
) -> None:
    for id_v in range(n_bars):
        ax = axes[id_v]
        for id_g, group in enumerate(groups):
            bar_label = WrapText(
                x=hist_data[group][id_v] + config.histograms.layout["bar_label_pad"],
                y=geometry["central_bar_positions"][id_g],
                text=str(int(hist_data_abs[group][id_v])),
                horizontalalignment="left",
                verticalalignment="center",
                fontproperties=config.histograms.font_bar_labels,
                x_units="data",
                y_units="data",
                width_units="inches",
                width=10,  # no wrap
                figure=fig,
                ax=ax,
            )
            fig.add_artist(bar_label)


def plot_bars(
    config: Configuration,
    hist_data: dict,
    geometry: dict,
    axes: list[Axes],
    n_bars: int,
    groups: list[str],
) -> None:
    for id_v in range(n_bars):
        ax = axes[id_v]
        for id_g, group in enumerate(groups):
            ax.barh(
                geometry["central_bar_positions"][id_g],
                hist_data[group][id_v],
                height=geometry["rel_bar_height"],
                color=config.histograms.colors[id_g],
            )


def get_geometry(config: Configuration, groups: list[str]) -> dict:
    geometry = {}
    n_groups = len(groups)
    rel_bar_height = (
        1.0 - config.histograms.layout["height_rel_pad_questions"]
    ) / n_groups
    geometry["rel_bar_height"] = rel_bar_height
    if n_groups % 2 == 0:
        # even number of bars
        positions = 0.5 * rel_bar_height + rel_bar_height * np.arange(n_groups / 2)
        positions = np.append(positions, -1.0 * positions)
    else:
        # uneven number of bars
        positions = np.arange((n_groups - 1) / 2) * rel_bar_height
        positions = np.append(positions, -1.0 * positions)
        positions = np.append(0, positions)

    geometry["central_bar_positions"] = positions
    return geometry


def get_histogram_data(
    hist_type: HistogramType,
    groups: list[str],
    value_map: Any | None,
    data: Data,
    codebook: pd.DataFrame,
    n_variables: int,
) -> tuple[dict, dict, int, int]:
    no_answer_code = data.no_answer_code
    max_value = 0

    hist_data_abs: dict = {}

    # get total number of answers
    code = codebook.iloc[0]
    variable = code["variable"]
    d = data.data[variable]
    # drop nans
    d = d[~d.isna()]
    n_no_answers = (d == no_answer_code).sum()
    n_answers = ((d != no_answer_code) & (d != code.missing_label)).sum()

    if hist_type == HistogramType.Single:
        for group in groups:
            d = data.data[data.data["nice_plots_group"] == group]
            hist_data_abs[group] = []

            code = codebook.iloc[0]
            variable = code["variable"]
            d = d[variable]
            # drop nans
            d = d[~d.isna()]
            # drop no answers
            d = d[~(d == no_answer_code)]
            # drop missing answers
            d = d[~(d == code.missing_label)]
            for key in list(value_map.keys() if value_map is not None else []):
                n = (d == key).sum()
                hist_data_abs[group].append(n)
                max_value = max(n, max_value)
    else:
        for group in groups:
            data_group = data.data[data.data["nice_plots_group"] == group]
            hist_data_abs[group] = []
            for id_v in range(n_variables):
                code = codebook.iloc[id_v]
                variable = code["variable"]
                d = data_group[variable]
                # drop nans
                d = d[~d.isna()]
                # drop no answers
                d = d[~(d == no_answer_code)]
                # drop missing answers
                d = d[~(d == code.missing_label)]
                # count number of Yes (1=Yes, 0=No)
                n = d.sum()
                hist_data_abs[group].append(n)
                max_value = max(n, max_value)

    # normalize
    hist_data = {}
    # add margin
    max_value = int(max_value * MARGIN_FACTOR)
    for group in groups:
        hist_data[group] = [n / max_value for n in hist_data_abs[group]]
    return hist_data, hist_data_abs, n_answers, n_no_answers


def get_layout(
    config: Configuration, n_bars: int, n_units_legend: int, groups
) -> tuple[Figure, list[Axes]]:
    # calculate figuresize and get figure
    fig_width = (
        config.histograms.layout["width_labels"]
        + config.histograms.layout["width_plot"]
        + config.histograms.layout["width_pad"]
    )

    fig_height = (
        (n_bars + n_units_legend)
        * (len(groups) + config.histograms.layout["height_rel_pad_questions"])
    ) * config.histograms.layout["height_bar"]
    fig = plt.figure(figsize=(fig_width, fig_height))

    # setup grid layout
    grid = gridspec.GridSpec(
        nrows=n_bars,
        ncols=1,
        wspace=0.0,
        hspace=0.0,
        left=(
            config.histograms.layout["width_labels"]
            + config.histograms.layout["width_pad"]
        )
        / fig_width,
        right=(
            config.histograms.layout["width_labels"]
            + config.histograms.layout["width_plot"]
            + config.histograms.layout["width_pad"]
        )
        / fig_width,
        top=(
            n_bars
            * (len(groups) + config.histograms.layout["height_rel_pad_questions"])
        )
        * config.histograms.layout["height_bar"]
        / fig_height,
        bottom=0.0,
        figure=fig,
    )

    # add Axes subplots
    axes = []
    for id_v in range(n_bars):
        ax = fig.add_subplot(grid[id_v])
        if (id_v == 0) & (id_v == (n_bars - 1)):
            ax.spines["top"].set_visible(True)
            ax.spines["left"].set_visible(True)
            ax.spines["right"].set_visible(True)
            ax.spines["bottom"].set_visible(True)
        elif id_v == 0:
            ax.spines["top"].set_visible(True)
            ax.spines["left"].set_visible(True)
            ax.spines["right"].set_visible(True)
            ax.spines["bottom"].set_visible(False)
        elif id_v == (n_bars - 1):
            ax.spines["top"].set_visible(False)
            ax.spines["left"].set_visible(True)
            ax.spines["right"].set_visible(True)
            ax.spines["bottom"].set_visible(True)
        else:
            ax.spines["top"].set_visible(False)
            ax.spines["left"].set_visible(True)
            ax.spines["right"].set_visible(True)
            ax.spines["bottom"].set_visible(False)

        # formatting
        ax.tick_params(
            axis="both",
            which="both",
            bottom=False,
            labelbottom=False,
            left=False,
            labelleft=False,
        )
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([-0.5, 0.5])
        axes.append(ax)
    return fig, axes


def get_histogram_type(n_variables: int, value_map: Any | None) -> HistogramType:
    """Determine if the given data can be used to
    construct a single histogram or a binary histogram
    """
    if value_map is None:
        logger.debug("Cannot produce histogram for value map = None. Skipping...")
        hist_type = HistogramType.Skip
    elif n_variables == 1:
        hist_type = HistogramType.Single
        logger.info(
            "Question block contains only a single question "
            "-> Producing a single histogram for this."
        )
    else:
        if len(value_map.keys()) == 2:
            hist_type = HistogramType.Multi
            logger.info(
                "Question block contains multiple questions "
                "with 2 possible answers each"
                "-> Interpreting as Yes/No questions and combining "
                "into a single histogram."
            )
        else:
            logger.debug("Cannot convert question block into a histogram. Skipping...")
            hist_type = HistogramType.Skip

    return hist_type
