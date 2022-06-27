import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from niceplots import utils
import logging
LOGGER = logging.getLogger(__name__)


def plot_timeboxes(xx, global_plotting_datas, ctx):
    plotting_datas = {}
    for label, data in global_plotting_datas.items():
        plotting_datas[label] = data[xx]
    
    first_key = list(plotting_datas.keys())[0]

    n_questions = len(plotting_datas[first_key][
        list(plotting_datas[first_key].keys())[0]])
    filter_groups = list(plotting_datas[first_key].keys())

    # initialize canvas
    y_size_in_inches = n_questions * ctx['timeboxes_plot_height']

    # initialize canvas
    figsize = (ctx['plot_width'], y_size_in_inches)
    fig, ax = plt.subplots(ncols=1, nrows=n_questions, figsize=figsize, tight_layout=False)
    if n_questions == 1:
        ax = [ax]
    plt.subplots_adjust(hspace=ctx['timeboxes_plot_dist'])

    # loop through questions
    for ii in range(n_questions):
        # loop through filter groups
        offsets = np.linspace(-(len(filter_groups)//2  * 0.1), len(filter_groups)//2  * 0.1, len(filter_groups))
        for g, group in enumerate(filter_groups):
            box_data = [plotting_datas[key][group][ii]['data'] for key in list(plotting_datas.keys())]
            ax[ii].boxplot(x=box_data, positions=np.arange(len(box_data)) + offsets[g])
        
        # axes styling
        ax[ii].set_xticks(np.arange(len(box_data)))
        ax[ii].set_xticklabels(list(plotting_datas.keys()), fontsize=ctx['fontsize'])

        # n_answers = len(plotting_datas[first_key][group][ii]['meta']['mapping'])
        # yticks = [plotting_datas[first_key][group][ii]['meta']['mapping'][z]['code'] for z in range(n_answers)]
        # ax[ii].set_yticks(yticks)
        # ax[ii].set_yticklabels(yticks, fontsize=ctx['fontsize'])
        # span = np.max(yticks) - np.min(yticks)
        # ax[ii].set_ylim([np.min(yticks) - 0.25 * span, np.max(yticks) + 0.25 * span])
        # ax[ii].set_xlim([0, len(means) - 1])

        ax[ii].set_title(plotting_datas[first_key][group][ii]['meta']['question'], fontsize=ctx['fontsize'])

        if ii == 0:
            title_height = utils.get_render_size(plotting_datas[first_key][group][ii]['meta']['question'], ctx, x_size=False)
            ax[ii].legend(ncol=2, bbox_to_anchor=(0, 1 + title_height + 0.2), loc='lower left', frameon=True, fontsize=ctx['fontsize_stats'])

    # save plot
    fig.savefig(
        f"{ctx['output_directory']}/{ctx['output_name']}_{xx}.{ctx['format']}",
        bbox_inches='tight', transparent=False)
    plt.close()


