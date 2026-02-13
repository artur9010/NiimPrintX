import sys


def main():
    from NiimPrintX.gui.app import Application
    from NiimPrintX.gui.main_window import MainWindow
    
    app = Application(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
