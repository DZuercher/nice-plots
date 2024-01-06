import pytest
from typing import Tuple
from niceplots.main import main
import os
from pathlib import Path
import shutil

example_dir = os.path.dirname(__file__) + '/../examples/'
config_path = Path(example_dir + 'example_config.yml')
codebook_path = Path(example_dir + 'example_codebook.csv')
data_path = Path(example_dir + 'example_data.csv')
@pytest.mark.parametrize(
    "output_name, plot_type",
    [
        (
                ("test_barplots", "barplots")
        ),
    ],
)
def test_main(output_name: str, plot_type: str) -> None:
    input_args = ((data_path), codebook_path, config_path, output_name, plot_type, "pdf", False, "4", (""))
    main(*input_args)
    output_directory = os.getcwd() + f"/{output_name}"
    # cleanup
    shutil.rmtree(output_directory)