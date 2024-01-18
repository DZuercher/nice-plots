import os
import shutil
from pathlib import Path

import pytest

from niceplots.main import main

example_dir = os.path.dirname(__file__) + "/../examples/"
config_path = Path(example_dir + "example_config.yml")
prefix = Path(example_dir)
codebook_path = Path(example_dir + "example_codebook.csv")
data_paths = (Path(example_dir + "example_data.csv"),)


@pytest.mark.parametrize(
    "output_name, plot_type",
    [
        (("test_main_barplots", "barplots")),
    ],
)
def test_main(output_name: str, plot_type: str) -> None:
    input_args = (
        data_paths,
        codebook_path,
        config_path,
        output_name,
        plot_type,
        "pdf",
        False,
        "4",
        ("",),
        prefix,
        False,
    )
    main(*input_args)

    # cleanup
    shutil.rmtree(f"{prefix}/{output_name}")
