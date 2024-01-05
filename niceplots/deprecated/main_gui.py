# Authors: Dominik Zuercher, Valeria Glauser

from niceplots import gui, niceplot_API
from niceplots import main as climain


def main():
    LOGGER = climain.init_logger("niceplots")
    climain.set_logger_level(LOGGER, 4)

    GUI = gui.GUI()

    np_instance = niceplot_API.niceplots_handles()

    GUI.config_gui(np_instance)
    GUI.start_gui()


if __name__ == "__main__":
    main()
