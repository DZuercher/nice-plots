==========
nice-plots
==========

Introduction
============

nice-plots allows to easily and automatically visualize survey data.
Currently there are 3 different types of visualization:

barplot:
--------

.. image:: examples/barplots/barplots_2.png
    :width: 500px

lineplot:
---------

.. image:: examples/lineplots/lineplots_4.png
    :width: 500px

histogram:
----------

.. image:: examples/histograms/histograms_0.png
    :width: 500px


Installation
============

Open a terminal and clone the nice-plots repository:

    $ git clone https://github.com/DZuercher/nice-plots.git

Enter the nice-plots directory:

    $ cd nice-plots

Install nice-plots:

    $ pip install . --user

Usage
=====

nice-plots is most easily used via CLI.
Just run

    $ nice-plots --help

to get a list of the arguments that nice-plots accepts.
nice-plots requires a YAML config file, a codebook and a data table.

There is an example configuration file in the examples directory explaining all the
different keywords that nice-plots accepts.

The plot_type keyword allows you to switch between the different types of
visualization.

The name keyword specifies how the output directory will be called. The output directory is created in the location indicated by the prefix argument.

nice-plots copies the codebook, config file and the data to the output directory and will
use these instead of the ones provided with the config, data and codebook arguments
whenever you rerun nice-plots with the same name.
You can ignore the previously generated files by passing the full-rerun keyword.

For a quick test of nice-plots navigate over to the examples directory and
run:

    $ nice-plots --config=example_config.yml --codebook=example_codebook.csv --data=example_data.csv --name=output1 --plot_type=bars

Credits
=======

Main developer: Dominik Zuercher, dominikzuercher1999@gmail.com
Co-Developer: Valeria Glauser

You are free to use and modify nice-plots however you wish but we would be
glad if you cite this repository in your work.
