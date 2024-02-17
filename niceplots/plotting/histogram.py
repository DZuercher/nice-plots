# Authors: Dominik Zuercher, Valeria Glauser
import matplotlib

matplotlib.use("agg")
import logging

import matplotlib.pyplot as plt
import numpy as np

from niceplots import lineplot

LOGGER = logging.getLogger(__name__)


def get_max_question_width(global_plotting_data, ctx):
    """
    Returns width of category label.
    :param plotting_data: Plotting data
    :param ctx: Configuration instance
    :return : Width of label
    """
    label_width = 0
    key0 = list(global_plotting_data[0].keys())[0]
    for p_d in global_plotting_data:
        for qq in p_d[key0]:
            q = qq["meta"]["question"]
            extent = utils.get_render_size(utils.wrap_text(q), ctx)
            label_width = np.max([label_width, extent])
    return label_width


def get_histogram_type(n_questions, plotting_data, xx):
    """Determine if the given data can be used to
    construct a single histogram or a binary histogram
    """
    single_histogram = False
    multi_histogram = False
    if n_questions == 1:
        single_histogram = True
        LOGGER.info(
            f"Question block {xx} contains only a single question "
            "-> Producing a single histogram for this."
        )
    else:
        key0 = list(plotting_data.keys())[0]
        if len(plotting_data[key0][0]["meta"]["mapping"]) == 2:
            multi_histogram = True
            LOGGER.info(
                f"Question block {xx} contains multiple questions "
                "with 2 possible answers each"
                "-> Interpreting as binary and combining "
                "into a single histogram."
            )
            LOGGER.warning(
                "CAUTION: I assume that code = 1 means Yes and code" " = 2 means No!"
            )
        else:
            LOGGER.warning(
                f"Cannot convert question block {xx} into " "a histogram. Skipping..."
            )
    return single_histogram, multi_histogram


def get_histogram_data(plotting_data, single_histogram, multi_histogram):
    """Depending on the histogram type get the necessary data."""
    if single_histogram:
        # loop over filter categories
        histogram_data = []
        for ii, key in enumerate(plotting_data.keys()):
            # get bin edges
            if ii == 0:
                if "bins" in plotting_data[key][0]["meta"]["mapping"]:
                    # special handling
                    bins = plotting_data[key][0]["meta"]["mapping"]["bins"]
                else:
                    bins = [
                        plotting_data[key][0]["meta"]["mapping"][jj]["code"] - 0.5
                        for jj in range(len(plotting_data[key][0]["meta"]["mapping"]))
                    ]
                    bins.append(bins[-1] + 1.0)
                bins = np.asarray(bins)

            d = plotting_data[key][0]["data"][
                np.logical_not(np.isnan(plotting_data[key][0]["data"]))
            ]
            d = d.astype(int)
            histogram_data.append(d)

        # get tick labels
        if "bins" in plotting_data[key][0]["meta"]["mapping"]:
            labels = []
            bin_edges = plotting_data[key][0]["meta"]["mapping"]["bins"]
            label_ticks = bin_edges[:-1] + 0.5 * (bin_edges[1:] - bin_edges[:-1])
            bin_edges = bin_edges.astype(int)

            for ii in range(len(bin_edges) - 1):
                labels.append(f"{bin_edges[ii]} - {bin_edges[ii + 1]}")
        else:
            labels = []
            label_ticks = []
            for m in plotting_data[key][0]["meta"]["mapping"]:
                label_ticks.append(m["code"])
                labels.append(m["label"])

    elif multi_histogram:
        histogram_data = []
        # loop over filter categories
        empty = True
        for ii, key in enumerate(plotting_data.keys()):
            # loop over questions
            data = []
            for jj in range(len(plotting_data[key])):
                p_d = plotting_data[key][jj]
                d = p_d["data"][np.logical_not(np.isnan(p_d["data"]))]
                d = d.astype(int)
                # Assuming 1 = Yes
                data += [jj] * len(d[d == 1])
            data = np.asarray(data)
            if len(data) > 0:
                empty = False
            histogram_data.append(data)
        if empty:
            return
        # get tick labels
        labels = []
        label_ticks = []
        for jj in range(len(plotting_data[key])):
            labels.append(plotting_data[key][jj]["meta"]["question"])
            label_ticks.append(jj)

        # set bins
        bins = np.arange(-0.5, len(plotting_data[key]) + 0.5)

    return labels, label_ticks, bins, histogram_data


def add_bar_length_labels(fig, ax, n, bin_edges, ctx):
    """Adds a small number at the top of the bars indicating the length of the bars."""
    # get offset of bars (from matplotib source code)
    dr = np.clip(ctx["rwidth"], 0, 1)
    totwidth = np.diff(bin_edges)
    width = dr * totwidth / len(n)

    # distance between bars and their labels (in axis pixels)
    zero_point = ax.transData.inverted().transform((0, 0))
    bar_label_pad = (
        ax.transData.inverted().transform((ctx["bar_pad"] * fig.dpi, 0)) - zero_point
    )[0]

    boffset = -0.5 * dr * totwidth * (1 - 1 / len(n))
    boffset += 0.5 * totwidth

    max_value = 0
    for jj, nn in enumerate(n):
        for ii, nnn in enumerate(nn):
            if nnn > 0:
                bar_label_size = utils.get_render_size(str(int(nnn)), ctx)
                bar_label_size = (
                    ax.transLimits.inverted().transform((bar_label_size, 0))
                    - ax.transLimits.inverted().transform((0, 0))
                )[0]

                max_value = np.max(
                    [max_value, nnn + bar_label_size + 2 * bar_label_pad]
                )
                ax.text(
                    nnn + bar_label_pad,
                    bin_edges[ii] + boffset[ii] + jj * width[ii],
                    str(int(nnn)),
                    va="center",
                    ha="left",
                    fontsize=ctx["fontsize"],
                )
    return max_value


def add_tick_labels(fig, ax, labels, label_ticks, ctx, global_plotting_data):
    """Add labels to the histogram bars indicating the question or category name."""
    mean_label_tick = np.mean(label_ticks)

    for ii in range(len(labels)):
        labels[ii] = utils.wrap_text(labels[ii])

    pad = (
        ax.transData.inverted().transform((ctx["histogram_padding"] * fig.dpi, 0))
        - ax.transData.inverted().transform((0, 0))
    )[0]
    for ii in range(len(label_ticks)):
        ax.text(
            -np.abs(pad),
            label_ticks[ii],
            labels[ii],
            ha="right",
            va="center",
            fontsize=ctx["fontsize"],
        )
    ax.tick_params(axis="both", length=0, pad=ctx["histogram_padding"])
    ax.set_xticks([])
    ax.set_yticks([])

    max_question_width = get_max_question_width(global_plotting_data, ctx)
    max_question_width = (
        ax.transLimits.inverted().transform((max_question_width, 0))
        - ax.transLimits.inverted().transform((0, 0))
    )[0]

    ax.text(-max_question_width - pad, mean_label_tick, " ")


def add_stats(plotting_data, ax, max_value, ctx):
    """Add a label indicating the number of participants and those that did not give an answer."""
    N = 0
    E = 0
    for ii, key in enumerate(plotting_data.keys()):
        # only look at first question
        N += len(plotting_data[key][0]["data"])
        if "no_answer" in plotting_data[key][0]["meta"].keys():
            E += plotting_data[key][0]["meta"]["no_answer"]

    stats = f"n = {N}"
    if "no_answer" in plotting_data[key][0]["meta"].keys():
        stats += f"\nE = {E}"

    ylim_low, ylim_up = ax.get_ylim()
    xlim_low, xlim_up = ax.get_xlim()

    ax.set_xlim([0, max_value])

    stats_pos = ax.transData.inverted().transform(
        (ctx["hist_stats_dist"], ctx["hist_stats_dist"])
    ) - ax.transData.inverted().transform((0, 0))

    ax.text(
        xlim_up - np.abs(stats_pos[0]),
        ylim_up,
        stats,
        fontsize=ctx["fontsize_stats"],
        ha="right",
        va="bottom",
    )

    # return the height of the stats label
    stats_height = utils.get_render_size(stats, ctx, x_size=False)
    stats_height = (
        ax.transLimits.inverted().transform((0, stats_height))
        - ax.transLimits.inverted().transform((0, 0))
    )[1]
    return ylim_low, ylim_up, stats_pos, stats_height


def plot_histograms(xx, global_plotting_data, ctx):
    plotting_data = global_plotting_data[xx]

    n_questions = len(plotting_data[list(plotting_data.keys())[0]])

    # check if this kind of item can be made into a single histogram/multihistogram
    single_histogram, multi_histogram = get_histogram_type(
        n_questions, plotting_data, xx
    )

    if (not single_histogram) and (not multi_histogram):
        return

    # preprocessing of data
    labels, label_ticks, bins, histogram_data = get_histogram_data(
        plotting_data, single_histogram, multi_histogram
    )

    # initialize canvas
    figsize = (ctx["plot_width"], ctx["plot_width"])
    fig, ax = plt.subplots(figsize=figsize, tight_layout=False)

    # draw histogram
    n, bin_edges, _ = ax.hist(
        histogram_data,
        bins=bins,
        orientation="horizontal",
        color=ctx["histogram_colors"][: len(list(plotting_data.keys()))],
        rwidth=ctx["rwidth"],
    )

    # need to explicitly set axes limits in order for data coordinates to be reset!
    xlims = ax.get_xlim()
    ax.set_xlim(xlims)
    delta = (bins[1] - bins[0]) / 2.0
    ax.set_ylim([bins[0] - delta, bins[-1] + delta])

    n = np.asarray(n)
    if len(list(n.shape)) == 1:
        n = n.reshape(1, -1)

    # add small numbers at top of bars to indicate their length
    max_bar_length = add_bar_length_labels(fig, ax, n, bin_edges, ctx)

    add_tick_labels(fig, ax, labels, label_ticks, ctx, global_plotting_data)

    # add stats to the plot
    ylim_low, ylim_up, stats_pos, stats_height = add_stats(
        plotting_data, ax, max_bar_length, ctx
    )

    ax.set_ylim([ylim_low, ylim_up + 2 * np.abs(stats_height) + np.abs(stats_pos[1])])

    # add the legend
    lineplot.add_legend(plotting_data, ctx["histogram_colors"], ctx)

    # save plot
    fig.savefig(
        f"{ctx['output_directory']}/{ctx['output_name']}_{xx}.{ctx['format']}",
        bbox_inches="tight",
        transparent=False,
    )
    plt.close()
