# Authors: Dominik Zuercher, Valeria Glauser

from niceplots import parser
from niceplots import process
from niceplots import barplot
from niceplots import lineplot
from niceplots import histogram
from niceplots import utils
import os
import numpy as np
import glob
from tqdm import tqdm
import pathlib
from threading import Thread
from tkPDFViewer import tkPDFViewer as pdf

try:
    import tkinter
except ImportError:
    raise Exception("Could not import tkinter. This means tk is not configured properly. On Linux this can be solved by installing tk.")
from tkinter import ttk
import tkinter.font as tkFont

global LOGGER
LOGGER = utils.init_logger(__file__)


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
        status_label.config(text="")

    def restore_code(self, status_label):
        status_label.config(text="Restoring defaults")
        LOGGER.info("Restoring codebook file")

        # remove config file
        os.remove(self.ctx['codebook_path'])

        # re-initialize
        self.codebook = parser.load_codebook(
            self.ctx, self.default_codebook_path.get())

        # reset string variables
        n_entries = self.codebook.shape[0]
        for idx, col in enumerate(self.codebook):
            if col == 'Index':
                continue
            # assign in loop otherswise copies variable address
            for idy in range(n_entries):
                self.codebook_variables[col][idy].set(self.codebook[col][idy])
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

        status_label.config(text="")

    def restore_config(self, status_label):
        status_label.config(text="Restoring defaults")
        LOGGER.info("Restoring config file")

        # remove config file
        os.remove(self.ctx['config_file'])

        # re-initialize
        self.ctx = parser.load_config(self.default_config_path.get(),
                                      self.output_dir.get(),
                                      os.path.basename(self.output_dir.get()))

        # reset string variables
        for key in self.config_variables.keys():
            self.config_variables[key].set(self.ctx[key])

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
        self.ctx = parser.load_config(self.default_config_path.get(),
                                      self.output_dir.get(),
                                      os.path.basename(self.output_dir.get()))

        LOGGER.info("Loading codebook...")
        self.codebook = parser.load_codebook(
            self.ctx, self.default_codebook_path.get())

        LOGGER.info("Loading data...")
        self.data = parser.load_data(
            self.ctx, self.data_path.get(), self.codebook)

        parser.check_config(self.ctx, self.codebook, self.data)
        LOGGER.info("Processing input data...")
        self.global_plotting_data = process.process_data(
            self.data, self.codebook, self.ctx)
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


class GUI:
    """ Handles GUI """

    def __init__(self):
        # set GUI scaling
        self.scaling = 2.0
        self.status_label = None

        # root window
        self.root = tkinter.Tk()
        self.root.title("nice-plots")

        # set global font
        self.default_font = tkFont.nametofont("TkDefaultFont")
        self.default_font.configure(size=int(10 * self.scaling))

        self.root.tk.call('tk', 'scaling', self.scaling)
        self.root.option_add("*Font", self.default_font)

    def config_gui(self, np_instance):

        self.np_instance = np_instance

        # Multi Tab
        self.tabControl = ttk.Notebook(self.root)
        self.tabControl.pack(expand=True)
        self.general_tab = ttk.Frame(
            self.tabControl)
        # padding=f"{3*self.scaling} {3*self.scaling} {12*self.scaling} {12*self.scaling}")
        self.config_tab = ttk.Frame(
            self.tabControl)
        # padding=f"{3*self.scaling} {3*self.scaling} {12*self.scaling} {12*self.scaling}")
        self.code_tab = ttk.Frame(
            self.tabControl)
        # padding=f"{3*self.scaling} {3*self.scaling} {12*self.scaling} {12*self.scaling}")
        self.preview_tab = ttk.Frame(
            self.tabControl)
        # padding=f"{3*self.scaling} {3*self.scaling} {12*self.scaling} {12*self.scaling}")

        self.general_tab.pack(fill='both', expand=True)
        self.config_tab.pack(fill='both', expand=True)
        self.code_tab.pack(fill='both', expand=True)
        self.preview_tab.pack(fill='both', expand=True)

        self.tabControl.add(self.general_tab, text='General')
        self.tabControl.add(self.config_tab, text='Config')
        self.tabControl.add(self.code_tab, text='Codebook')
        self.tabControl.add(self.preview_tab, text='Preview')

        # bind such that each time tab becomes visible function is called
        self.config_tab.bind("<Visibility>", self.config_config_tab)
        self.code_tab.bind("<Visibility>", self.config_code_tab)
        self.preview_tab.bind("<Visibility>", self.config_preview_tab)

        # configure the tabs
        self.config_general_tab()
        self.config_config_tab()
        self.config_code_tab()
        self.config_preview_tab()

    def config_preview_tab(self, event=None):
        if event is None:
            # assume initialization
            self.preview_label = ttk.Label(
                self.preview_tab,
                text="")
            self.preview_label.grid(
                column=0, row=0, sticky='W')
            self.preview_tab_initalized = False
        if not self.preview_tab_initalized:
            if self.np_instance.global_plotting_data is None:
                self.preview_label.config(
                    text="No plots to show yet. Press Save and Run in General tab first.")
            else:
                self.preview_label.config(text="Preview")
                self.preview_tab_initalized = True

                Lb = tkinter.Listbox(self.preview_tab)
                Lb.grid(row=1, column=0, sticky=('W', 'E', 'N', 'S'))

                plots = glob.glob(
                    self.np_instance.ctx['output_directory'] + '/*.' + self.np_instance.ctx['format'])
                plots = np.asarray(plots)
                self.plots = np.sort(plots)
                for idx, plot in enumerate(self.plots):
                    Lb.insert(idx, os.path.basename(plot))

                def callback(event=None):
                    print("CALL")
                    if event is not None:
                        selection = event.widget.curselection()
                        if selection:
                            self.viewer_index.set(selection[0])
                        else:
                            self.viewer_index.set(0)
                        old_v2 = self.preview_tab.grid_slaves(row=1, column=1)[0]
                        old_v2.grid_forget()

                        v1 = pdf.ShowPdf()
                        v1.img_object_li = []
                        v2 = v1.pdf_view(
                            self.preview_tab,
                            width=50,
                            height=30,
                            pdf_location=str(self.plots[int(self.viewer_index.get())]))
                        v2.grid(row=1, column=1, sticky=('W', 'E', 'N', 'S'))
                    else:
                        self.viewer_index = tkinter.StringVar()
                        self.viewer_index.set(0)
                        if self.np_instance.ctx['format'] == 'pdf':
                            v1 = pdf.ShowPdf()
                            v2 = v1.pdf_view(
                                self.preview_tab,
                                width=50,
                                height=30,
                                pdf_location=str(self.plots[int(self.viewer_index.get())]))
                            v2.grid(row=1, column=1, sticky=('W', 'E', 'N', 'S'))
                        else:
                            pass

                Lb.bind("<<ListboxSelect>>", callback)

                callback()

                # refresh button
                save_button = tkinter.Button(
                    self.preview_tab,
                    text="Refresh",
                    command=lambda: self.start_run('run_single', self.preview_status_label))
                save_button.grid(row=2, column=0)

                # run all button
                run_button = tkinter.Button(
                    self.preview_tab,
                    text="Rerun All",
                    command=lambda: self.start_run('run', self.preview_status_label))
                run_button.grid(row=3, column=0)

                self.preview_status_label = ttk.Label(
                    self.preview_tab, text="")
                self.preview_status_label.grid(column=0, row=4, sticky='W')
        # if selection changed redraw

    def config_code_tab(self, event=None):
        # Config Tab
        if event is None:
            # assume initialization
            self.code_label = ttk.Label(
                self.code_tab,
                text="")
            self.code_label.grid(
                column=0, row=0, sticky='W')
            self.code_tab_initalized = False
        if not self.code_tab_initalized:
            if self.np_instance.codebook is None:
                self.code_label.config(
                    text="Codebook not set yet. Press Save in General tab first.")
            else:
                self.code_label.config(text="Codebook")

                # add Scrollbars
                def onFrameConfigure(canvas, frame):
                    '''Reset the scroll region to encompass the inner frame'''
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    canvas.config(height=1500,
                                  width=frame.winfo_width() - 40)

                canvas = tkinter.Canvas(self.code_tab, borderwidth=0)
                frame = tkinter.Frame(canvas)
                vsb = tkinter.Scrollbar(
                    self.code_tab, orient="vertical", command=canvas.yview, width=40)
                hsb = tkinter.Scrollbar(
                    self.code_tab, orient="horizontal", command=canvas.xview, width=40)
                canvas.configure(yscrollcommand=vsb.set)
                canvas.configure(xscrollcommand=hsb.set)
                vsb.grid(row=1, column=1, sticky=('N', 'S', 'W', 'E'))
                hsb.grid(row=2, column=0, sticky=('W', 'E'))
                canvas.grid(row=1, column=0, sticky=('W', 'E', 'N', 'S'))
                canvas.create_window((4, 4), window=frame, anchor="nw")
                frame.bind("<Configure>", lambda event,
                           canvas=canvas: onFrameConfigure(canvas, self.code_tab))

                # display codebook
                n_entries = self.np_instance.codebook.shape[0]

                # variables
                for idx, col in enumerate(self.np_instance.codebook):
                    if col == 'Index':
                        continue
                    self.np_instance.codebook_variables[col] = []
                    # assign in loop otherswise copies variable address
                    for idy in range(n_entries):
                        self.np_instance.codebook_variables[col].append(
                            tkinter.StringVar())

                # header
                for idx, col in enumerate(self.np_instance.codebook):
                    ttk.Label(frame, text=col).grid(row=0, column=idx)

                # data
                for idx, col in enumerate(self.np_instance.codebook):
                    data = self.np_instance.codebook[col]
                    if col == 'Index':
                        for idy in range(n_entries):
                            ttk.Label(frame, text=data[idy]).grid(
                                row=idy + 1, column=idx)
                    else:
                        for idy in range(n_entries):
                            entry = ttk.Entry(
                                frame,
                                textvariable=self.np_instance.codebook_variables[col][idy])
                            entry.grid(row=idy + 1, column=idx,
                                       sticky=('W', 'E'))
                            self.np_instance.codebook_variables[col][idy].set(
                                data[idy])

                # save button
                save_button = tkinter.Button(
                    self.code_tab,
                    text="Save",
                    command=lambda: self.start_run('update_code', self.code_status_label))
                save_button.grid(row=3, column=0)

                # restore button
                restore_button = tkinter.Button(
                    self.code_tab,
                    text="Restore defaults",
                    command=lambda: self.start_run('restore_code', self.code_status_label))
                restore_button.grid(row=4, column=0)
                self.code_tab_initalized = True

                self.code_status_label = ttk.Label(self.code_tab, text="")
                self.code_status_label.grid(column=0, row=5, sticky='W')

    def config_config_tab(self, event=None):
        # Config Tab
        if event is None:
            # assume initialization
            self.config_label = ttk.Label(
                self.config_tab,
                text="")
            self.config_label.grid(
                column=0, row=0, sticky='W')
            self.config_tab_initalized = False
        if not self.config_tab_initalized:
            if self.np_instance.ctx is None:
                self.config_label.config(
                    text="Configuration file not set yet. Press Save in General tab first.")
            else:
                self.config_label.config(text="Options")

                # add Scrollbar
                def onFrameConfigure(canvas, frame):
                    '''Reset the scroll region to encompass the inner frame'''
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    canvas.config(width=frame.winfo_width())
                canvas = tkinter.Canvas(self.config_tab, borderwidth=0)
                frame = tkinter.Frame(canvas)
                vsb = tkinter.Scrollbar(
                    self.config_tab, orient="vertical", command=canvas.yview, width=40)
                canvas.configure(yscrollcommand=vsb.set)
                vsb.grid(row=1, column=1, sticky=('N', 'S', 'W', 'E'))
                canvas.grid(row=1, column=0, sticky=('W', 'E'))
                canvas.create_window((4, 4), window=frame, anchor="nw")
                frame.bind("<Configure>", lambda event,
                           canvas=canvas: onFrameConfigure(canvas, frame))

                # Display the options from the config file
                counter = 0
                # hide some options
                hide = ['output_name', 'config_file', 'output_directory',
                        'codebook_path', 'additional_codebook_entries']
                for key in self.np_instance.ctx.keys():
                    if key in hide:
                        continue
                    ttk.Label(frame, text=key).grid(
                        column=0, row=counter, sticky='W')

                    self.np_instance.config_variables[key] = tkinter.StringVar(
                    )
                    self.np_instance.config_variables[key].set(
                        self.np_instance.ctx[key])
                    ttk.Entry(
                        frame, width=40,
                        textvariable=self.np_instance.config_variables[key]).grid(column=1, row=counter)
                    counter += 1

                # save button
                save_button = tkinter.Button(
                    self.config_tab,
                    text="Save",
                    command=lambda: self.start_run('update_config', self.config_status_label))
                save_button.grid(row=2, column=0)

                # restore button
                restore_button = tkinter.Button(
                    self.config_tab,
                    text="Restore defaults",
                    command=lambda: self.start_run('restore_config', self.config_status_label))
                restore_button.grid(row=3, column=0)
                self.config_tab_initalized = True

                self.config_status_label = ttk.Label(self.config_tab, text="")
                self.config_status_label.grid(column=0, row=4, sticky='W')

    def config_general_tab(self):
        # General Tab

        # self.general_tab.grid(column=0, row=0, sticky=('N', 'W', 'E', 'S'))
        # self.general_tab.grid_columnconfigure(0, weight=1)
        # self.general_tab.grid_rowconfigure(0, weight=1)

        # default config file
        ttk.Label(self.general_tab, text="Default config file:").grid(
            column=0, row=0, sticky='W')
        default_config_entry = ttk.Entry(
            self.general_tab, width=40, textvariable=self.np_instance.default_config_path)
        default_config_entry.grid(column=1, row=0)
        default_config_button = tkinter.Button(
            self.general_tab,
            text="Browse",
            command=lambda: self.browse_button(self.np_instance.default_config_path, self.general_tab))
        default_config_button.grid(row=0, column=2)

        # default codebook
        ttk.Label(self.general_tab, text="Default codebook:").grid(
            column=0, row=1, sticky='W')
        default_codebook_entry = ttk.Entry(
            self.general_tab, width=40, textvariable=self.np_instance.default_codebook_path)
        default_codebook_entry.grid(column=1, row=1)
        default_codebook_button = tkinter.Button(
            self.general_tab,
            text="Browse",
            command=lambda: self.browse_button(self.np_instance.default_codebook_path, self.general_tab))
        default_codebook_button.grid(row=1, column=2)

        # data path
        ttk.Label(self.general_tab, text="Data path:").grid(
            column=0, row=3, sticky='W')
        data_entry = ttk.Entry(
            self.general_tab, width=40, textvariable=self.np_instance.data_path)
        data_entry.grid(column=1, row=3)
        data_button = tkinter.Button(
            self.general_tab,
            text="Browse",
            command=lambda: self.browse_button(self.np_instance.data_path, self.general_tab))
        data_button.grid(row=3, column=2)

        # default output directory
        ttk.Label(self.general_tab, text="Output directory:").grid(
            column=0, row=4, sticky='W')
        default_codebook_entry = ttk.Entry(
            self.general_tab, width=40, textvariable=self.np_instance.output_dir)
        default_codebook_entry.grid(column=1, row=4)
        default_codebook_button = tkinter.Button(
            self.general_tab,
            text="Browse", command=lambda: self.browse_button(self.np_instance.output_dir, self.general_tab))
        default_codebook_button.grid(row=4, column=2)

        # plot type selection
        ttk.Label(self.general_tab, text="Plot type:").grid(
            column=0, row=5, sticky='W')
        global plot_type
        plot_type = tkinter.StringVar()
        plot_type.set('bars')
        g1 = ttk.Radiobutton(self.general_tab, text='Barplot',
                             variable=self.np_instance.plot_type, value='bars')
        g2 = ttk.Radiobutton(self.general_tab, text='Lineplot',
                             variable=self.np_instance.plot_type, value='lines')
        g3 = ttk.Radiobutton(self.general_tab, text='Histogram',
                             variable=self.np_instance.plot_type, value='histograms')
        g1.grid(column=1, row=5, sticky='W', padx=20)
        g2.grid(column=1, row=6, sticky='W', padx=20)
        g3.grid(column=1, row=7, sticky='W', padx=20)

        # save button
        create_out_dir_button = tkinter.Button(
            self.general_tab,
            text="Save",
            command=lambda: self.start_run('save', self.status_label))
        create_out_dir_button.grid(row=8, column=0)

        # run button
        create_out_dir_button = tkinter.Button(
            self.general_tab,
            text="Run",
            command=lambda: self.start_run('run', self.status_label))
        create_out_dir_button.grid(row=8, column=1)

        # status label
        self.status_label = ttk.Label(self.general_tab, text="")
        self.status_label.grid(column=2, row=8, sticky='W')

        # some styling
        for child in self.general_tab.winfo_children():
            child.grid_configure(padx=5 * self.scaling, pady=5 * self.scaling)

        # set focus
        default_config_entry.focus()

    def start_gui(self):
        # start GUI
        self.root.mainloop()

    def browse_button(self, path, root):
        # Allow user to select a directory and store it
        filename = tkinter.filedialog.askdirectory(master=root)
        path.set(filename)

    def start_run(self, name, status_label):
        # start run function in new thread otherwise GUI freezes during execution
        exec = getattr(self.np_instance, name)
        Thread(target=exec, args=(status_label,), daemon=True).start()
