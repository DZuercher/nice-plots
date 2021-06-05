from niceplots import parser
from niceplots import process
import os
import pathlib
import shutil

example_dir = os.path.dirname(__file__) + '/../examples/'
config_path = example_dir + 'example_config.yml'
codebook_path = example_dir + 'example_codebook.csv'
data_path = example_dir + 'example_data.csv'


def test_process_data():
    output_name = 'test_process_data'

    output_directory = os.path.dirname(__file__) + '/' + output_name
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)

    ctx = parser.load_config(config_path, output_directory, output_name)
    codebook = parser.load_codebook(ctx, codebook_path)
    data = parser.load_data(ctx, data_path, codebook)

    process.process_data(data, codebook, ctx)

    shutil.rmtree(output_directory)
