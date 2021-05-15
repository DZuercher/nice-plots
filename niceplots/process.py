# Authors: Dominik Zuercher, Valeria Glauser

import numpy as np
from niceplots import utils
import frogress

LOGGER = utils.init_logger(__file__)


def parse_mapping(data, mapping, var_name):
    """
    Extract a mapping from codes to labels.
    """
    try:
        if mapping.strip() == 'none':
            nbins = 5
            ms = {'bins': np.linspace(
                np.min(data) - 0.5, np.max(data) + 0.5, nbins + 1)}
        else:
            mappings = mapping.split('\n')
            ms = []
            for ma in mappings:
                m = {}
                code = int(ma.split('=')[0])
                if code == 0:
                    continue
                m['code'] = code
                label = ma.split('=')[1]
                # remove leading and trailing whitespaces
                m['label'] = label.strip()
                ms.append(m)
        return ms
    except ValueError:
        raise ValueError(
            f"Your mapping {mapping} for variable {var_name} is ill-defined.")


def get_meta(var_idx, ctx, data, codebook):
    """
    Extracts necessary meta data from the codebook.
    :param var_idx: The index of the variable in the codebook
    :param ctx: Configuration instance.
    :param data: Data table.
    :param codebook: Codebook
    :return : Dictionary containing the meta data for the variable in question.
    """
    variable_name = np.asarray(
        codebook[ctx['name_label']], dtype=str)[var_idx]

    # get question name
    meta = {'question': np.asarray(
        codebook[ctx['question_label']], dtype=str)[var_idx]}

    # get the code -> text label mapping
    meta['mapping'] = parse_mapping(data[variable_name], np.asarray(
        codebook[ctx['mapping_label']], dtype=str)[var_idx], variable_name)

    # get the plotting configurations
    for key in ctx['additional_codebook_entries']:
        meta[key] = np.asarray(codebook[key + ' - nice-plots'],
                               dtype=str)[var_idx]
    return meta


def parse_filter_functions(data, ctx):
    """
    Extract filter expressions from config file.
    Convert to boolean filters and list of filter names.
    :param data: Data table
    :param ctx: Configuration instance
    :return : A tuble with two lists (filter category names, boolean filters)
    """
    filters = ctx['filters']

    if len(filters.keys()) == 0:
        return ([''], [np.ones(data.shape[0], dtype=bool)])
    else:
        f_names = []
        fs = []
        for f_name in list(filters.keys()):
            f_names.append(f_name)
            f = filters[f_name]
            var = f.split(' ')[0].strip()
            op = f.split(' ')[1].strip()
            val = f.split(' ')[2].strip()
            exp = f'np.asarray(data["{var}"]) {op} {val}'
            idx = eval(exp)
            fs.append(idx)
        return (f_names, fs)


# TODO
def check_codeblocks():
    # check consistency
    # within one block all the meta data must be equivalent
    pass


def process_data(data, codebook, ctx):
    LOGGER.info("Preprocessing data for plotting.")
    category_labels, categories = parse_filter_functions(
        data, ctx)

    block_id_label = ctx['block_id_label']
    # check if exists
    if block_id_label not in codebook:
        raise Exception(
            f"The codebook does not contain a column named {block_id_label} "
            "-> Cannot group variables into blocks.")
    # define the variable blocks
    block_ids = np.asarray(codebook[block_id_label], dtype=int)
    LOGGER.info(
        f"Found {len(np.unique(block_ids[block_ids > -0.1]))} "
        "question blocks.")

    # break up data into question blocks
    global_plotting_data = []
    for block_id in frogress.bar(np.unique(block_ids)):
        # skip block_id = -1
        if block_id < 0.:
            continue

        variable_indices = np.where(block_ids == block_id)[0]

        plotting_data = {}
        # loop over filter categories
        for ii, cat in enumerate(categories):
            p_d = []

            # loop over the variables in the question block
            for var_idx in variable_indices:
                variable_name = np.asarray(
                    codebook[ctx['name_label']], dtype=str)[var_idx]

                # get the necessary data from the data table
                if variable_name not in data:
                    raise ValueError(
                        f"Did not find the column {variable_name} "
                        "in your data")

                d = np.asarray(data[variable_name][cat])
                # get meta data
                meta = get_meta(var_idx, ctx, data, codebook)
                p_d.append({'meta': meta, 'data': d})

            plotting_data[category_labels[ii]] = p_d
        global_plotting_data.append(plotting_data)

    check_codeblocks()

    return global_plotting_data
