from niceplots.utils.config import Configuration
from pathlib import Path
import os

example_dir = os.path.dirname(__file__) + '/../examples/'
config_path = Path(example_dir + 'example_config.yml')
output_dir = example_dir + "/test_config"
name = "test"
def test_config():
    path_output_config = f"{output_dir}/config_{name}.yml"
    config = Configuration(config_path, "4", name, path_output_config, output_dir, "svg")
    # non default format
    assert config.plotting.format == "svg"
    assert tuple(config.data.filters.keys()) == ("Group 1", "Others")