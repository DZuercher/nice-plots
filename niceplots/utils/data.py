import os
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from pandas.api.types import is_numeric_dtype

from niceplots.utils.codebook import CodeBook
from niceplots.utils.config import Configuration
from niceplots.utils.nice_logger import init_logger, set_logger_level

logger = init_logger(__file__)


class Data:
    def __init__(
        self,
        df: pd.DataFrame,
        name: str,
        groups: dict,
        variables: pd.Series,
        no_answer_code: int,
        from_source: bool = False,
    ) -> None:
        self.name = name
        self.groups = groups
        self.variables = variables
        self.no_answer_code = no_answer_code
        self.data = df.to_frame() if isinstance(df, pd.Series) else df

        if from_source:
            self.preprocess()

    def preprocess(self):
        # check that all variables that are in the codebook are also in the data
        if not set(self.variables).issubset(set(self.data.columns)):
            missing_vars = set(self.variables) - set(self.data.columns)
            raise ValueError(
                f"Data Object {self.name}: Did not find {missing_vars} in data, but they are in the codebook."
            )
        # add category column
        if "nice_plots_group" in self.data.columns:
            raise ValueError(
                "Your data must not contain a column named: nice_plots_group"
            )

        self.data["nice_plots_group"] = None
        for group_name, group_string in self.groups.items():
            try:
                if isinstance(group_string, bool):
                    if group_string:
                        index_grouped = self.data.index
                    else:
                        index_grouped = pd.Index()
                else:
                    index_grouped = self.data.query(group_string).index
            except BaseException as error:
                raise ValueError(
                    f"Unable to apply your group filter {group_string} named {group_name} to data {self.name}"
                ) from error
            self.data.loc[index_grouped, "nice_plots_group"] = group_name

    def check(self, codebook: CodeBook):
        # check that values in each variable agree with the mapping in the codebook
        for _, row in codebook.codebook.iterrows():
            # TODO: at the moment restrict to numerical values
            if not is_numeric_dtype(self.data[row.variable]):
                raise ValueError(
                    f"Data Object {self.name}: Data is not numeric for variable {row.variable}. Nice-plots requires numberic data!"
                )
            if row.value_map is None:
                # require numerical values
                if not is_numeric_dtype(self.data[row.variable]):
                    raise ValueError(
                        f"Data Object {self.name}: No code mapping provided for variable {row.variable} but the data is not numeric!"
                    )
            else:
                mapping = eval(row.value_map)
                data_test = self.data[row.variable]
                data_test = data_test[
                    ~(
                        data_test.isna()
                        | (data_test == self.no_answer_code)
                        | (data_test == row.missing_label)
                    )
                ]
                if data_test.map(mapping).isna().sum() > 0:
                    raise ValueError(
                        f"Data Object {self.name}: Could not apply code mapping {mapping} to data for variable {row.variable}. Is your data out of range?"
                    )

    def summarize(self):
        logger.info(
            f"Data Object {self.name}: Data has {self.data.shape[0]} rows. They break down in the following categories:"
        )
        for group_name in self.groups.keys():
            filter_condition = f'nice_plots_group == "{group_name}"'
            logger.info(
                f"\t Group {group_name}: {self.data.query(filter_condition).nice_plots_group.count()} rows"
            )
        if self.data.nice_plots_group.isna().any():
            logger.warning(
                f"{self.data.nice_plots_group.isna().sum()} rows are not associated to any group -> Not used in plots."
            )


class DataCollection:
    def __init__(
        self, config: Configuration, codebook: CodeBook, path_output_data: Path
    ) -> None:
        self.delimiter = config.data.delimiter
        self.groups = config.data.groups
        self.no_answer_code = config.data.no_answer_code
        self.path_data = path_output_data
        self.variables = codebook.codebook.variable
        self.data_object_names: List = []

    def write_output_data(self) -> None:
        with pd.ExcelWriter(self.path_data) as writer:
            for name in self.data_object_names:
                getattr(self, name).data.to_excel(writer, sheet_name=name, index=False)

    def readin_data_files(
        self, data_paths: Tuple[Path, ...], data_labels: Tuple[str, ...]
    ) -> None:
        for path, label in zip(data_paths, data_labels):
            self.readin_data_file(path, label)

    def readin_data_file(self, path: Path, label: str) -> None:
        df = pd.read_csv(path, sep=self.delimiter)
        self._add_data_object(df, label, from_source=True)

    def readin_niceplots_data_file(self, path: Path) -> None:
        sheets = pd.read_excel(path, sheet_name=None)
        for label, df in sheets.items():
            self._add_data_object(df, label)

    def _add_data_object(
        self, df: pd.DataFrame, name: str, from_source: bool = False
    ) -> None:
        setattr(
            self,
            name,
            Data(
                df, name, self.groups, self.variables, self.no_answer_code, from_source
            ),
        )
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
    data_collection = DataCollection(config, codebook, path_output_data)

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
