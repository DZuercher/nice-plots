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


def get_question_padding(ctx, global_plotting_data):
    question_padding = utils.get_question_size(global_plotting_data, ctx)
    question_padding += ctx['padding']
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
    question_padding = get_question_padding(ctx, global_plotting_data)

    plotting_data = global_plotting_data[xx]
    # loop over question blocks and produce one plot for each question block
    n_questions = len(plotting_data[list(plotting_data.keys())[0]])

    # initialize canvas
    y_size = n_questions
    figsize = (ctx['plot_width'], ctx['plot_height_per_question'] * y_size)
    fig, ax = plt.subplots(figsize=figsize)

    # loop over filter categories
    xs = {}
    ys = {}

    # loop over filter categories
    for ii, key in enumerate(plotting_data.keys()):
        # get y axis posistions of the bars of this category
        offset = ctx['dist']
        positions = [offset + xx * ctx['plot_height_per_question']
                     for xx in range(n_questions)]
        ys[key] = positions

        # loop over questions
        x = np.zeros(0)
        for jj, p_d in enumerate(plotting_data[key]):

            # draw lines
            ax.axhline(positions[jj], c='k', lw=3)

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

            for edge in edges:
                ax.vlines(
                    edge, ymin=positions[jj] - 0.6,
                    ymax=positions[jj] + 0.6, color='k', lw=3)

            mean = np.mean(d)
            x = np.append(x, mean)
        xs[key] = x

        utils.add_questions(plotting_data[key], n_questions,
                            positions, ax, ctx, -question_padding)

    # plot the lines
    for ii, key in enumerate(xs.keys()):
        ax.plot(xs[key], ys[key], marker='X', markersize=25,
                color=lineplot_colors[ii], lw=3)

    label_key = list(plotting_data.keys())[0]
    labels = plotting_data[label_key]
    ylabels = [[], []]
    for p_d in labels:
        try:
            ylabels[0].append(p_d['meta']['mapping'][0]['label'])
            ylabels[1].append(p_d['meta']['mapping'][-1]['label'])
        except KeyError:
            ylabels[0].append(min_x)
            ylabels[1].append(max_x)

    # y axis
    for ii in range(len(ylabels[0])):
        ax.text(-0.08, positions[ii], ylabels[0][ii],
                fontsize=ctx['fontsize'], va='center', ha='right')
    for ii in range(len(ylabels[1])):
        ax.text(1.08, positions[ii], ylabels[1][ii],
                fontsize=ctx['fontsize'], va='center')

    # x axis
    ax.set_xticks([])
    ax.set_xticklabels([])
    # ax.set_xlim(-0.05, 1.05)
    ax.set_xlim(-0.005, 1.005)

    # leave 1 dist from top and bottom border
    ymax = -np.inf
    ymin = np.inf

    for ii, key in enumerate(ys.keys()):
        ymin = np.max([ymin, np.min(ys[key])])
        ymax = np.max([ymax, np.max(ys[key])])
    ax.invert_yaxis()
    ax.axis('off')

    # legend
    add_legend(plotting_data, lineplot_colors, ctx)

    # save plot
    fig.savefig(
        f"{ctx['output_directory']}/{ctx['output_name']}_{xx}.{ctx['format']}",
        bbox_inches='tight')
