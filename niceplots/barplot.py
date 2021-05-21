# Authors: Dominik Zuercher, Valeria Glauser

import matplotlib.pyplot as plt
import hyphen
from hyphen.textwrap2 import fill
import matplotlib.patches as mpatches
import math
import numpy as np
from niceplots import utils
import frogress

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


def add_legend(plotting_data, category_colors, ctx):
    """
    Adds a legend at the top describing the color -> label matching.
    """
    p_d = plotting_data[0]['meta']
    if 'bins' in p_d['mapping']:
        category_names = []
        lower = p_d['mapping']['bins'][:-1]
        upper = p_d['mapping']['bins'][1:]
        category_names = [
            f'{math.ceil(ll)} - {math.floor(u)}'
            for ll, u in zip(lower, upper)]
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


def get_stats(d, meta):
    if d.size > 0:
        st = 'n = {}\nm = {:.2f}\ns = {:.2f}'.format(
            d.size, np.mean(d), np.std(d))
        if 'no_answer' in meta.keys():
            st += '\nE = {}'.format(meta['no_answer'])

    else:
        st = '{:<9}'.format('n = {}'.format(d.size))
    return st


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
        st = get_stats(d, meta)
        ax.text(1.05, positions[ii], st,
                fontsize=ctx['fontsize'], color='black', va='center')


def wrap_text(text, width=60, lang='de_DE'):
    hyp = hyphen.Hyphenator(lang)
    return fill(text, width=width, use_hyphenator=hyp)


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


def add_questions(p_d, n_questions, positions, ax, ctx, dist):
    """
    Add the text of the question for which the distribution of the answer
    is displayed.
    """
    # add questions
    questions = []
    for q in p_d:
        questions.append(q['meta']['question'])
    for nq in range(n_questions):
        lab = wrap_text(questions[nq])
        ax.text(dist, positions[nq], lab, va='center',
                ha='left', fontsize=ctx['fontsize'])
    ax.set_yticks(np.arange(n_questions))


def get_render_size(object, ctx):
    """
    Returns width of a text.
    :param object: String to render
    :param ctx: Configuration instance
    :return : Width of text
    """
    figsize = (ctx['plot_width'], 10)
    f = plt.figure(figsize=figsize)
    rend = f.canvas.get_renderer()
    t = plt.text(0.5, 0.5, object, fontsize=ctx['fontsize'])
    extent = t.get_window_extent(renderer=rend)
    ax = f.gca()
    extent = extent.transformed(ax.transAxes.inverted())
    plt.close(f)
    return np.abs(extent.width)


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
        extent = get_render_size(lab, ctx)
        label_width = np.max([label_width, extent])
    return label_width


def get_question_size(plotting_data, ctx):
    """
    Returns width of question text.
    :param plotting_data: Plotting data
    :param ctx: Configuration instance
    :return : Width of question text
    """
    question = ''
    for p_d in plotting_data:
        p = p_d[list(p_d.keys())[0]]
        for p_ in p:
            if len(p_['meta']['question']) > len(question):
                question = p_['meta']['question']
    extent = get_render_size(wrap_text(question), ctx)
    return extent


def get_question_padding(ctx, global_plotting_data):
    """
    Get distance between question and category labels.
    :param ctx: Configuration instance
    :param global_plotting_data: Plotting data
    :return : padding distance
    """
    question_padding = get_question_size(global_plotting_data, ctx)
    question_padding += ctx['padding']
    question_padding += get_label_width(global_plotting_data, ctx)
    return question_padding


def make_plots(global_plotting_data, ctx):
    LOGGER.info("Producing plots")

    question_padding = get_question_padding(ctx, global_plotting_data)

    # loop over question blocks and produce one plot for each question block
    for xx, plotting_data in frogress.bar(enumerate(global_plotting_data)):
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

        add_questions(plotting_data[key], n_questions,
                      central_positions, ax, ctx, -question_padding)
        add_legend(plotting_data[key], category_colors, ctx)

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

        if ctx['debug']:
            if xx == 0:
                break
