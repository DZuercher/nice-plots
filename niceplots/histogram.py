# Authors: Dominik Zuercher, Valeria Glauser

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
import numpy as np
from niceplots import utils
import frogress
from multiprocessing import Pool
from functools import partial
import matplotlib as mpl

LOGGER = utils.init_logger(__file__)


def plot_histograms(xx, global_plotting_data, ctx):
    plotting_data = global_plotting_data[xx]

    n_questions = len(plotting_data[list(plotting_data.keys())[0]])

    # check if this can be made into a single histogram
    if n_questions == 1:
        single_histogram = True
        multi_histogram = False
        LOGGER.info(f"Question block {xx} contains only a single question "
                    "-> Producing a single histogram for this.")
    else:
        key0 = list(plotting_data.keys())[0]
        if len(plotting_data[key0][0]['meta']['mapping']) == 2:
            multi_histogram = True
            single_histogram = False
            LOGGER.info(f"Question block {xx} contains multiple questions "
                        "with 2 possible answers each"
                        "-> Interpreting as binary and combining "
                        "into a single histogram.")
            LOGGER.warn(
                "CAUTION: I assume that code = 1 means Yes and code"
                " = 2 means No!")
        else:
            LOGGER.warn(f"Cannot convert question block {xx} into "
                        "a histogram. Skipping...")
            return

    if single_histogram:
        # loop over filter categories
        histogram_data = []
        for ii, key in enumerate(plotting_data.keys()):
            # get bin edges
            if ii == 0:
                if 'bins' in plotting_data[key][0]['meta']['mapping']:
                    # special handling
                    bins = plotting_data[key]['meta']['mapping']['bins']
                else:
                    bins = [
                        plotting_data[key]['meta']['mapping'][jj]['code']
                        - 0.5 for jj in range(
                            len(plotting_data[key]['meta']['mapping']))]
                    bins.append(bins[-1] + 0.5)
                bins = np.asarray(bins)

            d = plotting_data[key][0]['data'][np.logical_not(
                np.isnan(plotting_data[key][0]['data']))]
            d = d.astype(int)
            histogram_data.append(d)

    if multi_histogram:
        histogram_data = []
        lower = +np.inf
        upper = -np.inf
        # loop over filter categories
        for ii, key in enumerate(plotting_data.keys()):
            # loop over questions
            data = []
            for jj in range(len(plotting_data[key])):
                p_d = plotting_data[key][jj]
                d = p_d['data'][np.logical_not(np.isnan(p_d['data']))]
                d = d.astype(int)
                data += [ii for xx in range(len(d[d == 1]))]
            data = np.asarray(data)
            histogram_data.append(data)
            lower = np.min([lower, np.min(data)])
            upper = np.max([upper, np.max(data)])

        # set bins
        bins = np.arange(lower - 0.5, upper + 1.5)

    # initialize canvas
    figsize = (ctx['plot_width'], ctx['plow_width'])
    fig, ax = plt.subplots(figsize=figsize)

    plt.hist(histogram_data, bins=bins)

    # save plot
    fig.savefig(
        f"{ctx['output_directory']}/{ctx['output_name']}_{xx}.pdf",
        bbox_inches='tight')


def make_plots(global_plotting_data, ctx, serial):
    if not serial:
        LOGGER.info("Running in parallel mode")
        with Pool() as p:
            p.map(
                partial(plot_histograms,
                        global_plotting_data=global_plotting_data, ctx=ctx),
                list(range(len(global_plotting_data))))
    else:
        LOGGER.info("Running in serial mode")
        # loop over question blocks and produce one plot
        # for each question block
        for xx, plotting_data in frogress.bar(enumerate(global_plotting_data)):
            plot_histograms(xx, global_plotting_data, ctx)
