from niceplots import parser
from niceplots import process
from niceplots import barplot
import os
import pathlib
import shutil

example_dir = os.path.dirname(__file__) + '/../examples/'
config_path = example_dir + 'example_config.yml'
codebook_path = example_dir + 'example_codebook.csv'
data_path = example_dir + 'example_data.csv'


def test_barplots():
    exec_func = getattr(barplot, 'plot_barplots')

    output_name = 'barplots'

    # create cache directory
    cache_directory = os.path.expanduser("~/.cache/nice-plots")
    pathlib.Path(cache_directory).mkdir(parents=True, exist_ok=True)

    output_directory = os.path.dirname(__file__) \
        + '/../examples/' + output_name
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)

    ctx = parser.load_config(config_path, output_directory, output_name)
    ctx['format'] = 'pdf'
    codebook = parser.load_codebook(ctx, codebook_path)
    data = parser.load_data(ctx, data_path, codebook)

    global_plotting_data = process.process_data(data, codebook, ctx)

    for xx, plotting_data in enumerate(global_plotting_data):
        exec_func(xx, global_plotting_data, ctx)

    # shutil.rmtree(output_directory)
