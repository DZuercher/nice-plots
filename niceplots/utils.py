# Authors: Dominik Zuercher, Valeria Glauser
import os
import logging
import sys
import matplotlib.pyplot as plt
import hyphen
from hyphen.textwrap2 import fill
import numpy as np
import logging
LOGGER = logging.getLogger(__name__)

lang = 'de_DE'
hyp = hyphen.Hyphenator(lang)


def get_render_size(object, ctx, x_size=True):
    """
    Returns width of a text.
    :param object: String to render
    :param ctx: Configuration instance
    :return : Width of text in Axes coordinates
    """

    # load cache
    if x_size:
        cache_file = os.path.expanduser(
            '~/.cache/nice-plots/object_render_sizes.npy')
        if os.path.exists(cache_file):
            cache = np.load(cache_file)
        else:
            cache = np.asarray([['', 0]], dtype=('str', 'int'))

        if object in cache[:, 0]:
            width = cache[cache[:, 0] == object, 1]
            width = float(width)
        else:
            figsize = (ctx['plot_width'], 10)
            f = plt.figure(figsize=figsize)
            rend = f.canvas.get_renderer()
            t = plt.text(0.5, 0.5, object, fontsize=ctx['fontsize'])
            extent = t.get_window_extent(renderer=rend)
            ax = f.gca()
            extent = extent.transformed(ax.transAxes.inverted())
            plt.close(f)
            width = np.abs(extent.width)
            cache = np.vstack((cache, [[object, width]]))
            np.save(cache_file, cache)
        return width
    else:
        cache_file = os.path.expanduser(
            '~/.cache/nice-plots/object_render_heights.npy')
        if os.path.exists(cache_file):
            cache = np.load(cache_file)
        else:
            cache = np.asarray([['', 0]], dtype=('str', 'int'))

        if object in cache[:, 0]:
            width = cache[cache[:, 0] == object, 1]
            width = float(width)
        else:
            figsize = (ctx['plot_width'], 10)
            f = plt.figure(figsize=figsize)
            rend = f.canvas.get_renderer()
            t = plt.text(0.5, 0.5, object, fontsize=ctx['fontsize'])
            extent = t.get_window_extent(renderer=rend)
            ax = f.gca()
            extent = extent.transformed(ax.transAxes.inverted())
            plt.close(f)
            width = np.abs(extent.height)
            cache = np.vstack((cache, [[object, width]]))
            np.save(cache_file, cache)
        return width


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


def get_stats(d, meta):
    if d.size > 0:
        st = 'n = {}\nm = {:.2f}\ns = {:.2f}'.format(
            d.size, np.mean(d), np.std(d))
        if 'no_answer' in meta.keys():
            st += '\nE = {}'.format(meta['no_answer'])

    else:
        st = '{:<9}'.format('n = {}'.format(d.size))
    return st


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


def wrap_text(text, width=60):
    cache_file = os.path.expanduser('~/.cache/nice-plots/text_wrap.npy')
    if os.path.exists(cache_file):
        cache = np.load(cache_file)
    else:
        cache = np.asarray([['', '']], dtype=('str', 'str'))
    if text in cache[:, 0]:
        return cache[cache[:, 0] == text, 1][0]
    else:
        wrapped = fill(text, width=width, use_hyphenator=hyp)
        cache = np.vstack((cache, [[text, wrapped]]))
        np.save(cache_file, cache)
        return wrapped

def inches_to_axispixels_size(size, fig, ax, dim='x'):
    """Given size of an object in inches returns the size of the object 
    in pixels in the specified dimesion of the plot (x or y)"""
    dpi = fig.dpi
    zero_point = ax.transAxes.inverted().transform((0, 0)) # reference point

    size = np.abs(size)
    if dim == 'x':
        phys_size = (ax.transAxes.inverted().transform(
            (size * dpi, 0)) - zero_point)[0]
        return np.abs(phys_size)
    elif dim == 'y':
        phys_size = (ax.transAxes.inverted().transform(
            (0, size* dpi)) - zero_point)[1]
        return np.abs(phys_size)
    else:
        raise ValueError("dim must be x or y.")

def axispixels_to_figurepixels_position(pos, ax): 
    figure_pos = ax.figure.transFigure.inverted().transform(
        ax.transData.transform(pos))
    return figure_pos

def axispixels_to_figurepixels_size(size, ax, dim='x'): 
    zero_point = ax.figure.transFigure.inverted().transform(
        ax.transData.transform((0, 0)))

    size = np.abs(size)
    if dim == 'x':
        fig_size = ax.figure.transFigure.inverted().transform(
            ax.transData.transform((size, 0)))
        fig_size = (fig_size - zero_point)[0]
        return np.abs(fig_size)
    elif dim == 'y':
        fig_size = ax.figure.transFigure.inverted().transform(
            ax.transData.transform((0, size)))
        fig_size = (fig_size - zero_point)[1]
        return np.abs(fig_size)
    else:
        raise ValueError("dim must be x or y.")