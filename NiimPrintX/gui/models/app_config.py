import os
import appdirs
import platform
from PyQt6.QtCore import QObject, pyqtSignal


class AppConfig(QObject):
    device_changed = pyqtSignal(str)
    label_size_changed = pyqtSignal(str)
    printer_connected_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.os_system = platform.system()
        self.print_dpi = 203
        self.screen_dpi = 72
        self.current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.icon_folder = os.path.join(self.current_dir, "icons")
        self.cache_dir = appdirs.user_cache_dir('NiimPrintX')
        
        self._device = None
        self._current_label_size = None
        self._printer_connected = False
        
        self.label_sizes = {
            "d110": {
                "size": {
                    "30mm x 15mm": (30, 15),
                    "40mm x 12mm": (40, 12),
                    "50mm x 14mm": (50, 14),
                    "75mm x 12mm": (75, 12),
                    "109mm x 12.5mm": (109, 12.5),
                },
                "density": 3
            },
            "d11": {
                "size": {
                    "30mm x 14mm": (30, 14),
                    "40mm x 12mm": (40, 12),
                    "50mm x 14mm": (50, 14),
                    "75mm x 12mm": (75, 12),
                    "109mm x 12.5mm": (109, 12.5),
                },
                "density": 3
            },
            "d101": {
                "size": {
                    "30mm x 14mm": (30, 14),
                    "40mm x 12mm": (40, 12),
                    "50mm x 14mm": (50, 14),
                    "75mm x 12mm": (75, 12),
                    "109mm x 12.5mm": (109, 12.5),
                },
                "density": 3
            },
            "b18": {
                "size": {
                    "40mm x 14mm": (40, 14),
                    "50mm x 14mm": (50, 14),
                    "120mm x 14mm": (120, 14),
                },
                "density": 3
            }
        }
        
        self.print_job = False
        self.printer_client = None

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        if self._device != value:
            self._device = value
            self.device_changed.emit(value)

    @property
    def current_label_size(self):
        return self._current_label_size

    @current_label_size.setter
    def current_label_size(self, value):
        if self._current_label_size != value:
            self._current_label_size = value
            self.label_size_changed.emit(value)

    @property
    def printer_connected(self):
        return self._printer_connected

    @printer_connected.setter
    def printer_connected(self, value):
        if self._printer_connected != value:
            self._printer_connected = value
            self.printer_connected_changed.emit(value)

    def get_label_size_mm(self):
        if self.device and self.current_label_size:
            return self.label_sizes[self.device]['size'][self.current_label_size]
        return (50, 14)

    def get_label_density(self):
        if self.device:
            return self.label_sizes[self.device]['density']
        return 3

    def mm_to_pixels(self, mm):
        inches = mm / 25.4
        return int(inches * self.print_dpi)

    def get_device_list(self):
        return list(map(str.upper, self.label_sizes.keys()))

    def get_label_sizes_for_device(self, device):
        device = device.lower()
        if device in self.label_sizes:
            return list(self.label_sizes[device]['size'].keys())
        return []
