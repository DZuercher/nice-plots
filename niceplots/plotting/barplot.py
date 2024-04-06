# Authors: Dominik Zuercher, Valeria Glauser
import ast
from typing import Any

import matplotlib as mpl
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

WIDTH_COLORBAR_REL = 0.5
HEIGHT_COLORBAR_REL = 0.2
# add units for legend (increase if legend is too large)
N_UNITS_LEGEND = 2


def plot_barplots(
    config: Configuration, codebook: CodeBook, data_collection: DataCollection
) -> None:
    for data_name in data_collection.data_object_names:
        data = getattr(data_collection, data_name)
        blocks = codebook.blocks[~np.isnan(codebook.blocks)]
        for block in blocks:
            plot_barplot(block, data, config, codebook)


def plot_barplot(
    block: int, data: Data, config: Configuration, codebook: CodeBook
) -> None:
    """
    BARPLOTS:
    For each question and group plot a horizontal bar. Each segment of the bar corresponds one answer and its width
    represents the relative amount of people that chose this answer.

    For each question a short statistics summary is added.

    Y-Layout: The only physical size input for the vertical direction is the height of one question barplot unit
    (height_question, in inches).


    The physical height of the plot is calculated from the number of questions, groups,
    relative spacings and the desired physical size of the bars.

    For the legend at the top 2 * height_question is allocated.

                       ---
                        |       _
                        |       | Bar for group 1, Question 1
                        |       -
    height_question     |      height_rel_pad_groups (relative spacing between bars within a question)
                        |       _
                        |       |  Bar for group 2, Question 1
                        |       -
                        |
                       ---     height_rel_pad_questions (relative spacing between bars between different questions)
                        |       _
                        |       | Bar for group 1, Question 2
                        |       -
    height_question     |      height_rel_pad_groups (relative spacing between bars within a question)
                        |       _
                        |       |  Bar for group 2, Question 2
                        |       -
                        |
                       ---

    X-Layout: For each component of the barplot (question label, group label, etc.) the physical width is
    required as an input in inches. The total physical width is the sum of all components.

    Text is wrapped automatically to the correct width.

      width_question   width_pad  width_groups  width_pad    width_plot   width_pad  width_summary
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
    text_color = codebook_block.iloc[0]["barplots.text_color"]
    value_map = (
        None
        if codebook_block.iloc[0]["value_map"] == ""
        else ast.literal_eval(codebook_block.iloc[0]["value_map"])
    )
    color_scheme = codebook_block.iloc[0]["barplots.color_scheme"]
    invert = codebook_block.iloc[0]["barplots.invert"]

    fig, axes = get_layout(config, n_variables, N_UNITS_LEGEND)
    geometry = get_geometry(config, groups)

    histograms, min_value, max_value = get_histograms(
        config, groups, codebook_block, data, n_variables, value_map
    )
    colors = get_colors(config, value_map, color_scheme, invert)

    add_bars(
        n_variables, axes, config, groups, geometry, histograms, colors, text_color
    )
    add_question_labels(fig, config, codebook_block, n_variables, N_UNITS_LEGEND)
    add_group_labels(fig, axes, groups, geometry, config)
    add_question_summaries(fig, config, data, codebook_block, axes, groups, geometry)
    add_legend(
        fig,
        axes[0],
        config,
        colors,
        value_map,
        min_value,
        max_value,
        n_variables,
        N_UNITS_LEGEND,
    )

    # save plot
    fig.savefig(
        f"{config.output_directory}/{config.output_name}_barplot_{int(block)}.{config.plotting.format}",
        transparent=False,
        bbox_inches="tight",
    )
    plt.close()


def add_group_labels(
    fig: Figure,
    axes: list[Axes],
    groups: list[str],
    geometry: dict,
    config: Configuration,
) -> None:
    for ax in axes:
        for id_g, group in enumerate(groups):
            if group == "nice_plots_default_group":
                continue
            group_label = WrapText(
                x=config.barplots.layout["width_question"]
                + config.barplots.layout["width_groups"]
                + config.barplots.layout["width_pad"],
                y=geometry["central_bar_positions"][id_g],
                text=group,
                horizontalalignment="right",
                verticalalignment="center",
                fontproperties=config.barplots.font_groups,
                x_units="inches",
                y_units="data",
                width_units="inches",
                width=config.barplots.layout["width_groups"],
                figure=fig,
                ax=ax,
            )
            fig.add_artist(group_label)


def add_question_summaries(
    fig: Figure,
    config: Configuration,
    data: Data,
    codebook_block: pd.DataFrame,
    axes: list[Axes],
    groups: list[str],
    geometry: dict,
) -> None:
    no_answer_code = data.no_answer_code

    for id_v, ax in enumerate(axes):
        for id_g, group in enumerate(groups):
            code = codebook_block.iloc[id_v]
            variable = code["variable"]

            d = data.data[data.data["nice_plots_group"] == group]
            d = d[variable]

            # drop nans
            d = d[~d.isna()]
            # drop missing answers
            d = d[~(d == code.missing_label)]

            summary = get_summary(d, no_answer_code)

            question_label = WrapText(
                x=config.barplots.layout["width_question"]
                + config.barplots.layout["width_groups"]
                + config.barplots.layout["width_plot"]
                + 3 * config.barplots.layout["width_pad"],
                y=geometry["central_bar_positions"][id_g],
                text=summary,
                horizontalalignment="left",
                verticalalignment="center",
                fontproperties=config.barplots.font_summary,
                x_units="inches",
                y_units="data",
                width_units="inches",
                width=config.barplots.layout["width_summary"],
                figure=fig,
                ax=ax,
            )
            fig.add_artist(question_label)


def get_summary(d: pd.DataFrame, no_answer_code: int) -> str:
    n_no_answer = (d == no_answer_code).sum()
    d = d[~(d == no_answer_code)]
    mean = d.mean()
    std = d.std()

    if d.size > 0:
        st = f"n = {d.size}\nm = {mean:.2f}\ns = {std:.2f}"
        st += f"\nE = {n_no_answer}"
    else:
        st = "{:<9}".format("n = 0")
    return st


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
            fontproperties=config.barplots.font_questions,
            x_units="inches",
            y_units="figure",
            width_units="inches",
            width=config.barplots.layout["width_question"],
            figure=fig,
        )
        fig.add_artist(question_label)


def get_layout(
    config: Configuration, n_variables: int, n_units_legend: int
) -> tuple[Figure, list[Axes]]:
    # calculate figuresize and get figure
    fig_width = (
        config.barplots.layout["width_question"]
        + config.barplots.layout["width_groups"]
        + config.barplots.layout["width_plot"]
        + config.barplots.layout["width_summary"]
        + 3 * config.barplots.layout["width_pad"]
    )

    fig_height = (n_variables + n_units_legend) * config.barplots.layout[
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
            config.barplots.layout["width_question"]
            + config.barplots.layout["width_groups"]
            + 2 * config.barplots.layout["width_pad"]
        )
        / fig_width,
        right=(
            config.barplots.layout["width_question"]
            + config.barplots.layout["width_groups"]
            + config.barplots.layout["width_plot"]
            + 2 * config.barplots.layout["width_pad"]
        )
        / fig_width,
        top=n_variables / (n_variables + n_units_legend),
        bottom=0.0,
        figure=fig,
    )

    # add Axes subplots
    axes = []
    for id_v in range(n_variables):
        ax = fig.add_subplot(grid[id_v])
        if (id_v == 0) & (id_v == (n_variables - 1)):
            ax.spines["top"].set_visible(True)
            ax.spines["left"].set_visible(True)
            ax.spines["right"].set_visible(True)
            ax.spines["bottom"].set_visible(True)
        elif id_v == 0:
            ax.spines["top"].set_visible(True)
            ax.spines["left"].set_visible(True)
            ax.spines["right"].set_visible(True)
            ax.spines["bottom"].set_visible(False)
        elif id_v == (n_variables - 1):
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


def get_colors(
    config: Configuration, value_map: Any | None, color_scheme: str, invert: bool
) -> np.array:
    if value_map is None:
        n_bins = config.plotting.nbins
    else:
        n_bins = len(value_map.keys())
    all_colors = plt.get_cmap(color_scheme)(np.linspace(0.15, 0.85, n_bins))
    all_colors = np.asarray(all_colors)
    if invert is True:
        all_colors = np.flip(all_colors, axis=0)
    return all_colors


def add_bars(
    n_variables: int,
    axes: list[Axes],
    config: Configuration,
    groups: list[str],
    geometry: dict,
    histograms: list,
    all_colors: np.array,
    text_color: str,
) -> None:
    for id_v in range(n_variables):
        ax = axes[id_v]
        histograms_variable = histograms[id_v]

        # make bars for each group
        for id_g, group in enumerate(groups):
            # bar chart
            widths_abs, offsets_abs = histograms_variable[group]

            # drop bins with no values
            colors = all_colors[widths_abs > 0]
            offsets_abs = offsets_abs[widths_abs > 0]
            widths_abs = widths_abs[widths_abs > 0]

            # make relative
            offsets = offsets_abs / np.sum(widths_abs)
            widths = widths_abs / np.sum(widths_abs)

            ax.barh(
                geometry["central_bar_positions"][id_g],
                widths,
                left=offsets,
                height=geometry["bar_height"],
                color=colors,
            )

            # add number indicating number of answers
            xcenters = offsets + widths / 2.0
            for ii, value in enumerate(widths_abs):
                if widths[ii] < 0.05:
                    # skip very narrow bins
                    continue
                ax.text(
                    xcenters[ii],
                    geometry["central_bar_positions"][id_g],
                    str(int(value)),
                    ha="center",
                    va="center",
                    color=text_color,
                    fontproperties=config.barplots.font_plot,
                )


def get_histograms(
    config: Configuration,
    groups: list[str],
    codebook: pd.DataFrame,
    data: Data,
    n_variables: int,
    value_map: Any | None,
) -> tuple[list, int, int]:
    no_answer_code = data.no_answer_code

    min_value = 1000000
    max_value = -1000000
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
            d = d[~(d == code.missing_label)]
            # drop no answer
            d = d[~(d == no_answer_code)]
            min_value = min(d.min(), min_value)
            max_value = max(d.max(), max_value)

    if value_map is None:
        # no mapping provided (assume numeric values)
        bin_edges = np.linspace(min_value, max_value, config.plotting.nbins + 1)
    else:
        bin_centers = np.asarray(list(value_map.keys()))
        bin_edges = np.append(bin_centers, bin_centers[-1] + 1) - 0.5

    histograms = []
    for id_v in range(n_variables):
        code = codebook.iloc[id_v]
        variable = code["variable"]
        histograms_variable = {}
        for group in groups:
            d = data.data[data.data["nice_plots_group"] == group]
            d = d[variable]

            # drop nans
            d = d[~d.isna()]
            # drop missing answers
            d = d[~(d == no_answer_code)]

            hist = np.histogram(d, bins=bin_edges)[0]
            histograms_variable[group] = [hist, np.cumsum(np.append(0, hist[:-1]))]
        histograms.append(histograms_variable)
    return histograms, min_value, max_value


def get_geometry(config: Configuration, groups: list[str]) -> dict:
    geometry = {}

    # calculate central positions of bars
    pad_questions = config.barplots.layout["height_rel_pad_questions"]
    pad_groups = config.barplots.layout["height_rel_pad_groups"]
    n_bars = len(groups)
    bar_height = (1.0 - pad_questions - (n_bars - 1) * pad_groups) / n_bars
    geometry["bar_height"] = bar_height

    if n_bars % 2 == 0:
        # even number of bars
        positions = (pad_groups + bar_height) / 2 + np.arange(n_bars / 2) * (
            bar_height + pad_groups
        )
        positions = np.append(positions, -1.0 * positions)
    else:
        # uneven number of bars
        positions = (np.arange((n_bars - 1) / 2) + 1) * (bar_height + pad_groups)
        positions = np.append(positions, -1.0 * positions)
        positions = np.append(0, positions)
    geometry["central_bar_positions"] = positions
    return geometry


def add_legend(
    fig: Figure,
    ax: Axes,
    config: Configuration,
    all_colors: np.array,
    value_map: Any | None,
    min_value: int,
    max_value: int,
    n_variables: int,
    n_units_legend: int,
) -> None:
    if value_map is None:
        # assume numeric values
        edges = np.linspace(min_value, max_value, config.plotting.nbins + 1)
        lower_ends = edges[:-1]
        upper_ends = edges[1:]
        category_names = [
            f"{low} - {up} {config.plotting.unit}"
            for low, up in zip(lower_ends, upper_ends)
        ]

    elif (pd.Series(value_map.values()).str.len() != 0).all():
        # full mapping provided
        category_names = list(value_map.values())
    elif (len(list(value_map.values())[0]) != 0) and (
        len(list(value_map.values())[-1]) != 0
    ):
        # mapping given but only for first and last element
        lower_category_name = list(value_map.values())[0]
        upper_category_name = list(value_map.values())[-1]

        n_bins = len(list(value_map.values()))
        norm = mpl.colors.Normalize(vmin=0, vmax=n_bins)
        cmap = mpl.colors.ListedColormap(all_colors)
        s_m = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
        s_m.set_array([])

        config.barplots.layout["width_question"] + config.barplots.layout[
            "width_groups"
        ] + config.barplots.layout["width_plot"] + 3 * config.barplots.layout[
            "width_pad"
        ],

        # in fractions of figure size
        inches_to_fig = fig.dpi_scale_trans + fig.transFigure.inverted()
        left = inches_to_fig.transform(
            (
                config.barplots.layout["width_question"]
                + config.barplots.layout["width_groups"]
                + 2 * config.barplots.layout["width_pad"]
                + config.barplots.layout["width_plot"] * (1 - WIDTH_COLORBAR_REL) / 2,
                0,
            )
        )[0]
        bottom = (n_variables + 0.1) / (n_variables + n_units_legend)
        x_size = inches_to_fig.transform(
            (config.barplots.layout["width_plot"] * WIDTH_COLORBAR_REL, 0.0)
        )[0]
        y_size = inches_to_fig.transform(
            (0, HEIGHT_COLORBAR_REL * config.barplots.layout["height_question"])
        )[1]

        cax = fig.add_axes([left, bottom, x_size, y_size], frame_on=False)
        plt.colorbar(
            s_m,
            cax=cax,
            orientation="horizontal",
            spacing="proportional",
            ticks=[],
        )

        inches_to_data = fig.dpi_scale_trans + cax.transData.inverted()
        # add min/max labels
        cax.text(
            inches_to_data.transform(
                (
                    config.barplots.layout["width_question"]
                    + config.barplots.layout["width_groups"]
                    + config.barplots.layout["width_pad"]
                    + (1 - WIDTH_COLORBAR_REL)
                    / 2
                    * config.barplots.layout["width_plot"],
                    0,
                )
            )[0],
            0.5,
            lower_category_name,
            va="center",
            ha="right",
            fontproperties=config.barplots.font_legend,
        )
        cax.text(
            inches_to_data.transform(
                (
                    config.barplots.layout["width_question"]
                    + config.barplots.layout["width_groups"]
                    + (1 + WIDTH_COLORBAR_REL)
                    / 2
                    * config.barplots.layout["width_plot"]
                    + 3 * config.barplots.layout["width_pad"],
                    0,
                )
            )[0],
            0.5,
            upper_category_name,
            va="center",
            ha="left",
            fontproperties=config.barplots.font_legend,
        )
        return
    else:
        raise NotImplementedError(f"Mapping {value_map} not understood.")

    patches = []
    for ii, category in enumerate(category_names):
        patches.append(Patch(color=all_colors[ii], label=category))
    ax.legend(
        handles=patches,
        ncol=2,
        bbox_to_anchor=(0, 1),
        loc="lower left",
        frameon=False,
        prop=config.barplots.font_legend,
    )
