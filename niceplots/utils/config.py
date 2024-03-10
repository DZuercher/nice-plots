import os
from pathlib import Path
from typing import Dict

import yaml
from matplotlib.font_manager import FontProperties

from niceplots.utils.nice_logger import init_logger, set_logger_level

logger = init_logger(__file__)


class ConfigBase:
    def update(self, config_dict: Dict) -> None:
        for key, value in config_dict.items():
            setattr(self, key, value)

    def check(self) -> None:
        pass

    def print(self, obj_name: str) -> None:
        logger.debug(f"{obj_name} :")
        for key, value in self.__dict__.items():
            logger.debug(f"\t {key} : {value}")


class DataConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.block_id_label = "Group"
        self.question_label = "Label"
        self.name_label = "Variable"
        self.mapping_label = "Value Codes"
        self.missing_label = "Missing Code"
        self.no_answer_code = 999
        self.groups: dict = {}
        self.delimiter = ","

    def update(self, config_dict: Dict) -> None:
        for key, value in config_dict.items():
            if key == "groups":
                if "nice_plots_default_group" in value.keys():
                    raise ValueError(
                        "Your groups must not contain a group named: nice_plots_default_group"
                    )
                if len(value.keys()) == 0:
                    value = {"nice_plots_default_group": "True"}
            setattr(self, key, value)


class PlottingConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.format = "pdf"
        self.nbins = 5
        self.unit = ""


class BarplotsConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.color_scheme = "RdYlGn"
        self.text_color = "black"
        self.invert = False
        self.layout = {
            "width_question": 2,
            "width_groups": 1,
            "width_plot": 3,
            "width_summary": 3,
            "width_pad": 0.2,
            "height_question": 1.5,
            "height_rel_pad_groups": 0.1,
            "height_rel_pad_questions": 0.3,
        }
        self.font_legend = {
            "family": "sans-serif",
            "style": "normal",
            "size": 8,  # in points
        }
        self.font_questions = {
            "family": "sans-serif",
            "style": "normal",
            "size": 12,  # in points
        }
        self.font_groups = {
            "family": "sans-serif",
            "style": "normal",
            "size": 12,  # in points
        }
        self.font_summary = {
            "family": "sans-serif",
            "style": "normal",
            "size": 8,  # in points
        }
        self.font_plot = {
            "family": "sans-serif",
            "style": "normal",
            "size": 12,  # in points
        }

    def make_fonts(self) -> None:
        self.font_legend = FontProperties(**self.font_legend)
        self.font_questions = FontProperties(**self.font_questions)
        self.font_groups = FontProperties(**self.font_groups)
        self.font_summary = FontProperties(**self.font_summary)
        self.font_plot = FontProperties(**self.font_plot)


class LineplotsConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.colors = ["C0", "C1", "C2", "C3", "C4"]
        self.invert = False
        self.layout = {
            "width_question": 2,
            "width_plot": 3.0,
            "width_pad": 0.2,
            "width_labels": 1.0,
            "height_question": 1.0,
            "rel_edge_line_height": 0.5,
        }
        self.font_legend = {
            "family": "sans-serif",
            "style": "normal",
            "size": 12,  # in points
        }
        self.font_questions = {
            "family": "sans-serif",
            "style": "normal",
            "size": 12,  # in points
        }
        self.font_labels = {
            "family": "sans-serif",
            "style": "normal",
            "size": 12,  # in points
        }


class HistogramsConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.colors = ["C0", "C1", "C2", "C3", "C4"]
        self.layout = {
            "width_labels": 1.5,
            "width_plot": 4,
            "width_pad": 0.2,
            "height_bar": 0.4,
            "height_rel_pad_questions": 0.4,
            "bar_label_pad": 0.02,
            "width_summary": 0.5,
            "pad_summary_right": 0.1,
            "pad_summary_top": 0.1,
        }
        self.font_legend = {
            "family": "sans-serif",
            "style": "normal",
            "size": 12,  # in points
        }
        self.font_labels = {
            "family": "sans-serif",
            "style": "normal",
            "size": 12,  # in points
        }
        self.font_summary = {
            "family": "sans-serif",
            "style": "normal",
            "size": 8,  # in points
        }
        self.font_bar_labels = {
            "family": "sans-serif",
            "style": "normal",
            "size": 10,  # in points
        }


class TimelinesConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.dist = 0.6
        self.height = 3.0
        self.colors = ["blue", "red"]


class Configuration:
    def __init__(
        self,
        config_path: Path | None = None,
        verbosity: str = "3",
        output_name: str = "output1",
        path_output_config: Path | None = None,
        output_directory: Path | None = None,
        output_format: str = "pdf",
        cache_directory: Path = Path("~/.cache/nice-plots"),
    ) -> None:
        logger.info("Initializing nice-plots configuration.")

        # defaults
        self.data = DataConfiguration()
        self.plotting = PlottingConfiguration()
        self.barplots = BarplotsConfiguration()
        self.lineplots = LineplotsConfiguration()
        self.histograms = HistogramsConfiguration()
        self.timelines = TimelinesConfiguration()

        # add some extra variables
        self.output_name = output_name
        self.config_file = path_output_config
        self.output_directory = output_directory
        self.verbosity = verbosity
        self.cache_directory = cache_directory
        self.codebook_file = Path("")
        self.data_file = Path("")

        if config_path is not None:
            # initialize using config file

            with open(config_path) as f:
                config_dict = yaml.load(f, yaml.FullLoader)

            # override
            self.data.update(config_dict["data"])

            config_dict["plotting"]["format"] = output_format
            self.plotting.update(config_dict["plotting"])

            self.barplots.update(config_dict["barplots"])
            self.lineplots.update(config_dict["lineplots"])
            self.histograms.update(config_dict["histograms"])
            self.timelines.update(config_dict["timelines"])

            logger.info(
                f"Initializing configuration instance using configuration file in {config_path}"
            )
        else:
            logger.debug("Initializing configuration instance using default values")

        self.sub_attrs = [
            "data",
            "plotting",
            "barplots",
            "lineplots",
            "histograms",
            "timelines",
        ]
        self.main_attrs = [
            "output_name",
            "config_file",
            "output_directory",
            "verbosity",
            "cache_directory",
        ]

        self.check_config()

        self.print_config()

    def make_fonts(self) -> None:
        self.barplots.make_fonts()

    def write_output_config(self) -> None:
        config_dict = {}
        config_dict["data"] = vars(self.data)
        config_dict["plotting"] = vars(self.plotting)
        config_dict["barplots"] = vars(self.barplots)
        config_dict["lineplots"] = vars(self.lineplots)
        config_dict["histograms"] = vars(self.histograms)
        config_dict["timelines"] = vars(self.timelines)

        if self.config_file is not None:
            with open(self.config_file, "w+") as f:
                yaml.dump(config_dict, f)
            logger.info(f"Wrote configuration to file {self.config_file}")

    def print_config(self) -> None:
        logger.debug("+" * 50 + " CONFIG " + "+" * 50)

        for attr in self.main_attrs:
            logger.debug(f"{attr} : {getattr(self, attr)}")
        for attr in self.sub_attrs:
            getattr(self, attr).print(attr)
        logger.debug("+" * 108)

    def check_config(self) -> None:
        for attr in self.sub_attrs:
            getattr(self, attr).check()


def get_cache(clear_cache: bool) -> Path:
    cache_directory = Path(os.path.expanduser("~/.cache/nice-plots"))
    if (os.path.exists(cache_directory)) & clear_cache:
        logger.warning("Resetting cache")
        os.rmdir(cache_directory)
    cache_directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using cache in: {cache_directory}")
    return cache_directory


def get_output_dir(name: str, prefix: Path) -> Path:
    output_directory = Path(f"{prefix}/{name}")
    output_directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using output directory: {output_directory}")
    return output_directory


def setup_config(
    prefix: Path,
    config_path: Path,
    name: str,
    verbosity: str,
    output_format: str,
    clear_cache: bool,
    write_config: bool = False,
    full_rerun: bool = True,
) -> Configuration:
    set_logger_level(logger, verbosity)

    path_cache = get_cache(clear_cache)
    path_output_dir = get_output_dir(name, prefix)

    path_output_config = Path(f"{path_output_dir}/config_{name}.yml")
    if os.path.exists(path_output_config) and not full_rerun:
        logger.warning(
            f"Found already existing configuration file in {path_output_config}. Using it instead of {config_path}"
        )
        config_path = path_output_config
    config = Configuration(
        config_path,
        verbosity,
        name,
        path_output_config,
        path_output_dir,
        output_format,
        path_cache,
    )
    if write_config:
        config.write_output_config()

    config.make_fonts()
    logger.info("Finished setting up nice-plots configuration.")
    return config
