import shutil
import pytest
from niceplots.utils.test_utils import get_test_inputs

from niceplots.utils.config import setup_config


@pytest.mark.parametrize('get_test_inputs', [['test_config']], indirect=["get_test_inputs"])
def test_config(get_test_inputs):
    name = get_test_inputs[0]
    prefix = get_test_inputs[1]
    config_path = get_test_inputs[2]

    config = setup_config(prefix, config_path, name, "4", "svg", False)
    # non default format
    assert config.plotting.format == "svg"
    assert tuple(config.data.groups.keys()) == ("Group 1", "Others")
