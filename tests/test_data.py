import pytest

from niceplots.utils.codebook import setup_codebook
from niceplots.utils.config import setup_config
from niceplots.utils.data import setup_data


@pytest.mark.parametrize(
    "get_test_inputs", [["test_single_data"]], indirect=["get_test_inputs"]
)
def test_single_data(get_test_inputs):
    name = get_test_inputs[0]
    prefix = get_test_inputs[1]
    config_path = get_test_inputs[2]
    codebook_path = get_test_inputs[3]
    data_path = get_test_inputs[4]
    data_labels = ("data",)
    data_paths = (data_path,)

    config = setup_config(prefix, config_path, name, "4", "pdf", False)
    codebook = setup_codebook(config, codebook_path)
    data = setup_data(config, codebook, data_paths, data_labels)

    assert config.data_file == data.path_data


@pytest.mark.parametrize(
    "get_test_inputs", [["test_multi_data"]], indirect=["get_test_inputs"]
)
def test_multi_data(get_test_inputs):
    name = get_test_inputs[0]
    prefix = get_test_inputs[1]
    config_path = get_test_inputs[2]
    codebook_path = get_test_inputs[3]
    data_path = get_test_inputs[4]

    data_labels = ("data1", "data2", "data3")
    data_paths = (
        data_path,
        data_path,
        data_path,
    )

    config = setup_config(prefix, config_path, name, "4", "pdf", False)
    codebook = setup_codebook(config, codebook_path)
    data = setup_data(config, codebook, data_paths, data_labels)

    assert config.data_file == data.path_data
