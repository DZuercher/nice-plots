# Authors: Dominik Zuercher, Valeria Glauser
import ast

# matplotlib.use("agg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

from niceplots.utils.nice_logger import init_logger
from niceplots.utils.plotting_utils import WrapText

logger = init_logger(__file__)


def plot_barplots(config, codebook, data_collection):
    for data_name in data_collection.data_object_names:
        data = getattr(data_collection, data_name)
        blocks = codebook.blocks[~np.isnan(codebook.blocks)]
        for block in blocks:
            plot_barplot(block, data, config, codebook)


def plot_barplot(block, data, config, codebook):
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

    Note: If the fontsize is very large and the text is very long it can happen that the wrapping does not
    work properly (overlapping or many lines).
    In that case you should increase the physical width of the plot components.

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
    # calculate some general numbers (number of bars etc.)
    codebook_block = codebook.codebook[codebook.codebook.block == block]
    n_questions = codebook_block.shape[0]
    n_groups = len(config.data.groups.keys())

    # calculate figuresize and get figure
    fig_width = (
        config.barplots.layout["width_question"]
        + config.barplots.layout["width_groups"]
        + config.barplots.layout["width_plot"]
        + config.barplots.layout["width_summary"]
        + 3 * config.barplots.layout["width_pad"]
    )

    # add units for legend (increase if legend is too large)
    n_units_legend = 2
    fig_height = (n_questions + n_units_legend) * config.barplots.layout[
        "height_question"
    ]
    fig = plt.figure(figsize=(fig_width, fig_height))

    # setup grid layout
    grid = gridspec.GridSpec(
        nrows=n_questions,
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
            + 3 * config.barplots.layout["width_pad"]
        )
        / fig_width,
        top=n_questions / (n_questions + n_units_legend),
        bottom=0.0,
        figure=fig,
    )

    # add Axes subplots
    plots = []
    for id_q in range(n_questions):
        ax = fig.add_subplot(grid[id_q], frameon=False)
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
        plots.append(ax)

    # TODO: plot bars
    for id_q in range(n_questions):
        add_bars(
            ax=plots[id_q], config=config, codebook=codebook_block.iloc[id_q], data=data
        )

    # add questions
    height_question_figure = 1.0 / (n_questions + n_units_legend)
    for id_q, question in enumerate(codebook_block.label):
        center_position_question = (0.5 + id_q) * height_question_figure
        question = WrapText(
            x=0.0,
            y=center_position_question,
            text=question,
            horizontalalignment="left",
            verticalalignment="center",
            fontproperties=config.barplots.font_questions,
            width_units="inches",
            width=config.barplots.layout["width_question"],
            figure=fig,
        )
        fig.add_artist(question)

    # TODO add labels (unhhh nasty...)
    # height_question_figure = 1. / (n_questions + n_units_legend)
    # for id_q, question in enumerate(codebook_block.label):
    #     center_position_question = (0.5 + id_q) * height_question_figure
    #     question = WrapText(x=0.0,
    #                         y=center_position_question,
    #                         text=question,
    #                         horizontalalignment='left',
    #                         verticalalignment='center',
    #                         fontproperties=config.barplots.font_question,
    #                         units="inches",
    #                         width=config.barplots.layout["width_question"],
    #                         figure=fig
    #                         )
    #     fig.add_artist(question)

    # TODO calculate and add summaries

    # TODO add legend

    # save plot
    fig.savefig(
        f"{config.output_directory}/{config.output_name}_{block}.{config.plotting.format}",
        transparent=False,
    )
    plt.close()


def add_bars(ax, config, codebook, data):
    """
    Plots the bar plots for one question block and one category.
    :param ax: Axes object
    :param plotting_data: Plotting data
    :param positions: y axis positions of the bars.
    :param ctx: Configuration instance
    :return : Used colors
    """
    text_color = codebook["barplots.text_color"]
    value_map = (
        None if codebook["value_map"] == "" else ast.literal_eval(codebook["value_map"])
    )
    color_scheme = codebook["barplots.color_scheme"]
    invert = codebook["barplots.invert"]
    variable = codebook["variable"]
    no_answer_code = data.no_answer_code
    groups = list(config.data.groups.keys())

    plotting_data = {}

    n_bins_max = 0
    # loop over groups
    for id_g, group in enumerate(groups):
        d = data.data[data.data["nice_plots_group"] == group]
        d = d[variable]

        # drop nans
        d = d[~d.isna()]
        # drop missing answers
        d = d[~(d == no_answer_code)]

        # generate histogram
        if value_map is None:
            # no mapping provided (assume integers and do not consider 0s)
            hist = np.bincount(d)[1:]
        else:
            bin_edges = np.asarray(list(value_map.keys()))
            bin_edges = np.append(bin_edges, bin_edges[-1] + 1) - 0.5
            hist = np.histogram(d, bins=bin_edges)[0]

        n_bins_max = max(len(hist), n_bins_max)
        plotting_data[group] = [hist, np.cumsum(np.append(0, hist[:-1]))]

    # make colors
    all_colors = plt.get_cmap(color_scheme)(np.linspace(0.15, 0.85, n_bins_max))
    all_colors = np.asarray(all_colors)
    if invert == True:
        all_colors = np.flip(all_colors, axis=0)

    # calculate central positions of bars
    pad_questions = config.barplots.layout["height_rel_pad_questions"]
    pad_groups = config.barplots.layout["height_rel_pad_groups"]
    n_bars = len(groups)
    bar_height = (1.0 - pad_questions - (n_bars - 1) * pad_groups) / n_bars

    if n_bars % 2 == 0:
        # even number of bars
        n_bars_above_0 = n_bars / 2
        positions = (pad_groups + bar_height) / 2 + np.arange(n_bars_above_0) * (
            bar_height + pad_groups
        )
        positions = np.append(positions, -1.0 * positions)
    else:
        # uneven number of bars
        n_bars_above_0 = (n_bars - 1) / 2
        positions = (np.arange(n_bars_above_0) + 1) * (bar_height + pad_groups)
        positions = np.append(positions, -1.0 * positions)
        positions = np.append(0, positions)

    # make bars for each group
    for id_g, group in enumerate(groups):
        # bar chart
        widths_abs, offsets_abs = plotting_data[group]

        # drop bins with no values
        colors = all_colors[widths_abs > 0]
        offsets_abs = offsets_abs[widths_abs > 0]
        widths_abs = widths_abs[widths_abs > 0]

        # make relative
        offsets = offsets_abs / np.sum(widths_abs)
        widths = widths_abs / np.sum(widths_abs)

        ax.barh(positions[id_g], widths, left=offsets, height=bar_height, color=colors)

        # add number indicating number of answers
        xcenters = offsets + widths / 2.0
        for ii, value in enumerate(widths_abs):
            if widths[ii] < 0.05:
                # skip very narrow bins
                continue
            ax.text(
                xcenters[ii],
                positions[id_g],
                str(int(value)),
                ha="center",
                va="center",
                color=text_color,
                fontproperties=config.barplots.font_plot,
            )
    return all_colors


# def add_legend(plotting_data, category_colors, ctx, fig, ax, num_bars, dist, height):
#     """
#     Adds a legend at the top describing what the colors mean.
#     """
#     p_d = plotting_data[0]["meta"]
#     if p_d["invert"] == "True":
#         category_colors = np.flip(category_colors, axis=0)
#
#     if "bins" in p_d["mapping"]:
#         # no labels for the colors given.
#         # Instead add a numerical range for each color category.
#         category_names = []
#         lower = p_d["mapping"]["bins"][:-1]
#         upper = p_d["mapping"]["bins"][1:]
#         category_names = [
#             f'{math.ceil(ll)} - {math.floor(u)} {p_d["unit"]}'
#             for ll, u in zip(lower, upper)
#         ]
#
#     elif "" in [p_d["mapping"][xx]["label"] for xx in range(len(p_d["mapping"]))]:
#         # no labels for the colors given.
#         # instead just add the colorbar with a min and max label
#
#         # dimensions in figure coordinates
#         position = [1.0 / 3.0, -dist]
#         position = utils.axispixels_to_figurepixels_position(position, ax)
#         size = [1.0 / 3.0, height / 2.0]
#         x_size = utils.axispixels_to_figurepixels_size(size[0], ax, dim="x")
#         y_size = utils.axispixels_to_figurepixels_size(size[1], ax, dim="y")
#
#         cax = fig.add_axes([position[0], position[1], x_size, y_size])
#
#         # colorbar
#         norm = mpl.colors.Normalize(vmin=0, vmax=len(p_d["mapping"]))
#         c_m = getattr(mpl.cm, p_d["color_scheme"])
#         c_m = mpl.colors.ListedColormap(
#             c_m(np.linspace(0.15, 0.85, len(p_d["mapping"])))
#         )
#         if p_d["invert"] == "True":
#             c_m = c_m.reversed()
#         s_m = mpl.cm.ScalarMappable(cmap=c_m, norm=norm)
#         s_m.set_array([])
#         cbar = plt.colorbar(
#             s_m,
#             cax=cax,
#             orientation="horizontal",
#             boundaries=list(np.arange(0, len(p_d["mapping"]) + 1)),
#             spacing="proportional",
#             ticks=[],
#         )
#
#         # add min/max labels
#         cax.text(
#             -0.3,
#             0.5,
#             p_d["mapping"][0]["label"],
#             va="center",
#             ha="right",
#             fontsize=ctx["fontsize_stats"],
#         )
#         cax.text(
#             len(p_d["mapping"]) + 0.3,
#             0.5,
#             p_d["mapping"][-1]["label"],
#             va="center",
#             ha="left",
#             fontsize=ctx["fontsize_stats"],
#         )
#
#         cbar.outline.set_visible(False)
#         cax.set_ylim([0.0, 1.0])
#         return
#
#     else:
#         # standard case. A label is given for each color.
#         category_names = []
#         for m in p_d["mapping"]:
#             category_names.append(m["label"])
#
#     patches = []
#     for ii, category in enumerate(category_names):
#         patches.append(mpatches.Patch(color=category_colors[ii], label=category))
#     plt.legend(
#         handles=patches,
#         ncol=2,
#         bbox_to_anchor=(0, 1),
#         loc="lower left",
#         frameon=False,
#         fontsize=ctx["fontsize_stats"],
#     )
#
#
# def add_stats(ax, plotting_data, positions, ctx):
#     """
#     Add sample size, mean and standard deviation at the end of each bar.
#     :param ax: Axes object
#     :param plotting_data: Plotting data
#     :param positions: y axis positions of the bars.
#     :param ctx: Configuration instance
#     """
#     for ii in range(len(plotting_data)):
#         d = plotting_data[ii]["data"][
#             np.logical_not(np.isnan(plotting_data[ii]["data"]))
#         ]
#         d = d.astype(float)
#
#         if "bins" not in plotting_data[ii]["meta"]["mapping"]:
#             # ignore 0 values
#             d = d[d > 0]
#
#         meta = plotting_data[ii]["meta"]
#         st = utils.get_stats(d, meta)
#         ax.text(
#             1.05,
#             positions[ii],
#             st,
#             fontsize=ctx["fontsize_stats"],
#             color="black",
#             va="center",
#         )
#
#
# def add_category_labels(n_categories, plotting_data, n_questions, positions, ax, ctx):
#     """
#     If the sample was split into different categories add a small label
#     indicating the category for which the plot was made.
#     """
#     positions = np.sort(np.asarray(positions))
#     ax.tick_params(axis="y", which="both", length=0, pad=7)
#     ax.set_yticks(positions, minor=True)
#
#     # add category names (only if more then 1 category)
#     if n_categories > 1:
#         ax.set_yticklabels(
#             np.tile(list(plotting_data.keys()), n_questions),
#             minor=True,
#             fontsize=ctx["fontsize"],
#         )
#     ax.set_yticklabels([])
#
#
# def get_label_width(plotting_data, ctx):
#     """
#     Returns width of category label.
#     :param plotting_data: Plotting data
#     :param ctx: Configuration instance
#     :return : Width of label
#     """
#     cat_labels = plotting_data[0].keys()
#     label_width = 0
#     for lab in cat_labels:
#         extent = utils.get_render_size(lab, ctx)
#         label_width = np.max([label_width, extent])
#     return label_width
#
#
# def get_question_padding(ctx, global_plotting_data, pad):
#     """
#     Get distance between question and category labels.
#     :param ctx: Configuration instance
#     :param global_plotting_data: Plotting data
#     :return : padding distance
#     """
#     question_padding = utils.get_question_size(global_plotting_data, ctx)
#     question_padding += pad
#     question_padding += get_label_width(global_plotting_data, ctx)
#     return question_padding
#
#
# def plot_barplots(xx, global_plotting_data, ctx):
#     plotting_data = global_plotting_data[xx]
#
#     # init figure
#     fig, ax = plt.subplots(tight_layout=False)
#
#     # get number of questions and filters
#     n_categories = len(plotting_data.keys())
#     n_questions = len(plotting_data[list(plotting_data.keys())[0]])
#
#     # calculate plot size in inches
#     y_size_in_inches = n_categories * n_questions * ctx["height"]
#     y_size_in_inches += (n_questions - 1) * ctx["major_dist"]
#     y_size_in_inches += n_questions * (n_categories - 1) * ctx["dist"]
#
#     # initialize canvas
#     figsize = (ctx["plot_width"], y_size_in_inches)
#     fig, ax = plt.subplots(figsize=figsize, tight_layout=False)
#
#     # get quantities in pixels
#     height = utils.inches_to_axispixels_size(
#         ctx["height"], fig, ax, dim="y"
#     )  # height of a single bar
#     dist = utils.inches_to_axispixels_size(
#         ctx["dist"], fig, ax, dim="y"
#     )  # distance between two bars of same question
#     major_dist = utils.inches_to_axispixels_size(
#         ctx["major_dist"], fig, ax, dim="y"
#     )  # distance between bars of different questions
#     label_pad = utils.inches_to_axispixels_size(
#         ctx["padding"], fig, ax, dim="x"
#     )  # distance between bar label and ???
#     distance = (
#         major_dist + dist * (n_categories - 1) + n_categories * height
#     )  # distance between bars of same category
#
#     # loop over filter categories
#     all_positions = []
#     for ii, key in enumerate(plotting_data.keys()):
#         offset = dist * ii + height * ii + height / 2.0
#         positions = [
#             offset + ii * distance for ii in range(n_questions)
#         ]  # positions of all questions belonging to this category
#
#         all_positions += positions
#
#         # make bar plots for all questions and category ii
#         category_colors = plot_nice_bar(ax, plotting_data[key], positions, ctx, height)
#
#         # add summary statistics at end of the bar
#         add_stats(ax, plotting_data[key], positions, ctx)
#
#     # add question labels central on the bars
#     if n_categories == 1:
#         offset = height / 2.0
#     elif (n_categories % 2) == 0:
#         offset = (
#             dist / 2.0
#             + int(n_categories / 2.0) * height
#             + (int(n_categories / 2.0) - 1) * dist
#         )
#     else:
#         offset = (
#             math.floor(n_categories / 2.0) * height
#             + height / 2.0
#             + (math.floor(n_categories / 2.0) - 1) * dist
#         )
#     central_positions = [offset + ii * distance for ii in range(n_questions)]
#
#     # distance between plot and questions
#     question_padding = get_question_padding(ctx, global_plotting_data, label_pad)
#     utils.add_questions(
#         plotting_data[key], n_questions, central_positions, ax, ctx, -question_padding
#     )
#
#     # add category names (must stay here!)
#     add_category_labels(
#         n_categories, plotting_data, n_questions, all_positions, ax, ctx
#     )
#
#     # axis formatting
#     ax.set_xticks([])
#     ax.set_xticklabels([])
#     ax.set_xlim([0, 1])
#     ax.set_ylim(
#         [-dist / 2.0, np.max(all_positions) + (height + dist) / 2.0]
#     )  # leave 1 dist from top and bottom border
#
#     ax.invert_yaxis()
#
#     # must be after limit setting and invert
#     add_legend(
#         plotting_data[key],
#         category_colors,
#         ctx,
#         fig,
#         ax,
#         len(all_positions),
#         dist,
#         height,
#     )
#
#     # save plot
#     fig.savefig(
#         f"{ctx['output_directory']}/{ctx['output_name']}_{xx}.{ctx['format']}",
#         bbox_inches="tight",
#         transparent=False,
#     )
#     plt.close()
