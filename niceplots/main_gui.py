# Authors: Dominik Zuercher, Valeria Glauser

from niceplots import objects

def main():
    gui = objects.GUI()

    np_instance = objects.niceplots_handles()

    gui.config_gui(np_instance)
    gui.start_gui()

if __name__ == '__main__':
    main()
