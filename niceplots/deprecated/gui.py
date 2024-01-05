# Authors: Dominik Zuercher, Valeria Glauser

import glob
import os
import sys
import threading

# from tkPDFViewer import tkPDFViewer as pdf
import tkinter.filedialog
from threading import Thread

import fitz
import numpy as np

try:
    import tkinter
except ImportError:
    raise Exception(
        "Could not import tkinter. This means tk is not configured properly. On Linux this can be solved by installing tk."
    )
import logging
import tkinter.font as tkFont
from tkinter import ttk

LOGGER = logging.getLogger(__name__)


class GUI:
    """Handles niceplots GUI"""

    def __init__(self):
        self.status_label = None

        # root window
        self.root = tkinter.Tk()

        # set GUI scaling
        dpi = self.root.winfo_fpixels("1i")
        if dpi > 80:
            LOGGER.info("Assuming high definition. Setting GUI scaling to 2.0")
            self.scaling = 2.0
        else:
            self.scaling = 1.0
        self.root.tk.call("tk", "scaling", self.scaling)

        self.root.geometry("1000x500")
        self.root.title("nice-plots")

        # font
        self.default_font = tkFont.Font(
            family="Arial", size=int(8 * self.scaling), weight="bold"
        )
        self.root.option_add("*Font", self.default_font)
        s = ttk.Style()
        s.configure("TNotebook.Tab", font=("Arial", f"{int(8 * self.scaling)}", "bold"))
        s.configure("TRadiobutton", font=("Arial", f"{int(8 * self.scaling)}", "bold"))
        s.configure("TButton", font=("Arial", f"{int(8 * self.scaling)}", "bold"))

    def config_gui(self, np_instance):
        """Configure the GUI"""
        # initalize niceplots API instance
        self.np_instance = np_instance

        # Multi Tab setup
        self.tabControl = ttk.Notebook(self.root)
        self.tabControl.pack(expand=True)
        self.general_tab = ttk.Frame(self.tabControl)
        self.config_tab = ttk.Frame(self.tabControl)
        self.code_tab = ttk.Frame(self.tabControl)
        self.preview_tab = ttk.Frame(self.tabControl)

        self.general_tab.pack(fill="both", expand=True)
        self.config_tab.pack(fill="both", expand=True)
        self.code_tab.pack(fill="both", expand=True)
        self.preview_tab.pack(fill="both", expand=True)

        self.tabControl.add(self.general_tab, text="General")
        self.tabControl.add(self.config_tab, text="Config")
        self.tabControl.add(self.code_tab, text="Codebook")
        self.tabControl.add(self.preview_tab, text="Preview")

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
            self.preview_label = ttk.Label(self.preview_tab, text="")
            self.preview_label.grid(column=0, row=0, columnspan=3, sticky="W")
            self.preview_tab_initalized = False
        if not self.preview_tab_initalized:
            if self.np_instance.global_plotting_data is None:
                self.preview_label.config(
                    text="No plots to show yet. Press Save and Run in General tab first."
                )
            elif (
                len(
                    glob.glob(
                        self.np_instance.ctx["output_directory"]
                        + "/*."
                        + self.np_instance.ctx["format"]
                    )
                )
                == 0
            ):
                self.preview_label.config(
                    text="No plots to show yet. Press Save and Run in General tab first."
                )
            else:
                # description
                description = (
                    " Here you can have a look at how the plots look like. \n "
                    "If you make changes to the configuration file or codebook you can hit Refresh \n "
                    "and click on the plot name in the list again to get an updated view of the plot. \n "
                    "Clicking Refresh All will rerun all the plots. \n \n "
                    "Preview: \n \n "
                )
                self.preview_label.config(text=description)

                self.preview_tab_initalized = True

                Lb = tkinter.Listbox(self.preview_tab)
                Lb.grid(row=1, column=0, sticky=("W", "E", "N", "S"))

                plots = glob.glob(
                    self.np_instance.ctx["output_directory"]
                    + "/*."
                    + self.np_instance.ctx["format"]
                )
                plots = np.asarray(plots)
                self.plots = np.sort(plots)
                for idx, plot in enumerate(self.plots):
                    Lb.insert(idx, os.path.basename(plot))

                def callback(event=None):
                    if event is not None:
                        selection = event.widget.curselection()
                        if selection:
                            self.viewer_index.set(selection[0])
                        else:
                            self.viewer_index.set(0)

                        fname = str(self.plots[int(self.viewer_index.get())])
                        doc = fitz.open(fname)
                        page = doc.load_page(0)
                        pix = page.get_pixmap()
                        imgdata = pix.tobytes("ppm")  # extremely fast!, no PIL
                        photo = tkinter.PhotoImage(data=imgdata)
                        self.preview_window.configure(image=photo)
                        self.preview_window.image = photo

                    else:
                        self.viewer_index = tkinter.StringVar()
                        self.viewer_index.set(0)

                        fname = str(self.plots[int(self.viewer_index.get())])
                        doc = fitz.open(fname)
                        page = doc.load_page(0)
                        pix = page.get_pixmap()
                        imgdata = pix.tobytes("ppm")  # extremely fast!, no PIL
                        photo = tkinter.PhotoImage(data=imgdata)

                        self.preview_window = ttk.Label(self.preview_tab, image=photo)
                        self.preview_window.image = photo
                        self.preview_window.grid(
                            row=1, column=1, sticky=("W", "E", "N", "S")
                        )

                Lb.bind("<<ListboxSelect>>", callback)

                callback()

                button_frame = tkinter.Frame(self.preview_tab)

                # refresh button
                single_refresh_button = ttk.Button(
                    button_frame,
                    text="Refresh",
                    command=lambda: self.start_single_refresh(
                        "run_single",
                        self.preview_status_label,
                        int(self.viewer_index.get()),
                    ),
                )
                single_refresh_button.grid(row=0, column=0)

                # run all button
                refresh_button = ttk.Button(
                    button_frame,
                    text="Refresh All",
                    command=lambda: self.start_refresh(
                        "run", self.preview_status_label
                    ),
                )
                refresh_button.grid(row=0, column=1)

                button_frame.grid(row=3, column=0, pady=self.scaling * 20)

                self.preview_status_label = ttk.Label(self.preview_tab, text="")
                self.preview_status_label.grid(column=0, row=4, sticky="W")

    def config_code_tab(self, event=None):
        # Config Tab
        if event is None:
            # assume initialization
            self.code_label = ttk.Label(self.code_tab, text="")
            self.code_label.grid(column=0, row=0, sticky="W")
            self.code_tab_initalized = False
        if not self.code_tab_initalized:
            if self.np_instance.codebook is None:
                self.code_label.config(
                    text="Codebook not set yet. Press Save in General tab first."
                )
            else:
                # description
                description = (
                    " Here you can edit the entries in the codebook in the output directory that is used by nice-plots. \n "
                    "Once you are done hit the Save button. \n "
                    "If you want to restore the codebook defined in the default codebook file hit the Restore defaults button. \n \n "
                    "Codebook: \n \n "
                )
                self.code_label.config(text=description)

                # add Scrollbars
                def onFrameConfigure(canvas, frame):
                    """Reset the scroll region to encompass the inner frame"""
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    canvas.config(height=1500, width=frame.winfo_width() - 40)

                canvas = tkinter.Canvas(self.code_tab, borderwidth=0)
                frame = tkinter.Frame(canvas)
                vsb = tkinter.Scrollbar(
                    self.code_tab, orient="vertical", command=canvas.yview, width=40
                )
                hsb = tkinter.Scrollbar(
                    self.code_tab, orient="horizontal", command=canvas.xview, width=40
                )
                canvas.configure(yscrollcommand=vsb.set)
                canvas.configure(xscrollcommand=hsb.set)
                vsb.grid(row=1, column=1, sticky=("N", "S", "W", "E"))
                hsb.grid(row=2, column=0, sticky=("W", "E"))
                canvas.grid(row=1, column=0, sticky=("W", "E", "N", "S"))
                canvas.create_window((4, 4), window=frame, anchor="nw")
                frame.bind(
                    "<Configure>",
                    lambda event, canvas=canvas: onFrameConfigure(
                        canvas, self.code_tab
                    ),
                )

                # display codebook
                n_entries = self.np_instance.codebook.shape[0]

                # variables
                for idx, col in enumerate(self.np_instance.codebook):
                    if col == "Index":
                        continue
                    self.np_instance.codebook_variables[col] = []
                    # assign in loop otherswise copies variable address
                    for idy in range(n_entries):
                        self.np_instance.codebook_variables[col].append(
                            tkinter.StringVar()
                        )

                # header
                for idx, col in enumerate(self.np_instance.codebook):
                    ttk.Label(frame, text=col).grid(
                        row=0, column=idx, sticky=("W", "E")
                    )

                # data
                for idx, col in enumerate(self.np_instance.codebook):
                    data = self.np_instance.codebook[col]
                    if col == "Index":
                        for idy in range(n_entries):
                            ttk.Label(frame, text=data[idy]).grid(
                                row=idy + 1, column=idx, sticky=("W", "E")
                            )
                    else:
                        for idy in range(n_entries):
                            entry = ttk.Entry(
                                frame,
                                textvariable=self.np_instance.codebook_variables[col][
                                    idy
                                ],
                            )
                            entry.grid(row=idy + 1, column=idx, sticky=("W", "E"))
                            self.np_instance.codebook_variables[col][idy].set(data[idy])

                button_frame = ttk.Frame(self.code_tab)

                # save button
                save_button = ttk.Button(
                    button_frame,
                    text="Save",
                    command=lambda: self.start_run(
                        "update_code", self.code_status_label
                    ),
                )

                # restore button
                restore_button = ttk.Button(
                    button_frame,
                    text="Restore defaults",
                    command=lambda: self.start_run(
                        "restore_code", self.code_status_label
                    ),
                )

                save_button.grid(row=0, column=0)
                restore_button.grid(row=0, column=1)
                button_frame.grid(row=4, column=0, sticky=("W"), pady=self.scaling * 20)
                self.code_tab_initalized = True

                self.code_status_label = ttk.Label(self.code_tab, text="")
                self.code_status_label.grid(column=0, row=5, sticky="W")

    def config_config_tab(self, event=None):
        # Config Tab

        if event is None:
            # assume initialization
            self.config_label = ttk.Label(self.config_tab, text="")
            self.config_tab_initalized = False
        if not self.config_tab_initalized:
            if self.np_instance.ctx is None:
                self.config_label.config(
                    text="Configuration file not set yet. Press Save in General tab first."
                )
            else:
                # description
                description = (
                    " Here you can edit the entries in the config file in the output directory that is used by nice-plots. \n "
                    "Once you are done hit the Save button. \n "
                    "If you want to restore the settings defined in the default config file hit the Restore defaults button \n \n "
                    "Options: \n \n "
                )
                self.config_label.config(text=description)

                # add Scrollbar
                def onFrameConfigure(canvas, frame):
                    """Reset the scroll region to encompass the inner frame"""
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    canvas.config(width=frame.winfo_width())

                canvas = tkinter.Canvas(self.config_tab, borderwidth=0)
                frame = tkinter.Frame(canvas)
                vsb = tkinter.Scrollbar(
                    self.config_tab, orient="vertical", command=canvas.yview, width=40
                )
                canvas.configure(yscrollcommand=vsb.set)
                canvas.grid(row=1, column=0, sticky=("W"))
                canvas.create_window((4, 4), window=frame, anchor="nw")
                frame.bind(
                    "<Configure>",
                    lambda event, canvas=canvas: onFrameConfigure(canvas, frame),
                )

                # Display the options from the config file
                counter = 0
                # hide some options
                hide = [
                    "output_name",
                    "config_file",
                    "output_directory",
                    "codebook_path",
                    "additional_codebook_entries",
                ]
                for key in self.np_instance.ctx.keys():
                    if key in hide:
                        continue
                    ttk.Label(frame, text=key).grid(column=0, row=counter, sticky="W")

                    self.np_instance.config_variables[key] = tkinter.StringVar()
                    self.np_instance.config_variables[key].set(
                        self.np_instance.ctx[key]
                    )
                    ttk.Entry(
                        frame,
                        width=40,
                        textvariable=self.np_instance.config_variables[key],
                    ).grid(column=1, row=counter, sticky="E")
                    counter += 1

                button_frame = ttk.Frame(self.config_tab)

                # save button
                save_button = ttk.Button(
                    button_frame,
                    text="Save",
                    command=lambda: self.start_run(
                        "update_config", self.config_status_label
                    ),
                )

                # restore button
                restore_button = ttk.Button(
                    button_frame,
                    text="Restore defaults",
                    command=lambda: self.start_run(
                        "restore_config", self.config_status_label
                    ),
                )
                self.config_tab_initalized = True

                self.config_status_label = ttk.Label(self.config_tab, text="")

                # placing
                self.config_label.grid(column=0, row=0, columnspan=3, sticky="W")
                vsb.grid(row=1, column=1, sticky=("N", "S", "W"))  # scrollbar
                button_frame.grid(row=2, column=0, sticky="W")
                save_button.grid(row=0, column=0)
                restore_button.grid(row=0, column=1)
                self.config_status_label.grid(column=0, row=4, sticky="W")

                # some styling
                for child in self.general_tab.winfo_children():
                    child.grid_configure(padx=self.scaling, pady=self.scaling)
                button_frame.grid_configure(pady=self.scaling * 20)

    def config_general_tab(self):
        # description
        description = (
            " Here you can set the paths to the files that nice-plots requires and choose the type of plots. \n \n "
            "Default config file: The config file will be produced based on the default config file. \n "
            "You can then edit the config file in the Config tab. \n "
            "Default codebook: The codebook will be produced based on the default codebook. \n "
            "You can then edit the codebook in the Codebook tab.\n "
            "Data path: Path to the tabular data. The data file is never touched or modified by nice-plots! \n "
            "Output directory: The directory where the plots will be created and the new config and codebook files are stored.\n \n "
            "Once you are done press Save. You can produce all plots by pressing the Run button. \n \n "
        )

        desc_label = ttk.Label(self.general_tab, text=description)

        # default config file
        label1 = ttk.Label(self.general_tab, text="Default config file:")
        default_config_entry = ttk.Entry(
            self.general_tab,
            width=40,
            textvariable=self.np_instance.default_config_path,
        )
        default_config_button = ttk.Button(
            self.general_tab,
            text="Browse",
            command=lambda: self.browse_button(
                self.np_instance.default_config_path, self.general_tab
            ),
        )

        # default codebook
        label2 = ttk.Label(self.general_tab, text="Default codebook:")
        default_codebook_entry = ttk.Entry(
            self.general_tab,
            width=40,
            textvariable=self.np_instance.default_codebook_path,
        )
        default_codebook_button = ttk.Button(
            self.general_tab,
            text="Browse",
            command=lambda: self.browse_button(
                self.np_instance.default_codebook_path, self.general_tab
            ),
        )

        # data path
        label3 = ttk.Label(self.general_tab, text="Data path:")
        data_entry = ttk.Entry(
            self.general_tab, width=40, textvariable=self.np_instance.data_path
        )
        data_button = ttk.Button(
            self.general_tab,
            text="Browse",
            command=lambda: self.browse_button(
                self.np_instance.data_path, self.general_tab
            ),
        )

        # default output directory
        label4 = ttk.Label(self.general_tab, text="Output directory:")
        default_output_entry = ttk.Entry(
            self.general_tab, width=40, textvariable=self.np_instance.output_dir
        )
        default_output_button = ttk.Button(
            self.general_tab,
            text="Browse",
            command=lambda: self.browse_button(
                self.np_instance.output_dir, self.general_tab
            ),
        )

        # plot type selection
        label5 = ttk.Label(self.general_tab, text="Plot type:")
        global plot_type
        plot_type = tkinter.StringVar()
        plot_type.set("bars")
        g1 = ttk.Radiobutton(
            self.general_tab,
            text="Barplot",
            variable=self.np_instance.plot_type,
            value="bars",
        )
        g2 = ttk.Radiobutton(
            self.general_tab,
            text="Lineplot",
            variable=self.np_instance.plot_type,
            value="lines",
        )
        g3 = ttk.Radiobutton(
            self.general_tab,
            text="Histogram",
            variable=self.np_instance.plot_type,
            value="histograms",
        )

        button_frame = tkinter.Frame(self.general_tab)

        # save button
        save_button = ttk.Button(
            button_frame,
            text="Save",
            command=lambda: self.start_run("save", self.status_label),
        )

        # run button
        run_button = ttk.Button(
            button_frame,
            text="Run",
            command=lambda: self.start_run("run", self.status_label),
        )

        # status label
        self.status_label = ttk.Label(self.general_tab, text="")

        # placing
        desc_label.grid(column=0, row=0, columnspan=4, sticky="W")
        label1.grid(column=0, row=1, sticky="W")
        label2.grid(column=0, row=2, sticky="W")
        label3.grid(column=0, row=4, sticky="W")
        label4.grid(column=0, row=5, sticky="W")
        label5.grid(column=0, row=6, sticky="W")

        default_config_entry.grid(column=1, row=1, sticky="W")
        default_codebook_entry.grid(column=1, row=2, sticky="W")
        data_entry.grid(column=1, row=4, sticky="W")
        default_output_entry.grid(column=1, row=5, sticky="W")

        default_config_button.grid(row=1, column=2, sticky="W")
        default_codebook_button.grid(row=2, column=2, sticky="W")
        data_button.grid(row=4, column=2, sticky="W")
        default_output_button.grid(row=5, column=2, sticky="W")

        g1.grid(column=1, row=6, sticky="W", padx=20)
        g2.grid(column=1, row=7, sticky="W", padx=20)
        g3.grid(column=1, row=8, sticky="W", padx=20)

        self.status_label.grid(column=2, row=9, sticky="W")

        button_frame.grid(row=9, column=0, sticky="W")
        save_button.grid(row=0, column=0, sticky="W")
        run_button.grid(row=0, column=1, sticky="E")

        # some styling
        for child in self.general_tab.winfo_children():
            child.grid_configure(padx=self.scaling, pady=self.scaling)

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

    def start_refresh(self, name, status_label):
        # start run function in new thread otherwise GUI freezes during execution
        exec = getattr(self.np_instance, name)
        Thread(target=exec, args=(status_label,), daemon=True).start()

    def start_single_refresh(self, name, status_label, index):
        # start run function in new thread otherwise GUI freezes during execution
        exec = getattr(self.np_instance, name)
        Thread(target=exec, args=(status_label, index), daemon=True).start()

    def config_log_tab(self, event=None):
        class ConsoleText(tkinter.Text):
            """A Tkinter Text widget that provides a scrolling display of console
            stderr and stdout.
            """

            class IORedirector:
                """A general class for redirecting I/O to this Text widget."""

                def __init__(self, text_area):
                    self.text_area = text_area

            class StdoutRedirector(IORedirector):
                """A class for redirecting stdout to this Text widget."""

                def write(self, str):
                    self.text_area.write(str, False)

            class StderrRedirector(IORedirector):
                """A class for redirecting stderr to this Text widget."""

                def write(self, str):
                    self.text_area.write(str, True)

            def __init__(self, master=None, cnf={}, **kw):
                """See the __init__ for Tkinter.Text for most of this stuff."""
                tkinter.Text.__init__(self, master, cnf, **kw)

                self.started = False
                self.write_lock = threading.Lock()

                self.tag_configure("STDOUT", background="white", foreground="black")
                self.tag_configure("STDERR", background="white", foreground="red")

                self.config(state=tkinter.NORMAL)
                self.bind("<Key>", lambda e: "break")  # ignore all key presses

            def start(self):
                if self.started:
                    return

                self.started = True

                self.original_stdout = sys.stdout
                self.original_stderr = sys.stderr

                stdout_redirector = ConsoleText.StdoutRedirector(self)
                stderr_redirector = ConsoleText.StderrRedirector(self)

                sys.stdout = stdout_redirector
                sys.stderr = stderr_redirector

            def stop(self):
                if not self.started:
                    return

                self.started = False

                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

            def write(self, val, is_stderr=False):
                self.write_lock.acquire()

                self.insert("end", val, "STDERR" if is_stderr else "STDOUT")
                self.see("end")

                self.write_lock.release()

        self.console_log = ConsoleText(self.log_tab)
        self.console_log.start()
        self.console_log.grid(row=0, column=0, sticky=("W", "E", "N", "S"))
