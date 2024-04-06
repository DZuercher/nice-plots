# Authors: Dominik Zuercher, Valeria Glauser
import ast
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

N_UNITS_LEGEND = 2


def plot_lineplots(
    config: Configuration, codebook: CodeBook, data_collection: DataCollection
) -> None:
    for data_name in data_collection.data_object_names:
        data = getattr(data_collection, data_name)
        blocks = codebook.blocks[~np.isnan(codebook.blocks)]
        for block in blocks:
            plot_lineplot(block, data, config, codebook)


def plot_lineplot(
    block: int, data: Data, config: Configuration, codebook: CodeBook
) -> None:
    """
    LINEPLOTS:
    For each question a linegrid is plotted. The mean of each group is indicated by a cross.

    Y-Layout: The only physical size input for the vertical direction is the height of one question lineplot unit
    (height_question, in inches). The spacing between questions is controlled by rel_edge_line_height.
    Concretely, the parameter controls the height of the vertical bars
    (1 = bars will just touch each other, 0= no vertical bars).

    The physical height of the plot is calculated from the number of questions, groups,
    relative spacings and the desired physical size of the bars.

    For the legend at the top 2 * height_question is allocated.

                       ---
                        |       _
    height_question     |       | Linegrid Question 1
                        |       -
                       ---     rel_edge_line_height (relative spacing between linegrids of different questions)
                        |       _
    height_question     |       | Linegrid Question 2
                        |       -
                       ---

    X-Layout: For each component of the lineplot (question label, edge label, etc.) the physical width is
    required as an input in inches. The total physical width is the sum of all components.

    Text is wrapped automatically to the correct width.

      width_question   width_pad  width_labels  width_pad    width_plot   width_pad  width_labels
    |                     | |                     | |                       |  |                    |
    |                     | |                     | |                       |  |                    |
    |                     | |                     | |                       |  |                    |
    |                     | |                     | |                       |  |                    |
    |                     | |                     | |                       |  |                    |
    |                     | |                     | |                       |  |                    |
    |                     | |                     | |                       |  |                    |
    |                     | |                     | |                       |  |                    |


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

    fig, axes = get_layout(config, n_variables, N_UNITS_LEGEND)

    min_value, max_value, min_label, max_label = plot_line_grid(
        n_variables, codebook_block, data, axes, config, value_map
    )
    plot_crosses(
        groups, n_variables, codebook_block, data, axes, config, min_value, max_value
    )

    add_question_labels(fig, config, codebook_block, n_variables, N_UNITS_LEGEND)
    add_edge_labels(fig, config, n_variables, N_UNITS_LEGEND, min_label, max_label)
    add_legend(axes[0], config, groups)

    # save plot
    fig.savefig(
        f"{config.output_directory}/{config.output_name}_lineplot_{int(block)}.{config.plotting.format}",
        transparent=False,
        bbox_inches="tight",
    )
    plt.close()


def add_question_labels(
    fig: Figure,
    config: Configuration,
    codebook_block: pd.DataFrame,
    n_variables: int,
    n_units_legend: int,
) -> None:
    height_question_figure = 1.0 / (n_variables + n_units_legend)
    for id_v, question in enumerate(codebook_block.label):
        center_position_question = (0.5 + id_v) * height_question_figure
        question_label = WrapText(
            x=0.0,
            y=center_position_question,
            text=question,
            horizontalalignment="left",
            verticalalignment="center",
            fontproperties=config.lineplots.font_questions,
            x_units="inches",
            y_units="figure",
            width_units="inches",
            width=config.lineplots.layout["width_question"],
            figure=fig,
        )
        fig.add_artist(question_label)


def add_edge_labels(
    fig: Figure,
    config: Configuration,
    n_variables: int,
    n_units_legend: int,
    min_label,
    max_label,
) -> None:
    min_label_plot = max_label if config.lineplots.invert else min_label
    max_label_plot = min_label if config.lineplots.invert else max_label

    height_question_figure = 1.0 / (n_variables + n_units_legend)
    for id_v in range(n_variables):
        center_position_question = (0.5 + id_v) * height_question_figure
        edge_label = WrapText(
            x=config.lineplots.layout["width_question"]
            + config.lineplots.layout["width_labels"]
            + config.lineplots.layout["width_pad"],
            y=center_position_question,
            text=min_label_plot,
            horizontalalignment="right",
            verticalalignment="center",
            fontproperties=config.lineplots.font_labels,
            x_units="inches",
            y_units="figure",
            width_units="inches",
            width=config.lineplots.layout["width_labels"],
            figure=fig,
        )
        fig.add_artist(edge_label)

        edge_label = WrapText(
            x=config.lineplots.layout["width_question"]
            + config.lineplots.layout["width_labels"]
            + 3 * config.lineplots.layout["width_pad"]
            + config.lineplots.layout["width_plot"],
            y=center_position_question,
            text=max_label_plot,
            horizontalalignment="left",
            verticalalignment="center",
            fontproperties=config.lineplots.font_labels,
            x_units="inches",
            y_units="figure",
            width_units="inches",
            width=config.lineplots.layout["width_labels"],
            figure=fig,
        )
        fig.add_artist(edge_label)


def plot_line_grid(
    n_variables: int,
    codebook: pd.DataFrame,
    data: Data,
    axes: list[Axes],
    config: Configuration,
    value_map: Any | None,
) -> tuple[int, int, str, str]:
    no_answer_code = data.no_answer_code

    min_value = 1000000
    max_value = -1000000

    # horizontal central lines
    for ax in axes:
        ax.hlines(0, xmin=0, xmax=1, color="k", lw=3)

    # vertical separation lines
    if value_map is None:
        # assume numeric values
        # get min max range
        for id_v in range(n_variables):
            code = codebook.iloc[id_v]
            variable = code["variable"]
            d = data.data[variable]
            # drop nans
            d = d[~d.isna()]
            # drop missing answers
            d = d[~(d == no_answer_code)]
            min_value = min(d.min(), min_value)
            max_value = max(d.max(), max_value)
        min_label = str(int(min_value))
        max_label = str(int(max_value))

        # no mapping provided (assume numeric values)
        n_bins = config.plotting.nbins
    else:
        n_bins = len(value_map.keys())
        min_value = list(value_map.keys())[0]
        max_value = list(value_map.keys())[-1]
        min_label = str(list(value_map.values())[0])
        max_label = str(list(value_map.values())[-1])
    for ax in axes:
        ax.vlines(
            np.linspace(0, 1, n_bins),
            ymin=-config.lineplots.layout["rel_edge_line_height"] / 2.0,
            ymax=config.lineplots.layout["rel_edge_line_height"] / 2.0,
            color="k",
            lw=3,
            clip_on=False,
        )
    return min_value, max_value, min_label, max_label


def plot_crosses(
    groups: list[str],
    n_variables: int,
    codebook: pd.DataFrame,
    data: Data,
    axes: list[Axes],
    config: Configuration,
    min_value: int,
    max_value: int,
) -> None:
    no_answer_code = data.no_answer_code

    # prep data (get means for each question/group)
    plotting_data: dict = {}
    for group in groups:
        data_group = data.data[data.data["nice_plots_group"] == group]
        plotting_data[group] = []
        for id_v in range(n_variables):
            code = codebook.iloc[id_v]
            variable = code["variable"]
            d = data_group[variable]

            # drop nans
            d = d[~d.isna()]
            # drop missing answers
            d = d[~(d == code.missing_label)]
            # drop no answer
            d = d[~(d == no_answer_code)]
            mean = np.mean(d)
            # normalize to 0-1 scale
            mean = (mean - min_value) / (max_value - min_value)

            if config.lineplots.invert:
                mean = 1.0 - mean

            plotting_data[group].append(mean)

    for id_g, group in enumerate(groups):
        for id_v in range(n_variables):
            ax = axes[id_v]

            # add X marker
            ax.plot(
                plotting_data[group][id_v],
                0,
                marker="X",
                markersize=20,
                color=config.lineplots.colors[id_g],
                lw=3,
                clip_on=False,
            )

            # add connecting line upwards
            if id_v > 0:
                ax.plot(
                    [plotting_data[group][id_v], plotting_data[group][id_v - 1]],
                    [0, 1],
                    color=config.lineplots.colors[id_g],
                    lw=3,
                    clip_on=False,
                )

            # add connecting line downwards
            if id_v < n_variables - 1:
                ax.plot(
                    [plotting_data[group][id_v], plotting_data[group][id_v + 1]],
                    [0, -1],
                    color=config.lineplots.colors[id_g],
                    lw=3,
                    clip_on=False,
                )


def get_layout(
    config: Configuration, n_variables: int, n_units_legend: int
) -> tuple[Figure, list[Axes]]:
    # calculate figuresize and get figure
    fig_width = (
        config.lineplots.layout["width_question"]
        + 2 * config.lineplots.layout["width_labels"]
        + config.lineplots.layout["width_plot"]
        + 3 * config.lineplots.layout["width_pad"]
    )

    fig_height = (n_variables + n_units_legend) * config.lineplots.layout[
        "height_question"
    ]
    fig = plt.figure(figsize=(fig_width, fig_height))

    # setup grid layout
    grid = gridspec.GridSpec(
        nrows=n_variables,
        ncols=1,
        wspace=0.0,
        hspace=0.0,
        left=(
            config.lineplots.layout["width_question"]
            + config.lineplots.layout["width_labels"]
            + 2 * config.lineplots.layout["width_pad"]
        )
        / fig_width,
        right=(
            config.lineplots.layout["width_question"]
            + config.lineplots.layout["width_labels"]
            + config.lineplots.layout["width_plot"]
            + 2 * config.lineplots.layout["width_pad"]
        )
        / fig_width,
        top=n_variables / (n_variables + n_units_legend),
        bottom=0.0,
        figure=fig,
    )

    # add Axes subplots
    axes = []
    for id_v in range(n_variables):
        ax = fig.add_subplot(grid[id_v], frameon=False)

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


def add_legend(ax, config, groups) -> None:
    if len(groups) > 0:
        patches = []
        for ii, group in enumerate(groups):
            if group == "nice_plots_default_group":
                continue
            patches.append(Patch(color=config.lineplots.colors[ii], label=group))
        ax.legend(
            handles=patches,
            ncol=2,
            bbox_to_anchor=(0, 1),
            loc="lower left",
            frameon=False,
            prop=config.lineplots.font_legend,
        )
