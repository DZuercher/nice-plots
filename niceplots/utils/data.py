import os
from pathlib import Path
from typing import List, Tuple

import pandas as pd

from niceplots.utils.codebook import CodeBook
from niceplots.utils.config import Configuration
from niceplots.utils.nice_logger import init_logger, set_logger_level

logger = init_logger(__file__)


class Data:
    def __init__(self, df: pd.DataFrame, name: str) -> None:
        self.name = name
        self.data = df

    def check(self, codebook: CodeBook):
        # check that all variables that are in the codebook are also in the data
        if not set(codebook.codebook.variable).issubset(set(self.data.columns)):
            missing_vars = set(codebook.codebook.variable) - set(self.data.columns)
            raise ValueError(
                f"Data Object {self.name}: Did not find {missing_vars} in data, but they are in the codebook."
            )

        # check that values in each variable agree with the mapping in the codebook
        for _, row in codebook.codebook.iterrows():
            if not row.value_map == "none":
                continue
            mapping = eval(row.value_map)
            if self.data[row.variable].map(mapping).isna().sum() > 0:
                raise ValueError(
                    f"Data Object {self.name}: Could not apply code mapping {mapping} to data for variable {row.variable}. Is your data out of range?"
                )

    def summarize(self):
        logger.info(f"Data Object {self.name}: Data has {self.data.shape[0]} rows.")


class DataCollection:
    def __init__(self, config: Configuration, path_output_data: Path) -> None:
        self.delimiter = config.data.delimiter
        self.path_data = path_output_data
        self.data_object_names: List = []

    def write_output_data(self) -> None:
        with pd.ExcelWriter(self.path_data) as writer:
            for name in self.data_object_names:
                getattr(self, name).to_excel(writer, sheet_name=name, index=False)

    def readin_data_files(
        self, data_paths: Tuple[Path, ...], data_labels: Tuple[str, ...]
    ) -> None:
        for path, label in zip(data_paths, data_labels):
            self.readin_data_file(path, label)

    def readin_data_file(self, path: Path, label: str) -> None:
        df = pd.read_csv(path, sep=self.delimiter)
        self._add_data_object(df, label)

    def readin_niceplots_data_file(self, path: Path) -> None:
        sheets = pd.read_excel(path)
        for label, df in sheets.items():
            self._add_data_object(df, label)

    def _add_data_object(self, df: pd.DataFrame, name: str) -> None:
        setattr(self, name, Data(df, name))
        self.data_object_names.append(name)

    def check(self, codebook: CodeBook):
        for name in self.data_object_names:
            getattr(self, name).check(codebook)

    def summarize(self):
        logger.info(
            f"Got a Data Collection holding {len(self.data_object_names)} data sets"
        )
        for name in self.data_object_names:
            getattr(self, name).summarize()


def setup_data(
    config: Configuration,
    codebook: CodeBook,
    data_paths: Tuple[Path, ...],
    data_labels: Tuple[str, ...],
    write_data: bool = False,
    full_rerun: bool = True,
) -> DataCollection:
    set_logger_level(logger, config.verbosity)

    logger.info("Initializing nice-plots data.")

    path_output_data = Path(f"{config.output_directory}/data_{config.output_name}.xlsx")
    data_collection = DataCollection(config, path_output_data)

    # check if there is already a data file in the output directory
    if os.path.exists(path_output_data) and not full_rerun:
        logger.warning(
            f"Found already existing data in {path_output_data}. Using it instead of {data_paths}"
        )
        data_collection.readin_niceplots_data_file(path_output_data)
    else:
        data_collection.readin_data_files(data_paths, data_labels)

    data_collection.check(codebook)
    data_collection.summarize()

    if write_data:
        data_collection.write_output_data()
    logger.info("Finished setting up nice-plots data.")

    # get new values from data collection to add to config
    config.data_file = data_collection.path_data
    return data_collection
