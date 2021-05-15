# Authors: Dominik Zuercher, Valeria Glauser

import yaml
import os
import pathlib
import pandas as pd
import shutil
from niceplots import utils

LOGGER = utils.init_logger(__file__)


# TODP
def check_config(ctx):
    """
    Checks if all attributes of the configuration instance are valid.
    :param ctx: Directory with configuration objects.
    """

    pass


def load_config(config_path, output_directory, output_name):
    """
    Loads the default config file from config directory.
    Arguments can be overriden by a user defined config file.
    The validity of the passed arguments is checked.
    :param config_path: Path to the user defined config file.
    :param output_directory: Output directory.
    :return : Directory with configuration objects.
    """

    # load default config file
    # default_config_path = str(pathlib.Path(__file__).parent.absolute())
    # default_config_path += '/../config/default_config.yml'
    default_config_path = config_path

    with open(default_config_path, 'r') as f:
        ctx = yaml.load(f, yaml.FullLoader)
    LOGGER.info(
        f"Loaded default configuration file from {default_config_path}")

    check_config(ctx)

    # load user defined config file

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

    check_config(ctx)

    ctx['output_name'] = output_name
    ctx['config_file'] = output_config
    ctx['output_directory'] = output_directory
    return ctx


# TODO
def check_codebook(codebook):
    """
    Checks validity of codebook.
    :param codebook: The codebook that should be checked.
    """
    pass


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
    output_codebook_path = ctx['output_directory'] + "/codebook.csv"
    initialize = False
    if not os.path.exists(output_codebook_path):
        shutil.copyfile(codebook_path, output_codebook_path)
        LOGGER.info(
            f"Copied codebook {codebook_path} -> {output_codebook_path}")
        initialize = True
    raw_codebook = pd.read_csv(output_codebook_path)
    LOGGER.info(
        f"Loaded codebook from {output_codebook_path}")

    check_codebook(raw_codebook)

    # add some additional columns to the codebook
    additional_codebook_entries = ['color_scheme', 'invert']

    if initialize:
        # add the plotting options columns to the codebook
        for key in additional_codebook_entries:
            raw_codebook[key + " - nice-plots"] = ctx[key]
            LOGGER.info(f"Added additional column {key} - nice-plots to "
                        f"codebook. Initialized with value {ctx[key]}")

    # write output codebook to the output directory
    raw_codebook.to_csv(output_codebook_path, index=False)

    codebook = raw_codebook
    ctx['codebook_path'] = output_codebook_path
    ctx['additional_codebook_entries'] = additional_codebook_entries
    return codebook


def load_data(ctx, data_path):
    """
    Load and preprocess the data table.
    :param ctx: Configuration instance.
    :param data_path: Path to data file.
    :return : Data table
    """
    raw_data = pd.read_csv(data_path)
    LOGGER.info(f"Loaded data table from file {data_path}")

    # potentially some pre-processing
    data = raw_data
    return data
