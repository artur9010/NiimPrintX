from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import Qt

from ..models import AppConfig, PrinterState


class StatusBar(QStatusBar):
    def __init__(self, app_config: AppConfig, printer_state: PrinterState, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self.printer_state = printer_state
        
        self._status_label = QLabel("Ready")
        self._printer_label = QLabel("Not connected")
        
        self.addWidget(self._status_label, 1)
        self.addPermanentWidget(self._printer_label)
        
        self._connect_signals()
    
    def _connect_signals(self):
        self.printer_state.connected_changed.connect(self._on_connection_changed)
        self.printer_state.status_changed.connect(self._on_status_changed)
        self.printer_state.connection_error.connect(self._on_error)
        self.app_config.label_size_changed.connect(self._on_label_changed)
    
    def _on_connection_changed(self, connected: bool):
        if connected:
            device = self.printer_state.current_device
            name = device.name if device else "Printer"
            self._printer_label.setText(f"Connected: {name}")
            self._printer_label.setStyleSheet("color: green;")
        else:
            self._printer_label.setText("Not connected")
            self._printer_label.setStyleSheet("color: gray;")
    
    def _on_status_changed(self, status: str):
        self._status_label.setText(status)
    
    def _on_error(self, error: str):
        self._status_label.setText(f"Error: {error}")
        self._status_label.setStyleSheet("color: red;")
    
    def _on_label_changed(self, size: str):
        device = self.app_config.device.upper() if self.app_config.device else "Unknown"
        self._status_label.setText(f"Device: {device}, Size: {size}")
