from niceplots.utils.nice_logger import init_logger, set_logger_level
import yaml
from pathlib import Path
from typing import Dict
logger = init_logger(__file__)

class ConfigBase():
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
        self.filters = {}
        self.delimiter = ","

class PlottingConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.plot_width = 8
        self.format = "pdf"
        self.fontsize = 15
        self.fontsize_stats = 12
        self.nbins = 5
        self.unit = ''

class BarplotsConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.invert = False
        self.color_scheme = 'RdYlGn'
        self.height = 0.7
        self.dist = 0.3
        self.major_dist = 1
        self.bar_text_color = 'black'
        self.padding = 0.3

class LineplotsConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.invert = False
        self.colors = ['C0', 'C1', 'C2', 'C3', 'C4']
        self.height = 0.7
        self.dist = 0.3
        self.padding = 3.0
        self.label_padding = 0.2

class HistogramsConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.colors = ['C0', 'C1', 'C2', 'C3', 'C4']
        self.padding = 0.2
        self.bar_pad = 0.1
        self.rwidth = 0.8
        self.dist = 0.5

class TimelinesConfiguration(ConfigBase):
    def __init__(self) -> None:
        self.dist = 0.6
        self.height = 3.0
        self.colors = ['blue', 'red']

class Configuration():
    def __init__(self, config_path: Path | None = None,
                 verbosity: str = "3",
                 output_name: str = "output1",
                 path_output_config: str | None = None,
                 output_directory: str | None = None,
                 output_format: str = "pdf") -> None:
        set_logger_level(logger, verbosity)

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

        if config_path is not None:
            # initialize using config file

            with open(config_path, "r") as f:
                config_dict = yaml.load(f, yaml.FullLoader)

            # override
            self.data.update(config_dict["data"])

            config_dict["plotting"]["format"] = output_format
            self.plotting.update(config_dict["plotting"])

            self.barplots.update(config_dict["barplots"])
            self.lineplots.update(config_dict["lineplots"])
            self.histograms.update(config_dict["histograms"])
            self.timelines.update(config_dict["timelines"])

            logger.debug(f"Initializing config instance using configuration file in {config_path}")
        else:
            logger.debug(f"Initializing config instance using default values")

        self.sub_attrs = ["data", "plotting", "barplots", "lineplots", "histograms", "timelines"]
        self.main_attrs = ["output_name", "config_file", "output_directory", "verbosity"]

        self.check_config()

        self.print_config()

    def write_output_config(self) -> None:

        config_dict = {}
        config_dict["data"] = vars(self.data)
        config_dict["plotting"] = vars(self.plotting)
        config_dict["barplots"] = vars(self.barplots)
        config_dict["lineplots"] = vars(self.lineplots)
        config_dict["histograms"] = vars(self.histograms)
        config_dict["timelines"] = vars(self.timelines)

        with open(self.config_file, "w+") as f:
            yaml.dump(config_dict, f)
        logger.debug(f"Wrote configuration to file {self.config_file}")

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