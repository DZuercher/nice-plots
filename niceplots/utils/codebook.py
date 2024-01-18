import os
from pathlib import Path

import pandas as pd

from niceplots.utils.config import Configuration
from niceplots.utils.nice_logger import init_logger, set_logger_level

logger = init_logger(__file__)


class CodeBook:
    def __init__(self, config: Configuration, path_output_codebook: Path) -> None:
        logger.info("Initializing nice-plots codebook.")

        self.delimiter = config.data.delimiter
        self.codebook_columns = {
            "variable": str,
            "label": str,
            "value_map": str,
            "block": int,
            "missing_label": object,
        }
        self.additional_config_columns = {
            "plotting.nbins": int,
            "plotting.unit": str,
            "barplots.text_color": str,
            "barplots.color_scheme": str,
            "barplots.invert": bool,
            "lineplots.invert": bool,
            "data.no_answer_code": object,
        }
        self.codebook = pd.DataFrame(
            columns=list(self.codebook_columns.keys())
            + list(self.additional_config_columns.keys()),
        )
        # set datatypes
        for col, type in {
            **self.codebook_columns,
            **self.additional_config_columns,
        }.items():
            self.codebook[col] = self.codebook[col].astype(type)
        self.path_codebook = path_output_codebook
        self.name_label = config.data.name_label
        self.question_label = config.data.question_label
        self.block_id_label = config.data.block_id_label
        self.mapping_label = config.data.mapping_label
        self.missing_label = config.data.missing_label

        # read defaults from config
        self.config_defaults: dict = {}
        for col in self.additional_config_columns.keys():
            self.config_defaults[col] = getattr(
                getattr(config, col.split(".")[0]), col.split(".")[1]
            )

    def readin_codebook_file(self, codebook_path: Path) -> None:
        df = pd.read_csv(
            codebook_path,
            sep=self.delimiter,
        )

        self.codebook["variable"] = df[self.name_label]
        self.codebook["label"] = df[self.question_label]
        self.codebook["value_map"] = df[self.mapping_label]
        self.codebook["value_map"] = self.parse_value_mapping(self.codebook)
        self.codebook["block"] = df[self.block_id_label]
        self.codebook["missing_label"] = df[self.missing_label]

        # Add additional columns based on config
        for name, value in self.config_defaults.items():
            self.codebook[name] = value

        self.check()

    def parse_value_mapping(self, df_in: pd.DataFrame) -> pd.Series:
        mappings_parsed = []
        for i, row in df_in.iterrows():
            try:
                if row.value_map == "none":
                    mapping_parsed = row.value_map
                else:
                    map_strings = row.value_map.split("\n")
                    m = {}
                    for ma in map_strings:
                        code = int(ma.split("=")[0].strip())
                        if code == row["data.no_answer_code"]:
                            continue
                        m[code] = ma.split("=")[1].strip()
                    mapping_parsed = str(m)
            except ValueError as error:
                raise ValueError(
                    f"Unable to process code mapping {row.value_map} in Codebook Line {i}"
                ) from error
            mappings_parsed.append(mapping_parsed)

        return pd.Series(mappings_parsed)

    def readin_niceplots_codebook_file(self, codebook_path: Path) -> None:
        self.codebook = pd.read_csv(
            codebook_path,
            sep=self.delimiter,
        )

        self.path_codebook = Path(codebook_path)
        self.check()

    def write_output_codebook(self) -> None:
        self.codebook.to_csv(self.path_codebook, index=False)

    def check(self) -> None:
        # check that all required columns exist in codebook
        for col in list(self.codebook_columns.keys()) + list(
            self.additional_config_columns.keys()
        ):
            if col not in self.codebook.columns:
                raise ValueError(
                    f"Your codebook does not contain column {col}. But it is required by nice-plots."
                )

        # assert uniqueness of value map within a block
        unique_map_counts = self.codebook.groupby("block")["value_map"].nunique()
        if not unique_map_counts.loc[unique_map_counts.index != -1].max() == 1:
            mismatched_blocks = unique_map_counts[unique_map_counts > 1]
            for block in mismatched_blocks:
                raise ValueError(
                    f"Code mapping not unique for question block {block}. Found mappings: {self.codebook[self.codebook.block == block].value_map.drop_duplicates()}"
                )

    def summarize(self):
        logger.info(f"Got codebook defining {self.codebook.shape[0]} variables.")
        blocks = self.codebook.block.unique()
        blocks = blocks[blocks != -1]
        logger.info(f"Got codebook defining {len(blocks)} blocks.")


def setup_codebook(
    config: Configuration,
    path_codebook: Path,
    write_codebook: bool = False,
    full_rerun: bool = True,
) -> CodeBook:
    set_logger_level(logger, config.verbosity)

    path_output_codebook = Path(
        f"{config.output_directory}/codebook_{config.output_name}.csv"
    )
    codebook = CodeBook(config, path_output_codebook)

    # check if there is already a codebook in the output directory
    if os.path.exists(path_output_codebook) and not full_rerun:
        logger.warning(
            f"Found already existing codebook file in {path_output_codebook}. Using it instead of {path_codebook}"
        )
        codebook.readin_niceplots_codebook_file(path_output_codebook)
    else:
        codebook.readin_codebook_file(path_codebook)

    codebook.summarize()
    if write_codebook:
        codebook.write_output_codebook()
    logger.info("Finished setting up nice-plots codebook.")

    # get new values from codebook to add to config
    config.codebook_file = codebook.path_codebook
    return codebook
