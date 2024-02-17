import pytest
from niceplots.utils.codebook import setup_codebook
from niceplots.utils.config import setup_config
from niceplots.utils.test_utils import get_test_inputs

@pytest.mark.parametrize('get_test_inputs', [['test_codebook']], indirect=["get_test_inputs"])
def test_codebook(get_test_inputs):
    name = get_test_inputs[0]
    prefix = get_test_inputs[1]
    config_path = get_test_inputs[2]
    codebook_path = get_test_inputs[3]

    config = setup_config(prefix, config_path, name, "4", "pdf", False)
    codebook = setup_codebook(config, codebook_path)

    assert config.codebook_file == codebook.path_codebook
