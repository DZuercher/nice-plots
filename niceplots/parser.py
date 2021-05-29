# Authors: Dominik Zuercher, Valeria Glauser

import yaml
import os
import pandas as pd
import shutil
from niceplots import utils
import numpy as np

LOGGER = utils.init_logger(__file__)


def isnumber(x):
    try:
        float(x)
        return True
    except:
        return False


def check_config(ctx, codebook, data):
    """
    Checks if all attributes of the configuration instance are valid.
    :param ctx: Directory with configuration objects.
    :param codebook: Codebook
    :param data: Data array
    """
   # check that filters are correct
    filters = ctx['filters']

    if len(filters.keys()) == 0:
        pass
    else:
        for f_name in list(filters.keys()):
            f = filters[f_name]
            var = f.split(' ')[0].strip()
            op = f.split(' ')[1].strip()
            val = f.split(' ')[2].strip()
            exp = f'np.asarray(data["{var}"]) {op} {val}'
            try:
                eval(exp)
            except KeyError:
                raise Exception(
                    f"Unable to process filter entry {f}. "
                    f"The column {var} does not exist in your data.")
            except SyntaxError:
                raise Exception(
                    f"Unable to process filter entry {f}. "
                    f"Something with the Syntax is wrong.")


def load_config(config_path, output_directory, output_name):
    """
    Loads the default config file from config directory.
    Arguments can be overriden by a user defined config file.
    The validity of the passed arguments is checked.
    :param config_path: Path to the user defined config file.
    :param output_directory: Output directory.
    :return : Directory with configuration objects.
    """

    # load default config
    default_config_path = config_path

    with open(default_config_path, 'r') as f:
        ctx = yaml.load(f, yaml.FullLoader)
    LOGGER.info(
        'Loaded default configuration file from {}'.format(default_config_path))

    # check if config in output directory already exists
    output_config = output_directory + '/config_{}.yml'.format(output_name)
    if not os.path.exists(output_config):
        shutil.copyfile(config_path, output_config)
        LOGGER.info(f"Copied config file {config_path} -> {output_config}")
    with open(output_config, 'r') as f:
        user_ctx = yaml.load(f, yaml.FullLoader)
    LOGGER.info(
        f"Loaded user configuration file from {output_config}")

    # override defaults
    for obj in user_ctx:
        if obj in ctx:
            LOGGER.info(
                "Overriding default value of argument "
                f"{obj} -> {user_ctx[obj]}")
            ctx[obj] = user_ctx[obj]

    ctx['output_name'] = output_name
    ctx['config_file'] = output_config
    ctx['output_directory'] = output_directory
    return ctx


def check_codebook(codebook, ctx):
    """
    Checks validity of codebook.
    :param codebook: The codebook that should be checked.
    :param ctx: Configuration instance.
    """

    # check that all required columns are there
    required_columns = ['block_id_label', 'question_label', 'name_label',
                        'mapping_label', 'missing_label']
    for col in required_columns:
        if ctx[col] not in codebook.columns:
            raise Exception(
                f"The coumn named {ctx[col]} corresponding to "
                f"the {col} entry in the configuration file does not exist "
                "in your codebook but is required by nice-plots. Aborting...")

    block_id_label = ctx['block_id_label']
    # define the variable blocks
    block_ids = np.asarray(codebook[block_id_label], dtype=int)

    # check for each question block if mapping is valid and consistent
    # throughout the block
    for block_id in np.unique(block_ids[block_ids >= 0]):
        variable_indices = np.where(block_ids == block_id)[0]

        # loop over mappings in block
        mappings = []
        for mapping in codebook[ctx['mapping_label']][variable_indices]:
            if mapping.strip() == 'none':
                continue
            else:
                try:
                    mappings_ = mapping.split('\n')
                    ms = []
                    for ma in mappings_:
                        m = {}
                        code = int(ma.split('=')[0])
                        # CHECK THIS!
                        if code == 0:
                            continue
                        m['code'] = code
                        label = ma.split('=')[1]
                        # remove leading and trailing whitespaces
                        m['label'] = label.strip()
                        ms.append(m)
                except:
                    raise Exception(
                        f"Unable to process mapping {mapping}. Aborting...")
                for m in ms:
                    if not (isinstance(m['code'], int)):
                        raise Exception(
                            f"The code {m['code']} in mapping {mapping} "
                            "is not an integer. Aborting.")
                    if not (m['code'] > 0):
                        raise Exception(
                            f"The code {m['code']} in mapping {mapping} "
                            "must be an integer larger than 0. Aborting.")
            mappings.append(ms)
        # check consistency
        for ii, m in enumerate(mappings):
            if m != mappings[0]:
                raise Exception(
                    f"Problem in Codebook for question block {block_id}."
                    "The mappings for all variables in a question block must "
                    "be the same, but I found mappings the two mappings \n \n"
                    f"{codebook[ctx['name_label']][variable_indices[ii]]}:"
                    " \n"
                    f"{m} \n \n and \n \n"
                    f"{codebook[ctx['name_label']][variable_indices[0]]}:"
                    " \n"
                    f"{mappings[0]} "
                    "\n \n to be unequal!")


def check_data(data, ctx, codebook):
    """
    Checks validity of data.
    :param data: The data that should be checked.
    :param ctx: Configuration instance.
    :param codebook: The codebook.
    """

    # check that required columns are there
    required_columns = codebook[ctx['name_label']]
    for col in required_columns:
        if col not in data.columns:
            raise Exception(
                f"The coumn named {col} defined in your codebook "
                f"does not exist in your data. Aborting...")

    # set all non numerical entries in data to NaN
    string_filter = data.applymap(isnumber)
    num_strings = np.asarray(string_filter).size \
        - np.sum(np.asarray(string_filter))
    LOGGER.warning(f"Found {num_strings} non-numerical values in "
                   "your data. Setting them to NaN.")
    data = data[string_filter]
    data = data.applymap(float)


def load_codebook(ctx, codebook_path):
    """
    Load and preprocess the codebook. If it exists loads the codebook from
    the output directory. Finished codebook gets written to the output
    directory. The codebook gets checked for its validity.
    :param ctx: Configuration instance.
    :param codebook_path: Path to codebook file.
    :return : Codebook
    """

    # check if there is already a codebook in the output directory
    output_codebook_path = ctx['output_directory'] \
        + f"/codebook_{ctx['output_name']}.csv"
    initialize = False
    if not os.path.exists(output_codebook_path):
        shutil.copyfile(codebook_path, output_codebook_path)
        LOGGER.info(
            f"Copied codebook {codebook_path} -> {output_codebook_path}")
        initialize = True
    raw_codebook = pd.read_csv(output_codebook_path, keep_default_na=False,
                               sep=ctx['delimiter'], dtype='object')

    LOGGER.info(
        f"Loaded codebook from {output_codebook_path}")

    # add some additional columns to the codebook
    additional_codebook_entries = ['color_scheme', 'invert', 'nbins', 'unit']

    if initialize:
        # add the plotting options columns to the codebook
        for key in additional_codebook_entries:
            raw_codebook[key + " - nice-plots"] = ctx[key]
            LOGGER.info(f"Added additional column {key} - nice-plots to "
                        f"codebook. Initialized with value {ctx[key]}")

    codebook = raw_codebook
    ctx['codebook_path'] = output_codebook_path
    ctx['additional_codebook_entries'] = additional_codebook_entries

    # convert to numeric where necessary
    numeric_entries = ['nbins - nice-plots', ctx['missing_label']]
    for key in numeric_entries:
        codebook[key] = pd.to_numeric(codebook[key])

    check_codebook(codebook, ctx)

    # write output codebook to the output directory
    codebook.to_csv(output_codebook_path, index=False)
    return codebook


def load_data(ctx, data_path, codebook):
    """
    Load and preprocess the data table.
    :param ctx: Configuration instance.
    :param data_path: Path to data file.
    :return : Data table
    """
    raw_data = pd.read_csv(data_path, sep=ctx['delimiter'])
    LOGGER.info(f"Loaded data table from file {data_path}")

    # potentially some pre-processing
    data = raw_data

    check_data(data, ctx, codebook)
    return data
