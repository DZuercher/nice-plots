# Authors: Dominik Zuercher, Valeria Glauser

import matplotlib.pyplot as plt
import hyphen
from hyphen.textwrap2 import fill
import matplotlib.patches as mpatches
import math
import numpy as np
from niceplots import utils
import frogress
from multiprocessing import Pool
from functools import partial
import matplotlib as mpl

LOGGER = utils.init_logger(__file__)


def plot_nice_bar(ax, plotting_data, positions, ctx):
    """
    Plots the bar plots for one question block and one category.
    :param ax: Axes object
    :param plotting_data: Plotting data
    :param positions: y axis positions of the bars.
    :param ctx: Configuration instance
    :return : Used colors
    """

    text_color = ctx['bar_text_color']

    # create histograms for each question
    results = []
    results_cum = []

    # loop over questions
    for p_d in plotting_data:
        # remove nan values (missing)
        d = p_d['data'][np.logical_not(np.isnan(p_d['data']))]
        d = d.astype(int)

        # special handling if no mapping scheme defined
        if 'bins' in plotting_data[0]['meta']['mapping']:
            hist = np.histogram(
                d, bins=plotting_data[0]['meta']['mapping']['bins'])[0]
        else:
            hist = np.bincount(d)
            hist = hist[1:]
        if p_d['meta']['invert'] == 'True':
            # flip order of bins
            hist = np.flip(hist)
        # ignore first bin (zero values)
        results.append(hist)
        results_cum.append(np.cumsum(hist))

    # Get colors for each category
    if 'bins' in plotting_data[0]['meta']['mapping']:
        n_categories = len(plotting_data[0]['meta']['mapping']['bins']) - 1
    else:
        n_categories = len(plotting_data[0]['meta']['mapping'])
    all_category_colors = plt.get_cmap(
        plotting_data[0]['meta']['color_scheme'])(np.linspace(
            0.15, 0.85, n_categories))
    all_category_colors = np.asarray(all_category_colors)

    # loop over questions in block and produce one bar each
    for i in range(len(results)):
        # bar chart
        widths = results[i]
        offsets = results_cum[i]

        bool_idx = np.append(
            widths, [0] * (all_category_colors.shape[0] - len(widths)))
        category_colors = all_category_colors[bool_idx > 0, :]

        offsets = offsets[widths > 0]
        widths = widths[widths > 0]

        offsets = offsets / np.sum(widths)
        widths = widths / np.sum(widths)
        starts = offsets - widths

        ax.barh(positions[i], widths, left=starts,
                height=ctx['width'], color=category_colors)

        # add number indicating number of answers
        xcenters = starts + widths / 2.
        for ii, c in enumerate(results[i][results[i] > 0]):
            ax.text(xcenters[ii], positions[i], str(int(c)), ha='center',
                    va='center',
                    color=text_color, fontsize=ctx['fontsize'])

    return all_category_colors


def add_legend(plotting_data, category_colors, ctx, fig, ax, num_bars):
    """
    Adds a legend at the top describing the color -> label matching.
    """
    p_d = plotting_data[0]['meta']
    if 'bins' in p_d['mapping']:
        category_names = []
        lower = p_d['mapping']['bins'][:-1]
        upper = p_d['mapping']['bins'][1:]
        category_names = [
            f'{math.ceil(ll)} - {math.floor(u)} {p_d["unit"]}'
            for ll, u in zip(lower, upper)]
    elif '' in [p_d['mapping'][xx]['label']
                for xx in range(len(p_d['mapping']))]:

        #box = mpl.transforms.Bbox.from_bounds(0.195, 0.05, 0.55, ctx['width'] / 3)
        # cax = fig.add_axes(
        #    fig.transFigure.inverted().transform_bbox(
        #        ax.transAxes.transform_bbox(box)))
        cax = fig.add_axes(
            [0.25, 0.89, 0.5, ctx['width'] / num_bars])
        norm = mpl.colors.Normalize(vmin=0, vmax=len(p_d['mapping']) + 1)
        c_m = getattr(mpl.cm, p_d['color_scheme'])
        s_m = mpl.cm.ScalarMappable(cmap=c_m, norm=norm)
        s_m.set_array([])
        cbar = fig.colorbar(s_m, cax=cax, orientation='horizontal',
                            boundaries=list(
                                np.arange(0, len(p_d['mapping']) + 1)),
                            spacing='proportional', ticks=[])
        cax.text(-0.3, 0.0, p_d['mapping'][0]['label'],
                 va='bottom', ha='right', fontsize=ctx['fontsize'])
        cax.text(len(p_d['mapping']) + 0.3, 0.0, p_d['mapping'][-1]['label'],
                 va='bottom', ha='left', fontsize=ctx['fontsize'])
        cbar.outline.set_visible(False)
        return
    else:
        category_names = []
        for m in p_d['mapping']:
            category_names.append(m['label'])
    patches = []
    for ii, category in enumerate(category_names):
        patches.append(mpatches.Patch(
            color=category_colors[ii], label=category))
    plt.legend(handles=patches,
               ncol=2, bbox_to_anchor=(0, 1),
               loc='lower left', frameon=False, fontsize=ctx['fontsize'])


def add_stats(ax, plotting_data, positions, ctx):
    """
    Add sample size, mean and standard deviation at the end of each bar.
    :param ax: Axes object
    :param plotting_data: Plotting data
    :param positions: y axis positions of the bars.
    :param ctx: Configuration instance
    """
    for ii in range(len(plotting_data)):
        d = plotting_data[ii]['data'][np.logical_not(
            np.isnan(plotting_data[ii]['data']))]
        d = d.astype(float)

        if 'bins' not in plotting_data[ii]['meta']['mapping']:
            # ignore 0 values
            d = d[d > 0]

        meta = plotting_data[ii]['meta']
        st = utils.get_stats(d, meta)
        ax.text(1.05, positions[ii], st,
                fontsize=ctx['fontsize_stats'], color='black', va='center')


def add_cat_names(n_categories, plotting_data,
                  n_questions, positions, ax, ctx):
    """
    If the sample was split into different categories add a small label
    indicating the category for which the plot was made.
    """
    ax.tick_params(axis='y', which='both', length=0, pad=7)
    ax.set_yticks(positions, minor=True)

    # add category names (only if more then 1 category)
    if n_categories > 1:
        ax.set_yticklabels(
            np.tile(list(plotting_data.keys()),
                    n_questions), minor=True, fontsize=ctx['fontsize'])
    ax.set_yticklabels([])


def get_label_width(plotting_data, ctx):
    """
    Returns width of category label.
    :param plotting_data: Plotting data
    :param ctx: Configuration instance
    :return : Width of label
    """
    cat_labels = plotting_data[0].keys()
    label_width = 0
    for lab in cat_labels:
        extent = utils.get_render_size(lab, ctx)
        label_width = np.max([label_width, extent])
    return label_width


def get_question_padding(ctx, global_plotting_data):
    """
    Get distance between question and category labels.
    :param ctx: Configuration instance
    :param global_plotting_data: Plotting data
    :return : padding distance
    """
    question_padding = utils.get_question_size(global_plotting_data, ctx)
    question_padding += ctx['padding']
    question_padding += get_label_width(global_plotting_data, ctx)
    return question_padding


def plot_barplots(xx, global_plotting_data, ctx):
    question_padding = get_question_padding(ctx, global_plotting_data)
    plotting_data = global_plotting_data[xx]

    # loop over question blocks and produce one plot for each question block
    n_categories = len(plotting_data.keys())
    n_questions = len(plotting_data[list(plotting_data.keys())[0]])

    # initialize canvas
    y_size = n_categories * n_questions
    figsize = (ctx['plot_width'], ctx['plot_height_per_question'] * y_size)
    fig, ax = plt.subplots(figsize=figsize)

    # distance between bars of same category
    distance = ctx['major_dist'] + n_categories * \
        ctx['width'] + (n_categories - 1) * ctx['dist']

    # loop over filter categories
    all_positions = []
    for ii, key in enumerate(plotting_data.keys()):
        # get y axis posistions of the bars of this category
        offset = (ctx['width'] + ctx['dist']) / 2. \
            + ii * (ctx['width'] + ctx['dist'])
        positions = [offset + ii * distance for ii in range(n_questions)]
        all_positions += positions

        # make bar plots
        category_colors = plot_nice_bar(
            ax, plotting_data[key], positions, ctx)

        # add summary statistics at the end
        add_stats(ax, plotting_data[key], positions, ctx)

    all_positions = np.sort(np.asarray(all_positions))
    if n_categories == 1:
        offset = ctx['dist'] + ctx['width'] / 2.
    elif (n_categories % 2) == 0:
        offset = ctx['dist'] + (n_categories // 2) * ctx['width']
    else:
        offset = ctx['dist'] / 2. + \
            ((n_categories - 1) // 2) * (ctx['width'] + ctx['dist'])
    central_positions = [offset + ii
                         * distance for ii in range(n_questions)]

    utils.add_questions(plotting_data[key], n_questions,
                        central_positions, ax, ctx, -question_padding)
    add_legend(plotting_data[key], category_colors, ctx, fig, ax,
               len(all_positions))

    # must stay here!
    add_cat_names(n_categories, plotting_data,
                  n_questions, all_positions, ax, ctx)

    # x axis formatting
    ax.set_xticks([])
    ax.set_xticklabels([])
    ax.set_xlim(0, 1)

    # leave 1 dist from top and bottom border
    ax.set_ylim([-ctx['dist'] / 2.,
                 np.max(all_positions) + ctx['width'] / 2. + ctx['dist']])
    ax.invert_yaxis()

    # save plot
    fig.savefig(
        f"{ctx['output_directory']}/{ctx['output_name']}_{xx}.pdf",
        bbox_inches='tight')


def make_plots(global_plotting_data, ctx, parallel):
    if parallel:
        LOGGER.info("Running in parallel mode")
        with Pool() as p:
            p.map(
                partial(plot_barplots,
                        global_plotting_data=global_plotting_data, ctx=ctx),
                list(range(len(global_plotting_data))))
    else:
        LOGGER.info("Running in serial mode")
        # loop over question blocks and produce one plot for each question block
        for xx, plotting_data in frogress.bar(enumerate(global_plotting_data)):
            plot_barplots(xx, global_plotting_data, ctx)
