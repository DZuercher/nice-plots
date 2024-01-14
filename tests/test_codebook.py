import os
import shutil
from pathlib import Path

from niceplots.utils.codebook import setup_codebook
from niceplots.utils.config import setup_config

example_dir = os.path.dirname(__file__) + "/../examples/"
config_path = Path(example_dir + "example_config.yml")
codebook_path = Path(example_dir + "example_codebook.csv")
prefix = Path(example_dir)
name = "test_codebook"


def test_codebook():
    config = setup_config(prefix, config_path, name, "4", "svg", False)
    codebook = setup_codebook(config, codebook_path)

    assert config.codebook_file == codebook.path_codebook

    # cleanup
    shutil.rmtree(f"{prefix}/{name}")
