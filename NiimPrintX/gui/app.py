import sys
import platform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class Application(QApplication):
    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv
        super().__init__(argv)
        
        self.setApplicationName("NiimPrintX")
        self.setApplicationDisplayName("NiimPrintX Label Printer")
        self.setOrganizationName("NiimPrintX")
        