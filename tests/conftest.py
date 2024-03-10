import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture()
def get_test_inputs(request):
    name = request.param[0]
    example_dir = os.path.dirname(__file__) + "/../examples/"
    config_path = Path(example_dir + "example_config.yml")
    codebook_path = Path(example_dir + "example_codebook.csv")
    data_path = Path(example_dir + "example_data.csv")
    prefix = Path(example_dir)
    output_dir = f"{prefix}/{name}"
    print(f"Using test directory {output_dir}")
    yield (name, prefix, config_path, codebook_path, data_path)
    shutil.rmtree(output_dir)


@pytest.fixture()
def get_test_inputs_main(request):
    name = request.param[0]
    plot_type = [request.param[1]]
    example_dir = os.path.dirname(__file__) + "/../examples/"
    config_path = Path(example_dir + "example_config.yml")
    codebook_path = Path(example_dir + "example_codebook.csv")
    data_path = Path(example_dir + "example_data.csv")
    prefix = Path(example_dir)
    output_dir = f"{prefix}/{name}"
    print(f"Using test directory {output_dir}")
    yield (name, prefix, config_path, codebook_path, data_path, plot_type)
    shutil.rmtree(output_dir)
