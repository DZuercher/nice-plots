import os
import shutil
from pathlib import Path

from niceplots.utils.config import setup_config
from niceplots.utils.data import setup_data

example_dir = os.path.dirname(__file__) + "/../examples/"
config_path = Path(example_dir + "example_config.yml")
prefix = Path(example_dir)


def test_single_data():
    data_labels = ("data",)
    name = "test_single_data"
    data_paths = (Path(example_dir + "example_data.csv"),)

    config = setup_config(prefix, config_path, name, "4", "pdf", False)
    data = setup_data(config, data_paths, data_labels)

    assert config.data_file == data.path_data

    # cleanup
    shutil.rmtree(f"{prefix}/{name}")


def test_multi_data():
    data_labels = ("data1", "data2", "data3")
    name = "test_multi_data"
    data_paths = (
        Path(example_dir + "example_data.csv"),
        Path(example_dir + "example_data.csv"),
        Path(example_dir + "example_data.csv"),
    )

    config = setup_config(prefix, config_path, name, "4", "pdf", False)
    data = setup_data(config, data_paths, data_labels)

    assert config.data_file == data.path_data

    # cleanup
    shutil.rmtree(f"{prefix}/{name}")
