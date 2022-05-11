# Authors: Dominik Zuercher, Valeria Glauser
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
import numpy as np
from niceplots import utils
import matplotlib as mpl
import logging
LOGGER = logging.getLogger(__name__)


def plot_nice_bar(ax, plotting_data, positions, ctx, height):
    """
    Plots the bar plots for one question block and one category.
    :param ax: Axes object
    :param plotting_data: Plotting data
    :param positions: y axis positions of the bars.
    :param ctx: Configuration instance
    :return : Used colors
    """

    text_color = plotting_data[0]['meta']['bar_text_color']

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
    if p_d['meta']['invert'] == 'True':
        all_category_colors = np.flip(all_category_colors)

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
                height=height, color=category_colors)

        # add number indicating number of answers
        xcenters = starts + widths / 2.
        for ii, c in enumerate(results[i][results[i] > 0]):
            ax.text(xcenters[ii], positions[i], str(int(c)), ha='center',
                    va='center',
                    color=text_color, fontsize=ctx['fontsize'])

    return all_category_colors


def add_legend(plotting_data, category_colors, ctx, fig, ax, num_bars, dist,
               height):
    """
    Adds a legend at the top describing what the colors mean.
    """
    p_d = plotting_data[0]['meta']

    if 'bins' in p_d['mapping']:
        # no labels for the colors given.
        # Instead add a numerical range for each color category.
        category_names = []
        lower = p_d['mapping']['bins'][:-1]
        upper = p_d['mapping']['bins'][1:]
        category_names = [
            f'{math.ceil(ll)} - {math.floor(u)} {p_d["unit"]}'
            for ll, u in zip(lower, upper)]

    elif '' in [p_d['mapping'][xx]['label'] for xx in range(len(p_d['mapping']))]:
        # no labels for the colors given.
        # instead just add the colorbar with a min and max label

        # dimensions in figure coordinates
        position = [1. / 3., -dist]
        position = utils.axispixels_to_figurepixels_position(position, ax)
        size = [1. / 3., height / 2.]
        x_size = utils.axispixels_to_figurepixels_size(size[0], ax, dim='x')
        y_size = utils.axispixels_to_figurepixels_size(size[1], ax, dim='y')

        cax = fig.add_axes([position[0], position[1],
                            x_size, y_size])

        # colorbar
        norm = mpl.colors.Normalize(vmin=0, vmax=len(p_d['mapping']))
        c_m = getattr(mpl.cm, p_d['color_scheme'])
        c_m = mpl.colors.ListedColormap(c_m(np.linspace(
            0.15, 0.85, len(p_d['mapping']))))
        s_m = mpl.cm.ScalarMappable(cmap=c_m, norm=norm)
        s_m.set_array([])
        cbar = plt.colorbar(s_m, cax=cax, orientation='horizontal',
                            boundaries=list(
                                np.arange(0, len(p_d['mapping']) + 1)),
                            spacing='proportional', ticks=[])

        # add min/max labels
        cax.text(-0.3, 0.5, p_d['mapping'][0]['label'],
                 va='center', ha='right', fontsize=ctx['fontsize_stats'])
        cax.text(len(p_d['mapping']) + 0.3, 0.5, p_d['mapping'][-1]['label'],
                 va='center', ha='left', fontsize=ctx['fontsize_stats'])

        cbar.outline.set_visible(False)
        cax.set_ylim([0., 1.])
        return

    else:
        # standard case. A label is given for each color.
        category_names = []
        for m in p_d['mapping']:
            category_names.append(m['label'])

    patches = []
    for ii, category in enumerate(category_names):
        patches.append(mpatches.Patch(
            color=category_colors[ii], label=category))
    plt.legend(handles=patches,
               ncol=2, bbox_to_anchor=(0, 1),
               loc='lower left', frameon=False, fontsize=ctx['fontsize_stats'])


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


def add_category_labels(n_categories, plotting_data,
                  n_questions, positions, ax, ctx):
    """
    If the sample was split into different categories add a small label
    indicating the category for which the plot was made.
    """
    positions = np.sort(np.asarray(positions))
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


def get_question_padding(ctx, global_plotting_data, pad):
    """
    Get distance between question and category labels.
    :param ctx: Configuration instance
    :param global_plotting_data: Plotting data
    :return : padding distance
    """
    question_padding = utils.get_question_size(global_plotting_data, ctx)
    question_padding += pad
    question_padding += get_label_width(global_plotting_data, ctx)
    return question_padding


def plot_barplots(xx, global_plotting_data, ctx):
    plotting_data = global_plotting_data[xx]

    # init figure
    fig, ax = plt.subplots(tight_layout=False)

    # get number of questions and filters
    n_categories = len(plotting_data.keys())
    n_questions = len(plotting_data[list(plotting_data.keys())[0]])

    # calculate plot size in inches
    y_size_in_inches = n_categories * n_questions * ctx['height']
    y_size_in_inches += (n_questions - 1) * ctx['major_dist']
    y_size_in_inches += n_questions * (n_categories - 1) * ctx['dist']

    # initialize canvas
    figsize = (ctx['plot_width'], y_size_in_inches)
    fig, ax = plt.subplots(figsize=figsize, tight_layout=False)


    # get quantities in pixels
    height = utils.inches_to_axispixels_size(ctx['height'], fig, ax, dim='y') # height of a single bar
    dist = utils.inches_to_axispixels_size(ctx['dist'], fig, ax, dim='y') # distance between two bars of same question
    major_dist = utils.inches_to_axispixels_size(ctx['major_dist'], fig, ax, dim='y') # distance between bars of different questions
    label_pad = utils.inches_to_axispixels_size(ctx['padding'], fig, ax, dim='x') # distance between bar label and ???
    distance = major_dist + dist * (n_categories - 1) + n_categories * height # distance between bars of same category


    # loop over filter categories
    all_positions = []
    for ii, key in enumerate(plotting_data.keys()):
        offset = dist * ii + height * ii + height / 2.
        positions = [offset + ii * distance for ii in range(n_questions)] # positions of all questions belonging to this category

        all_positions += positions

        # make bar plots for all questions and category ii
        category_colors = plot_nice_bar(
            ax, plotting_data[key], positions, ctx, height)

        # add summary statistics at end of the bar
        add_stats(ax, plotting_data[key], positions, ctx)

    # add question labels central on the bars
    if n_categories == 1:
        offset = height / 2.
    elif (n_categories % 2) == 0:
        offset = dist / 2. + int(n_categories / 2.) * height \
            + (int(n_categories / 2.) - 1) * dist
    else:
        offset = math.floor(n_categories / 2.) * height + height / 2. \
            + (math.floor(n_categories / 2.) - 1) * dist
    central_positions = [offset + ii
                         * distance for ii in range(n_questions)]

    # distance between plot and questions
    question_padding = get_question_padding(
        ctx, global_plotting_data, label_pad)
    utils.add_questions(plotting_data[key], n_questions,
                        central_positions, ax, ctx, -question_padding)

    # add category names (must stay here!)
    add_category_labels(n_categories, plotting_data,
                  n_questions, all_positions, ax, ctx)

    # axis formatting
    ax.set_xticks([])
    ax.set_xticklabels([])
    ax.set_xlim([0, 1])
    ax.set_ylim([-dist / 2., np.max(all_positions) + (height + dist) / 2.]) # leave 1 dist from top and bottom border

    ax.invert_yaxis()

    # must be after limit setting and invert
    add_legend(plotting_data[key], category_colors, ctx, fig, ax,
               len(all_positions), dist, height)

    # save plot
    fig.savefig(
        f"{ctx['output_directory']}/{ctx['output_name']}_{xx}.{ctx['format']}",
        bbox_inches='tight', transparent=False)
    plt.close()
