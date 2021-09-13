# Authors: Dominik Zuercher, Valeria Glauser

from niceplots import niceplot_API
from niceplots import gui

def main():
    GUI = gui.GUI()

    np_instance = niceplot_API.niceplots_handles()

    GUI.config_gui(np_instance)
    GUI.start_gui()

if __name__ == '__main__':
    main()
