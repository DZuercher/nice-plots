# Authors: Dominik Zuercher, Valeria Glauser

try:
    import tkinter
except ImportError:
    raise Exception("Could not import tkinter. This means tk is not configured properly. On Linux this can be solved by installing tk.")
import os
from tqdm import tqdm
import pathlib
import copy
from niceplots import utils
from niceplots import parser
from niceplots import process
from niceplots import barplot
from niceplots import lineplot
from niceplots import histogram

import logging
LOGGER = logging.getLogger(__name__)

class niceplots_handles:
    """ Holds nice plots objects """

    def __init__(self):
        ###########################
        # static nice plots objects
        ###########################
        self.ctx = None
        self.data = None
        self.codebook = None
        self.global_plotting_data = None

        ###########################
        # mutable objects
        ###########################
        self.default_config_path = tkinter.StringVar()
        self.default_codebook_path = tkinter.StringVar()
        self.output_dir = tkinter.StringVar()
        self.data_path = tkinter.StringVar()
        self.plot_type = tkinter.StringVar()
        self.config_variables = {}
        self.codebook_variables = {}
        self.plot_type.set('bars')

        # set defaults
        self.default_config_path.set(
            f'{os.path.dirname(__file__)}/../examples/example_config.yml')
        self.default_codebook_path.set(
            f'{os.path.dirname(__file__)}/../examples/example_codebook.csv')
        self.output_dir.set(f'{os.path.dirname(__file__)}/../examples/test')
        self.data_path.set(
            f'{os.path.dirname(__file__)}/../examples/example_data.csv')

    def create_directories(self):
        """ Create directories needed by nice plots """
        # create cache directory
        cache_directory = os.path.expanduser("~/.cache/nice-plots")
        pathlib.Path(cache_directory).mkdir(parents=True, exist_ok=True)

        # create output directory
        pathlib.Path(self.output_dir.get()).mkdir(parents=True, exist_ok=True)

    def update_code(self, status_label):
        """Update codebook"""
        status_label.config(text="Saving...")
        LOGGER.info("Updating codebook")

        # update codebook
        for col in self.codebook_variables:
            for idy in range(len(self.codebook_variables[col])):
                self.codebook[col][idy] = self.codebook_variables[col][idy].get()

        # write to file
        self.codebook.to_csv(self.ctx['codebook_path'], index=False)

        self.save(status_label)
        status_label.config(text="")

    def restore_code(self, status_label):
        status_label.config(text="Restoring defaults")
        LOGGER.info("Restoring codebook file")

        # remove config file
        os.remove(self.ctx['codebook_path'])

        # re-initialize
        code_out = parser.load_codebook(
            self.ctx, self.default_codebook_path.get())
        if isinstance(code_out, str):
            status_label.config(text=code_out)
            return
        else:
            self.codebook = code_out

        # reset string variables
        n_entries = self.codebook.shape[0]
        for idx, col in enumerate(self.codebook):
            if col == 'Index':
                continue
            # assign in loop otherswise copies variable address
            for idy in range(n_entries):
                self.codebook_variables[col][idy].set(self.codebook[col][idy])
        self.save(status_label)
        status_label.config(text="")

    def update_config(self, status_label):
        """Update config"""
        status_label.config(text="Saving...")
        LOGGER.info("Updating codebook")

        # update ctx
        for key in self.config_variables.keys():
            self.ctx[key] = self.config_variables[key].get()

        # update config file
        with open(self.ctx['config_file'], 'r') as f:
            config_file = f.readlines()
        for ii in range(len(config_file)):
            for key in self.ctx.keys():
                if config_file[ii].startswith(key):
                    if '#' in config_file[ii]:
                        suffix = '#' + config_file[ii].split('#')[-1]
                    else:
                        suffix = ''
                    if (parser.isnumber(self.ctx[key])) | (self.ctx[key].startswith('{')) | (self.ctx[key].startswith('[')) | (self.ctx[key].startswith('(')):
                        config_file[ii] = f'{key} : {self.ctx[key]} {suffix} \n'
                    else:
                        config_file[ii] = f'{key} : \'{self.ctx[key]}\' {suffix} \n'
        with open(self.ctx['config_file'], 'w') as f:
            f.writelines(config_file)

        self.save(status_label)
        status_label.config(text="")

    def restore_config(self, status_label):
        status_label.config(text="Restoring defaults")
        LOGGER.info("Restoring config file")

        # remove config file
        os.remove(self.ctx['config_file'])

        # re-initialize
        ctx_out = parser.load_config(self.default_config_path.get(),
                                      self.output_dir.get(),
                                      os.path.basename(self.output_dir.get()))
        if isinstance(ctx_out, str):
            status_label.config(text=ctx_out)
            return
        else:
            self.ctx = ctx_out

        # reset string variables
        for key in self.config_variables.keys():
            self.config_variables[key].set(self.ctx[key])

        self.save(status_label)
        status_label.config(text="")

    def save(self, status_label):
        """ Resets static objects using current values of mutables """
        status_label.config(text="Saving...")

        self.create_directories()

        LOGGER.info(
            f"Set default configuration file path -> {self.default_config_path.get()}")
        LOGGER.info(
            f"Set default codebook file path -> {self.default_codebook_path.get()}")
        LOGGER.info(f"Set output directory path -> {self.output_dir.get()}")
        LOGGER.info(f"Set data file path -> {self.data_path.get()}")

        # parsing
        ctx_out = parser.load_config(self.default_config_path.get(),
                                      self.output_dir.get(),
                                      os.path.basename(self.output_dir.get()))
        if isinstance(ctx_out, str):
            status_label.config(text=ctx_out)
            return
        else:
            self.ctx = ctx_out

        LOGGER.info("Loading codebook...")
        code_out = parser.load_codebook(
            self.ctx, self.default_codebook_path.get())
        if isinstance(code_out, str):
            status_label.config(text=code_out)
            return
        else:
            self.codebook = code_out

        LOGGER.info("Loading data...")
        data = parser.load_data(
            self.ctx, self.data_path.get(), self.codebook)
        if isinstance(data, str):
            status_label.config(text=data)
            return
        else:
            self.data = data

        status = parser.check_config(self.ctx, self.codebook, self.data)
        if len(status) > 0:
            status_label.config(text=status)
            return

        LOGGER.info("Processing input data...")
        data_out = process.process_data(
            self.data, self.codebook, self.ctx)
        if isinstance(data_out, str):
            status_label.config(text=data_out)
            return
        else:
            self.global_plotting_data = data_out

        status_label.config(text="")

    def run(self, status_label):
        """ Produces the plots """
        status_label.config(text="Running...")
        LOGGER.info("Producing your plots please wait...")
        if self.plot_type.get() == 'bars':
            exec_func = getattr(barplot, 'plot_barplots')
        elif self.plot_type.get() == 'lines':
            exec_func = getattr(lineplot, 'plot_lineplots')
        elif self.plot_type.get() == 'histograms':
            exec_func = getattr(histogram, 'plot_histograms')
        else:
            raise Exception(
                f"Plot type {self.plot_type.get()} does not exist.")

        if self.global_plotting_data is None:
            status_label.config(
                text="You need to hit save at least once before running!")
            return

        # loop over question blocks and produce one plot for each
        # question block
        for xx, plotting_data in tqdm(enumerate(self.global_plotting_data)):
            exec_func(xx, self.global_plotting_data, self.ctx)
        LOGGER.info("nice-plots finished without errors :)")
        status_label.config(text="")

    def run_single(self, status_label, index):
        """ Produces a single plot"""
        status_label.config(text="Running...")
        LOGGER.info("Producing your plots please wait...")
        if self.plot_type.get() == 'bars':
            exec_func = getattr(barplot, 'plot_barplots')
        elif self.plot_type.get() == 'lines':
            exec_func = getattr(lineplot, 'plot_lineplots')
        elif self.plot_type.get() == 'histograms':
            exec_func = getattr(histogram, 'plot_histograms')
        else:
            raise Exception(
                f"Plot type {self.plot_type.get()} does not exist.")

        if self.global_plotting_data is None:
            status_label.config(
                text="You need to hit save at least once before running!")
            return

        exec_func(index, self.global_plotting_data, self.ctx)
        LOGGER.info("nice-plots finished without errors :)")
        status_label.config(text="")