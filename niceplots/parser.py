# Authors: Dominik Zuercher, Valeria Glauser

import logging
import os
import shutil

import numpy as np
import pandas as pd
import yaml

LOGGER = logging.getLogger(__name__)


def isnumber(x):
    """
    Checks if string x is a numercial number.
    :param x: String to check.
    :return : Returns true if x is a number and False otherwise.
    """
    try:
        float(x)
        return True
    except ValueError:
        return False


def get_filter_from_string(f, variables):
    """
    Replaces the variable names in the string f that encodes the
    filter expressions to obtain valid filter expressions.
    :param f: String encoding the filters.
    :param variables: The different variable names used in the data.
    :return : Modified version of string f.
    """
    for var in reversed(sorted(variables, key=len)):
        ii = 0
        while 1:
            pos = f.find(var, ii)
            if pos > 0:
                if f[pos - 1] != '"':
                    f_ = f[:pos]
                    rep = f[pos:].replace(var, f'np.asarray(data["{var}"])', 1)
                    f = f_ + rep
                    ii = pos + len(var) + 20
                else:
                    ii = pos + len(var) + 3
            elif pos == 0:
                # need special handling for replace at beginning
                f = f.replace(var, f'np.asarray(data["{var}"])', 1)
                ii = pos + len(var) + 20
            else:
                break
    return f


def check_config(ctx, codebook, data):
    """
    Checks if all attributes of the configuration instance are valid.
    Note: data is used to evaluate the filter expressions.
    :param ctx: Directory with configuration objects.
    :param codebook: Codebook (pandas data frame)
    :param data: Data (pandas data frame)
    """
    # check that filters are correct
    filters = ctx["filters"]

    if len(filters.keys()) == 0:
        pass
    else:
        for f_name in list(filters.keys()):
            f = filters[f_name]
            # attempt to replace all variable names in filter expressions
            f = get_filter_from_string(f, codebook[ctx["name_label"]])
            try:
                eval(f)
            except KeyError:
                return (
                    f"Unable to process filter entry {f} in your config file. "
                    f"Some variables seem to not be present in your data."
                )
            except SyntaxError:
                return (
                    f"Unable to process filter entry {f}. "
                    f"Something with the Syntax is wrong."
                )
    return ""


def load_config(config_path, output_directory, output_name):
    """
    Loads the default config file from config_path.
    Overrides with values from local config file in output_directory.
    Creates the local config file in output_directory if it does not exist already.
    :param config_path: Path to the default config file.
    :param output_directory: Output directory.
    :return : Directory holding config values.
    """
    # load default config
    default_config_path = str(config_path)
    with open(default_config_path) as f:
        try:
            ctx = yaml.load(f, yaml.FullLoader)
        except Exception as e:
            status = f"Could not load default config file from path {default_config_path}. Error: {e}"
            return status
    LOGGER.debug(f"Loaded default configuration file from {default_config_path}")

    # check if config in output directory already exists, create otherwise
    output_config = f"{output_directory}/config_{output_name}.yml"
    if not os.path.exists(output_config):
        shutil.copyfile(config_path, output_config)
        LOGGER.info(
            f"Copied default config file to output directory: {config_path} -> {output_config}"
        )

    # load output config file
    with open(output_config) as f:
        try:
            user_ctx = yaml.load(f, yaml.FullLoader)
        except Exception as e:
            status = f"Could not load config file from path {output_config}. Error: {e}"
            return status
    LOGGER.info(f"Using configuration file in: {output_config}")

    # override defaults
    for obj in user_ctx:
        if obj in ctx:
            LOGGER.debug(
                "Overriding default value of config argument "
                f"{obj} -> {user_ctx[obj]}"
            )
            ctx[obj] = user_ctx[obj]

    # add some extra variables
    ctx["output_name"] = output_name
    ctx["config_file"] = output_config
    ctx["output_directory"] = output_directory

    LOGGER.debug("+" * 50 + " CONFIG " + "+" * 50)
    for item in ctx.items():
        LOGGER.debug(f"{item[0]} : {item[1]}")
    LOGGER.debug("+" * 108)

    return ctx


def check_codebook(codebook, ctx):
    """
    Checks validity of codebook.
    :param codebook: The codebook that should be checked (pandas data frame).
    :param ctx: Configuration instance.
    """
    # check that all required columns exist
    required_columns = [
        "block_id_label",
        "question_label",
        "name_label",
        "mapping_label",
        "missing_label",
    ]
    for col in required_columns:
        if ctx[col] not in codebook.columns:
            return (
                f"The column named {ctx[col]} corresponding to "
                f"the {col} entry in the configuration file does not exist "
                "in your codebook but is required by nice-plots. Aborting..."
            )

    block_id_label = ctx["block_id_label"]
    # define the variable blocks
    block_ids = np.asarray(codebook[block_id_label], dtype=int)

    # check for each question block if mapping is valid and consistent
    # throughout the block
    for block_id in np.unique(block_ids[block_ids >= 0]):
        variable_indices = np.where(block_ids == block_id)[0]

        # loop over mappings in block
        mappings = []
        for mapping in codebook[ctx["mapping_label"]][variable_indices]:
            if mapping.strip() == "none":
                continue
            else:
                try:
                    mappings_ = mapping.split("\n")
                    ms = []
                    for ma in mappings_:
                        m = {}
                        code = int(ma.split("=")[0])
                        if code == ctx["no_answer_code"]:
                            continue
                        m["code"] = code
                        label = ma.split("=")[1]
                        # remove leading and trailing whitespaces
                        m["label"] = label.strip()
                        ms.append(m)
                except:
                    return f"Unable to process code mapping {mapping}. Aborting..."
                for m in ms:
                    if not (isinstance(m["code"], int)):
                        return (
                            f"The code {m['code']} in code mapping {mapping} in your codebook"
                            "is not an integer. Aborting."
                        )
                    if not (m["code"] > 0):
                        return (
                            f"The code {m['code']} in code mapping {mapping} in your codebook"
                            "must be an integer larger than 0. Aborting."
                        )
            mappings.append(ms)

        # check consistency throughout the question black
        for ii, m in enumerate(mappings):
            if m != mappings[0]:
                return (
                    f"Problem in Codebook for question block "
                    f"{block_id}."
                    f"The code mappings for all variables in a question block must "
                    f"be the same, but I found the two mappings \n \n"
                    f"{codebook[ctx['name_label']][variable_indices[ii]]}:"
                    f" \n"
                    f"{m} \n \n and \n \n"
                    f"{codebook[ctx['name_label']][variable_indices[0]]}:"
                    f" \n"
                    f"{mappings[0]} "
                    f"\n \n to be unequal!"
                )
    return ""


def check_data(data, ctx, codebook):
    """
    Checks validity of data and removes non-numerical entries.
    :param data: The data that should be checked (pandas data frame).
    :param ctx: Configuration instance.
    :param codebook: The codebook (pandas data frame).
    :return : Processed data table
    """
    # check that required columns exist
    required_columns = codebook[ctx["name_label"]]
    for col in required_columns:
        if col not in data.columns:
            return (
                f"The column named {col} defined in your codebook "
                f"does not exist in your data. Aborting..."
            )

    # set all non numerical entries in data to NaN
    # string_filter = data.applymap(isnumber)
    # num_strings = np.asarray(string_filter).size \
    #     - np.sum(np.asarray(string_filter))
    # if num_strings > 0:
    #     LOGGER.warning(f"Found {num_strings} non-numerical values in "
    #                 "your data. Setting them to NaN.")
    # data = data[string_filter]
    # data = data.applymap(float)

    # check that data is in the range required by mappings
    block_id_label = ctx["block_id_label"]
    block_ids = np.asarray(codebook[block_id_label], dtype=int)
    for block_id in np.unique(block_ids[block_ids >= 0]):
        variable_indices = np.where(block_ids == block_id)[0]
        mapping = codebook[ctx["mapping_label"]][variable_indices[0]]
        if mapping.strip() == "none":
            continue
        else:
            mappings_ = mapping.split("\n")
            ms = []
            for ma in mappings_:
                code = int(ma.split("=")[0])
                ms.append(code)
            for var in variable_indices:
                d = data[codebook[ctx["name_label"]][var]]
                d = np.asarray(d, dtype=int)
                check = np.all(
                    (d >= np.min(ms)) & (d <= np.max(ms))
                    | np.isclose(d, codebook.at[var, ctx["missing_label"]])
                )
                if not check:
                    raise ValueError(
                        f"Some values in your data for variable {codebook[ctx['name_label']][var]} "
                        f"are outside of the range specified in the codebook."
                    )
    return data


def load_codebook(ctx, codebook_path):
    """
    Load and preprocess the codebook. If it exists loads the codebook from
    the output directory. Otherwise create it from the global one.
    The codebook gets checked for its validity.
    :param ctx: Configuration instance.
    :param codebook_path: Path to codebook file.
    :return : Codebook (pandas data frame)
    """
    # check if there is already a codebook in the output directory
    output_codebook_path = (
        f"{ctx['output_directory']}/codebook_{ctx['output_name']}.csv"
    )
    if os.path.exists(output_codebook_path):
        try:
            codebook = pd.read_csv(
                output_codebook_path,
                keep_default_na=False,
                sep=ctx["delimiter"],
                dtype="object",
            )
        except Exception as e:
            status = f"Could not load codebook file from path {output_codebook_path}. Error: {e}"
            return status
        initialize = False
    else:
        LOGGER.debug(
            f"Did not find a local codebook in {output_codebook_path}. Creating from global one."
        )
        # if isinstance(codebook_path, str):
        try:
            codebook = pd.read_csv(
                codebook_path,
                keep_default_na=False,
                sep=ctx["delimiter"],
                dtype="object",
            )
        except Exception as e:
            status = (
                f"Could not load codebook file from path {codebook_path}. Error: {e}"
            )
            return status
        LOGGER.debug(f"Loaded global codebook from: {codebook_path}")
        # else:
        #     codebook = codebook_path
        initialize = True

    # add some additional columns to the codebook
    additional_codebook_entries = [
        "color_scheme",
        "invert",
        "nbins",
        "unit",
        "bar_text_color",
    ]

    if initialize:
        # add the plotting options columns to the codebook
        for key in additional_codebook_entries:
            if f"{key} - nice-plots" not in codebook:
                codebook[key + " - nice-plots"] = ctx[key]
                LOGGER.debug(
                    f"Added additional column {key} - nice-plots to "
                    f"codebook. Initialized with value {ctx[key]}."
                )

    # add codebook realted variables to config instance
    ctx["codebook_path"] = output_codebook_path
    ctx["additional_codebook_entries"] = additional_codebook_entries

    # convert to numeric where necessary
    numeric_entries = ["nbins - nice-plots", ctx["missing_label"]]
    for key in numeric_entries:
        codebook[key] = pd.to_numeric(codebook[key])

    # check validity
    status = check_codebook(codebook, ctx)
    if len(status) > 0:
        return status

    # write output codebook to the output directory
    if initialize:
        try:
            codebook.to_csv(output_codebook_path, index=False)
        except Exception as e:
            status = f"Could not save codebook file to path {output_codebook_path}. Error: {e}"
            return status
        LOGGER.debug(
            f"Copied global codebook to local: {codebook_path} -> {output_codebook_path}"
        )
    LOGGER.info(f"Using codebook in: {output_codebook_path}")

    LOGGER.debug("+" * 50 + " CODEBOOK " + "+" * 50)
    LOGGER.debug("\n" + str(codebook.head()))
    LOGGER.debug("+" * 110)
    return codebook


def load_data(ctx, data_path, codebook):
    """
    Load and preprocess the data table from data_path.
    :param ctx: Configuration instance.
    :param data_path: Path to data file.
    :param codebook: The codebook (pandas data frame)
    :return : Data table (pandas data frame)
    """
    try:
        data = pd.read_csv(data_path, sep=ctx["delimiter"])
    except Exception as e:
        status = f"Could not load data file from path {data_path}. Error: {e}"
        return status
    LOGGER.info(f"Using data table in: {data_path}")

    # check validity and replace non-numerical entries
    data = check_data(data, ctx, codebook)

    LOGGER.debug("+" * 50 + " DATA " + "+" * 50)
    LOGGER.debug("\n" + str(data.head()))
    LOGGER.debug("+" * 106)
    return data
