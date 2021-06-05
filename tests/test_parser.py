from niceplots import parser
import os
import pathlib
import shutil

example_dir = os.path.dirname(__file__) + '/../examples/'
config_path = example_dir + 'example_config.yml'
codebook_path = example_dir + 'example_codebook.csv'
data_path = example_dir + 'example_data.csv'


def test_load_config():
    output_name = 'test_load_config'

    output_directory = os.path.dirname(__file__) + '/' + output_name
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)

    parser.load_config(config_path, output_directory, output_name)

    shutil.rmtree(output_directory)


def test_load_codebook():
    output_name = 'test_load_codebook'

    output_directory = os.path.dirname(__file__) + '/' + output_name
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)

    ctx = parser.load_config(config_path, output_directory, output_name)
    parser.load_codebook(ctx, codebook_path)

    shutil.rmtree(output_directory)


def test_load_data():
    output_name = 'test_load_data'

    output_directory = os.path.dirname(__file__) + '/' + output_name
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)

    ctx = parser.load_config(config_path, output_directory, output_name)
    codebook = parser.load_codebook(ctx, codebook_path)
    data = parser.load_data(ctx, data_path, codebook)

    parser.check_config(ctx, codebook, data)

    shutil.rmtree(output_directory)
