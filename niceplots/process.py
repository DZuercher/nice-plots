# Authors: Dominik Zuercher, Valeria Glauser

import numpy as np
from niceplots import utils
from niceplots import parser
from tqdm import tqdm
import logging
LOGGER = logging.getLogger(__name__)


def parse_mapping(data, mapping, ctx, nbins):
    """
    Extract a mapping from codes to labels for variable var_name.
    Also chek if giving no answer is allowed for this variable.
    :param data: Data
    :param mapping: The string from the codebook describing 
    the code mapping.
    :param ctx: Configuration instance
    :param nbins: Number of bins used to break up numerical ranges.
    """
    contains_no_answer = False
    if mapping.strip() == 'none':
        # no mapping to text required.
        # Just break up numerical range into nbins linearly spaced bins
        ms = {'bins': np.linspace(
            np.min(data) - 0.5, np.max(data) + 0.5, nbins + 1)}
    else:
        mappings = mapping.split('\n')
        ms = []
        for ma in mappings:
            m = {}
            code = int(ma.split('=')[0])
            if (code == ctx['no_answer_code']):
                contains_no_answer = True
                continue
            m['code'] = code
            label = ma.split('=')[1]
            # remove leading and trailing whitespaces
            m['label'] = label.strip()
            ms.append(m)
            
        # sort by codes
        codes = []
        for entry in ms:
            codes.append(int(entry['code']))
        codes = np.asarray(codes)
        idx = np.argsort(codes)
        ms = np.asarray(ms)[idx]

    return ms, contains_no_answer


def get_meta(var_idx, ctx, data, codebook):
    """
    Extracts necessary meta data for the variables from the codebook.
    :param var_idx: The index of the variable in the codebook
    :param ctx: Configuration instance.
    :param data: Data table.
    :param codebook: Codebook
    :return : Dictionary containing the meta data for the variable in question.
    """
    # get question text
    meta = {'question': np.asarray(
        codebook[ctx['question_label']], dtype=str)[var_idx]}

    # get missing code
    meta['missing_code'] = np.asarray(
        codebook[ctx['missing_label']], dtype=int)[var_idx]

    # get the code mapping (numerical answer to text conversion) 
    variable_name = np.asarray(
        codebook[ctx['name_label']], dtype=str)[var_idx]
    meta['mapping'], contains_no_answer = parse_mapping(
        data[variable_name], np.asarray(
            codebook[ctx['mapping_label']], dtype=str)[var_idx],
        ctx, codebook['nbins - nice-plots'][var_idx])

    # get additional plotting configurations (color scheme, etc.)
    for key in ctx['additional_codebook_entries']:
        meta[key] = np.asarray(codebook[key + ' - nice-plots'],
                               dtype=str)[var_idx]
    return meta, contains_no_answer


def parse_filter_functions(data, codebook, ctx):
    """
    Extract filter expressions from config file.
    Convert to boolean filters and list of filter category names.
    :param data: Data table
    :param codebook: Codebook
    :param ctx: Configuration instance
    :return : A tuble with two lists (filter category names, boolean filters)
    """
    filters = ctx['filters']

    if len(filters.keys()) == 0:
        # No filters specified -> just one category with key '' and all participants
        return ([''], [np.ones(data.shape[0], dtype=bool)])
    else:
        f_names = []
        fs = []
        for f_name in list(filters.keys()):
            f_names.append(f_name)
            f = filters[f_name]
            # replace all variable names (cannot fail due to check in config readin step)
            f = parser.get_filter_from_string(f, codebook[ctx['name_label']])
            # evaluate filter expression -> boolean filter
            idx = eval(f)            
            fs.append(idx)
        return (f_names, fs)


def process_data(data, codebook, ctx):
    """
    Preprocesses data and codebook for subsequent plotting.
    :param data: Data (pandas data frame)
    :param codebook: Codebook (pandas data frame)
    :param ctx: Configuration instance
    :return : Preprocessed data for plotting. 
    Structure = [data for question block 1, data for question block 2, ...]. 
    Where data for question block i = {filter category 1 : [data for variable 1, ...], 
    filter category 2: [...], ...} and data for 
    variable i = {'meta': {meta data}, 'data': [answer 1, answer 2, ...]}.
    All answers that are either missing value or no answer are removed from the
    final data but the number of no answers are stored in the meta data.
    Also potential NaN values are removed.
    """
    LOGGER.debug("Starting preprocessing data for plotting")

    # break up data into categories based on filter expressions
    category_labels, categories = parse_filter_functions(
        data, codebook, ctx)

    # get the question block ids from the codebook
    block_id_label = ctx['block_id_label']
    block_ids = np.asarray(codebook[block_id_label], dtype=int)
    LOGGER.info(
        f"Found {len(np.unique(block_ids[block_ids > -1]))} "
        "question blocks.")

    # break up data into question blocks (1 plot per block)
    global_plotting_data = []
    for block_id in np.unique(block_ids):
        # ignore negativ block_ids
        if block_id < 0.:
            continue

        # variables belonging to the block
        variable_indices = np.where(block_ids == block_id)[0]

        plotting_data = {}
        # loop over filter categories
        for ii, cat in enumerate(categories):
            p_d = []

            # loop over the variables in the question block
            for var_idx in variable_indices:
                # get variable name from codebook
                variable_name = np.asarray(
                    codebook[ctx['name_label']], dtype=str)[var_idx]

                # get the data for the variable from the data table
                d = np.asarray(data[variable_name][cat])

                # get question meta data (missing value, code mapping, etc.)
                meta, contains_no_answer = get_meta(
                    var_idx, ctx, data, codebook)

                # ignore missing values
                d = d[np.logical_not(np.isclose(d, meta['missing_code']))]

                # remove potential NaN values
                d = d[np.logical_not(np.isnan(d))]

                # filter out no answers but add number of no answers to meta
                if contains_no_answer:
                    meta['no_answer'] = d[
                        np.isclose(d, ctx['no_answer_code'])].size
                    d = d[np.logical_not(
                        np.isclose(d, ctx['no_answer_code']))]

                # add to plotting data for this category
                p_d.append({'meta': meta, 'data': d})

            # add to plotting data for this question block 
            plotting_data[category_labels[ii]] = p_d
        # add data for the question block to global plotting data
        global_plotting_data.append(plotting_data)

        # logging
        LOGGER.debug('+'*120 + '\n')
        LOGGER.debug(f"Plotting meta data for question block {ii}: \n")
        LOGGER.debug("Questions: \n")
        questions = [f"{plotting_data[category_labels[0]][xx]['meta']['question']}" for xx in range(len(variable_indices))]
        n_questions = len(questions)
        for xx, q in enumerate(questions):
            if xx == n_questions - 1:
                LOGGER.debug(f'{q} \n')
            else:
                LOGGER.debug(q)
        meta = plotting_data[category_labels[0]][0]['meta']
        LOGGER.debug("Meta data: \n")
        for m in meta.items():
            if m[0] == 'question':
                continue
            elif m[0] == 'mapping':
                LOGGER.debug("mapping: ")
                for ma in m[1]:
                    LOGGER.debug(f"\t {ma['code']} : {ma['label']}")
            else:
                LOGGER.debug(f"{m[0]} : {m[1]}")
    LOGGER.debug('+'*120 + '\n')
    return global_plotting_data
