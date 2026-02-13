from typing import Optional, List
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class DiscoveredDevice:
    address: str
    name: str
    rssi: int = 0


class PrinterState(QObject):
    scanning_changed = pyqtSignal(bool)
    devices_found = pyqtSignal(list)
    connected_changed = pyqtSignal(bool)
    connection_error = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._scanning = False
        self._connected = False
        self._current_device: Optional[DiscoveredDevice] = None
        self._discovered_devices: List[DiscoveredDevice] = []

    @property
    def scanning(self) -> bool:
        return self._scanning

    @scanning.setter
    def scanning(self, value: bool):
        if self._scanning != value:
            self._scanning = value
            self.scanning_changed.emit(value)

    @property
    def connected(self) -> bool:
        return self._connected

    @connected.setter
    def connected(self, value: bool):
        if self._connected != value:
            self._connected = value
            self.connected_changed.emit(value)

    @property
    def current_device(self) -> Optional[DiscoveredDevice]:
        return self._current_device

    @current_device.setter
    def current_device(self, value: Optional[DiscoveredDevice]):
        self._current_device = value

    @property
    def discovered_devices(self) -> List[DiscoveredDevice]:
        return self._discovered_devices

    def set_discovered_devices(self, devices: List[DiscoveredDevice]):
        self._discovered_devices = devices
        self.devices_found.emit(devices)

    def clear_devices(self):
        self._discovered_devices = []
        self.devices_found.emit([])

    def set_status(self, status: str):
        self.status_changed.emit(status)

    def report_error(self, error: str):
        self.connection_error.emit(error)
