import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
import numpy as np
from niceplots import utils

LOGGER = utils.init_logger(__file__)


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
        lab = utils.wrap_text(questions[nq])
        ax.text(dist, positions[nq], lab, va='center',
                ha='right', fontsize=ctx['fontsize'])
    ax.set_yticks(np.arange(n_questions))


def get_question_padding(ctx, global_plotting_data, pad):
    question_padding = utils.get_question_size(global_plotting_data, ctx)
    question_padding += pad
    label_width = 0
    for ii in range(len(global_plotting_data)):
        cat_labels_key = list(global_plotting_data[ii].keys())[0]
        cat_labels = global_plotting_data[ii][cat_labels_key]

        for lab in cat_labels:
            try:
                text = lab['meta']['mapping'][0]['label']
            except KeyError:
                continue
            extent = utils.get_render_size(text, ctx)
            label_width = np.max([label_width, extent])

    question_padding += label_width
    return question_padding


def add_legend(plotting_data, colors, ctx):
    """
    Adds a legend at the top describing the color -> label matching.
    """
    filter_categories = plotting_data.keys()

    if len(list(filter_categories)) > 1:
        patches = []
        for ii, category in enumerate(filter_categories):
            patches.append(mpatches.Patch(
                color=colors[ii], label=category))
        plt.legend(handles=patches,
                   ncol=2,
                   # no more than 2, otherwise might be longer than plot
                   # ncol=math.ceil(len(filter_categories) / 2),
                   bbox_to_anchor=(0, 1),
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
        d = d.astype(int)

        if 'bins' not in plotting_data[ii]['meta']['mapping']:
            # ignore No Answer
            d = d[d > 0]

        meta = plotting_data[ii]['meta']
        st = utils.get_stats(d, meta)
        ax.text(1.05, positions[ii], st,
                fontsize=ctx['fontsize_stats'], color='black', va='center')


def plot_lineplots(xx, global_plotting_data, ctx):
    lineplot_colors = ctx['lineplot_colors']

    plotting_data = global_plotting_data[xx]
    # loop over question blocks and produce one plot for each question block
    n_questions = len(plotting_data[list(plotting_data.keys())[0]])

    # init figure
    fig, ax = plt.subplots()
    dpi = fig.dpi

    y_size_in_inches = n_questions * ctx['line_plot_height']
    y_size_in_inches += (n_questions - 1) * ctx['line_plot_dist']

    # initialize canvas
    figsize = (ctx['plot_width'], y_size_in_inches)
    fig, ax = plt.subplots(figsize=figsize)

    # get plot height and distances in data coordinates
    zero_point = ax.transAxes.inverted().transform((0, 0))
    height = (ax.transAxes.inverted().transform(
        (0, ctx['line_plot_height'] * dpi)) - zero_point)[1]
    dist = (ax.transAxes.inverted().transform(
        (0, ctx['line_plot_dist'] * dpi)) - zero_point)[1]
    label_pad = (ax.transAxes.inverted().transform(
        (ctx['line_plot_padding'] * dpi, 0)) - zero_point)[0]
    pad = (ax.transAxes.inverted().transform(
        (ctx['line_plot_label_padding'] * dpi, 0)) - zero_point)[0]
    height = np.abs(height)
    dist = np.abs(dist)
    label_pad = np.abs(label_pad)
    pad = np.abs(pad)

    question_padding = get_question_padding(ctx, global_plotting_data,
                                            label_pad + pad)

    # loop over filter categories
    xs = {}
    ys = {}

    # loop over filter categories
    for ii, key in enumerate(plotting_data.keys()):
        # get y axis posistions of the bars of this category
        positions = [xx * (height + dist) + height / 2.
                     for xx in range(n_questions)]
        ys[key] = positions

        # loop over questions
        x = np.zeros(0)
        for jj, p_d in enumerate(plotting_data[key]):

            # draw lines
            ax.hlines(positions[jj], xmin=0, xmax=1, color='k', lw=3)

            d = p_d['data'][np.logical_not(
                np.isnan(p_d['data']))]
            d = d.astype(int)

            if 'bins' not in p_d['meta']['mapping']:
                # ignore No Answer
                d = d[d > 0]

            # add bin edges
            mapping = p_d['meta']['mapping']
            if 'bins' in mapping:
                if mapping['bins'][0] < 0:
                    mapping['bins'] = np.asarray(mapping['bins'])
                    mapping['bins'] -= mapping['bins'][0]
                edges = np.histogram(d, bins=mapping['bins'])[1]
                min_x = int(edges[0])
                max_x = int(math.ceil(edges[-1]))
            else:
                edges = np.asarray([mapping[x]['code']
                                    for x in range(
                    len(p_d['meta']['mapping']))])

            d = (d - edges[0]) / (edges[-1] - edges[0])
            edges = (edges - edges[0]) / (edges[-1] - edges[0])

            # plot the lines
            for edge in edges:
                if p_d['meta']['invert'] == 'True':
                    ax.vlines(
                        1. - edge, ymin=positions[jj] - height / 2.,
                        ymax=positions[jj] + height / 2., color='k', lw=3)
                else:
                    ax.vlines(
                        edge, ymin=positions[jj] - height / 2.,
                        ymax=positions[jj] + height / 2., color='k', lw=3)

            mean = np.mean(d)
            if p_d['meta']['invert'] == 'True':
                mean = 1. - mean

            x = np.append(x, mean)
        xs[key] = x

        utils.add_questions(plotting_data[key], n_questions,
                            positions, ax, ctx, -question_padding)

    # plot the markers
    for ii, key in enumerate(xs.keys()):
        ax.plot(xs[key], ys[key], marker='X', markersize=20,
                color=lineplot_colors[ii], lw=3)

    label_key = list(plotting_data.keys())[0]
    labels = plotting_data[label_key]
    ylabels = [[], []]
    for p_d in labels:
        try:
            if p_d['meta']['invert'] == 'True':
                ylabels[1].append(p_d['meta']['mapping'][0]['label'])
                ylabels[0].append(p_d['meta']['mapping'][-1]['label'])
            else:
                ylabels[0].append(p_d['meta']['mapping'][0]['label'])
                ylabels[1].append(p_d['meta']['mapping'][-1]['label'])
        except KeyError:
            if p_d['meta']['invert'] == 'True':
                ylabels[1].append(min_x)
                ylabels[0].append(max_x)
            else:
                ylabels[0].append(min_x)
                ylabels[1].append(max_x)

    # y axis labels
    for ii in range(len(ylabels[0])):
        ax.text(-pad, positions[ii], ylabels[0][ii],
                fontsize=ctx['fontsize'], va='center', ha='right')
    for ii in range(len(ylabels[1])):
        ax.text(1. + pad, positions[ii], ylabels[1][ii],
                fontsize=ctx['fontsize'], va='center')

    # add_stats(ax, plotting_data, positions, ctx)

    # x axis
    ax.set_xticks([])
    ax.set_xticklabels([])
    ax.set_xlim(-0.05, 1.05)

    ax.invert_yaxis()
    ax.axis('off')

    # legend
    add_legend(plotting_data, lineplot_colors, ctx)

    # save plot
    fig.savefig(
        f"{ctx['output_directory']}/{ctx['output_name']}_{xx}.{ctx['format']}",
        bbox_inches='tight')
