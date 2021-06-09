# Authors: Dominik Zuercher, Valeria Glauser

import os
import logging
import sys
import matplotlib.pyplot as plt
import hyphen
from hyphen.textwrap2 import fill
import numpy as np


def init_logger(filepath, logging_level='info'):
    """
    Initializes a logger instance for a file.

    :param filepath: The path of the file for which the logging is done.
    :param logging_level: The logger level
                          (critical, error, warning, info or debug)
    :return: Logger instance
    """
    logger = logging.getLogger(os.path.basename(filepath)[:10])

    if len(logger.handlers) == 0:
        log_formatter = logging.Formatter(
            "%(asctime)s %(name)0.10s %(levelname)0.3s   %(message)s ",
            "%y-%m-%d %H:%M:%S")
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)
        logger.propagate = False
        set_logger_level(logger, logging_level)

    return logger


def set_logger_level(logger, level):
    """
    Sets the global logging level. Meassages with a logging level below will
    not be logged.

    :param logger: A logger instance.
    :param logging_level: The logger severity
                          (critical, error, warning, info or debug)
    """

    logging_levels = {'critical': logging.CRITICAL,
                      'error': logging.ERROR,
                      'warning': logging.WARNING,
                      'info': logging.INFO,
                      'debug': logging.DEBUG}

    logger.setLevel(logging_levels[level])


def get_render_size(object, ctx, x_size=True):
    """
    Returns width of a text.
    :param object: String to render
    :param ctx: Configuration instance
    :return : Width of text in Axes coordinates
    """

    # load cache
    if x_size:
        cache_file = os.path.expanduser('~/.cache/nice-plots/object_render_sizes.npy')
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
        cache_file = os.path.expanduser('~/.cache/nice-plots/object_render_heights.npy')
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


def wrap_text(text, width=60, lang='de_DE'):
    hyp = hyphen.Hyphenator(lang)
    return fill(text, width=width, use_hyphenator=hyp)
