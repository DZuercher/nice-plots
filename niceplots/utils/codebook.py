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

        self.codebook = pd.DataFrame(
            columns=["variable", "label", "value_map", "block", "color_scheme"],
            # TODO dtypes
            # dtype=[]
        )
        self.path_codebook = Path(path_output_codebook)
        self.name_label = config.data.name_label
        self.question_label = config.data.question_label
        self.block_id_label = config.data.block_id_label
        self.mapping_label = config.data.mapping_label

    def readin_codebook_file(self, codebook_path: Path) -> None:
        df = pd.read_csv(
            codebook_path,
            sep=self.delimiter,
        )

        self.path_codebook = Path(codebook_path)

        # TODO potentially process codebook further

        self.codebook["variable"] = df[self.name_label]
        self.codebook["label"] = df[self.question_label]
        # Todo process
        self.codebook["value_map"] = df[self.mapping_label]
        self.codebook["block"] = df[self.block_id_label]

        # TODO check
        self.check()

    def write_output_codebook(self):
        self.codebook.to_csv(self.path_codebook, index=False)

    def check(self):
        pass


def setup_codebook(
    config: Configuration, path_codebook: Path, write_codebook: bool = False
) -> CodeBook:
    set_logger_level(logger, config.verbosity)

    # check if there is already a codebook in the output directory
    path_output_codebook = Path(
        f"{config.output_directory}/codebook_{config.output_name}.csv"
    )
    if os.path.exists(path_output_codebook):
        logger.warning(
            f"Found already existing codebook file in {path_output_codebook}. Using it instead of {path_codebook}"
        )
        path_codebook = path_output_codebook

    codebook = CodeBook(config, path_output_codebook)
    codebook.readin_codebook_file(path_codebook)

    if write_codebook:
        codebook.write_output_codebook()
    logger.info("Finished setting up nice-plots codebook.")

    # get new values from codebook to add to config
    config.codebook_file = codebook.path_codebook
    return codebook
