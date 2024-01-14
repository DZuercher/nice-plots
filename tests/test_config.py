import os
import shutil
from pathlib import Path

from niceplots.utils.config import setup_config

example_dir = os.path.dirname(__file__) + "/../examples/"
config_path = Path(example_dir + "example_config.yml")
output_dir = example_dir + "/test_config"
name = "test"


def test_config():
    config = setup_config(config_path, name, "4", "svg", False)
    # non default format
    assert config.plotting.format == "svg"
    assert tuple(config.data.filters.keys()) == ("Group 1", "Others")

    # cleanup
    shutil.rmtree(f"{os.getcwd()}/test")
