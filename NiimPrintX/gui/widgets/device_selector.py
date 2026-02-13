from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QSpinBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QThread

from ..models import AppConfig, PrinterState
from ..workers import BluetoothWorker


LABEL_TYPE_MAP = {
    "Y4513120A": "40mm x 12mm",
    "Y4513000A": "50mm x 14mm",
    "Y4513120C": "30mm x 15mm",
}


class DeviceSelector(QWidget):
    print_requested = pyqtSignal()
    
    def __init__(self, app_config: AppConfig, printer_state: PrinterState, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self.printer_state = printer_state
        self._bt_worker: Optional[BluetoothWorker] = None
        
        self._setup_ui()
        self._connect_signals()
        self._set_initial_values()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("Device:"))
        
        self.device_combo = QComboBox()
        self.device_combo.addItems(self.app_config.get_device_list())
        self.device_combo.setCurrentText("D110")
        layout.addWidget(self.device_combo)
        
        layout.addWidget(QLabel("Label size:"))
        
        self.label_size_combo = QComboBox()
        self._populate_label_sizes()
        layout.addWidget(self.label_size_combo)
        
        layout.addWidget(QLabel("Density:"))
        
        self.density_spin = QSpinBox()
        self.density_spin.setRange(1, 5)
        self.density_spin.setValue(3)
        layout.addWidget(self.density_spin)
        
        layout.addSpacing(20)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setCheckable(True)
        layout.addWidget(self.connect_btn)
        
        layout.addStretch()
        
        self.print_btn = QPushButton("Print")
        self.print_btn.setEnabled(False)
        self.print_btn.clicked.connect(self._on_print_clicked)
        layout.addWidget(self.print_btn)
    
    def _connect_signals(self):
        self.device_combo.currentTextChanged.connect(self._on_device_changed)
        self.label_size_combo.currentTextChanged.connect(self._on_label_size_changed)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        
        self.printer_state.connected_changed.connect(self._on_connection_changed)
        self.printer_state.status_changed.connect(self._on_status_changed)
    
    def _set_initial_values(self):
        device = self.device_combo.currentText()
        self.app_config.device = device.lower()
        
        label_size = self.label_size_combo.currentText()
        if label_size:
            self.app_config.current_label_size = label_size
    
    def _populate_label_sizes(self):
        device = self.device_combo.currentText().lower()
        sizes = self.app_config.get_label_sizes_for_device(device)
        self.label_size_combo.clear()
        self.label_size_combo.addItems(sizes)
    
    def _update_label_sizes(self):
        device = self.device_combo.currentText().lower()
        sizes = self.app_config.get_label_sizes_for_device(device)
        self.label_size_combo.blockSignals(True)
        self.label_size_combo.clear()
        self.label_size_combo.addItems(sizes)
        if sizes:
            self.label_size_combo.setCurrentIndex(0)
        self.label_size_combo.blockSignals(False)
        
        label_size = self.label_size_combo.currentText()
        if label_size:
            self.app_config.current_label_size = label_size
    
    def _on_device_changed(self, device: str):
        self.app_config.device = device.lower()
        self._update_label_sizes()
    
    def _on_label_size_changed(self, size: str):
        self.app_config.current_label_size = size
    
    def _on_connect_clicked(self, checked: bool):
        if checked:
            self._connect_to_printer()
        else:
            self._disconnect()
    
    def _connect_to_printer(self):
        model = self.device_combo.currentText().lower()
        
        self.connect_btn.setText("Connecting...")
        self.connect_btn.setEnabled(False)
        self.printer_state.set_status(f"Searching for {model.upper()}...")
        
        self._bt_worker = BluetoothWorker()
        
        self._bt_worker.connected.connect(self._on_connected)
        self._bt_worker.disconnected.connect(self._on_disconnected)
        self._bt_worker.error.connect(self._on_error)
        self._bt_worker.rfid_detected.connect(self._on_rfid_detected)
        
        self._bt_worker.connect_by_model(model)
    
    def _on_connected(self, device):
        self.printer_state.current_device = device
        self.printer_state.connected = True
        self.printer_state.set_status(f"Connected to {device.name}")
        
        self.connect_btn.setText("Disconnect")
        self.connect_btn.setEnabled(True)
        self.connect_btn.setChecked(True)
        self.print_btn.setEnabled(True)
    
    def _on_rfid_detected(self, rfid_info):
        from loguru import logger
        logger.info(f"RFID info received: {rfid_info}")
        
        barcode = rfid_info.get("barcode", "")
        total_len = rfid_info.get("total_len", 0)
        
        if barcode in LABEL_TYPE_MAP:
            label_size = LABEL_TYPE_MAP[barcode]
            logger.info(f"Detected label size from barcode: {label_size}")
            
            index = self.label_size_combo.findText(label_size)
            if index >= 0:
                self.label_size_combo.setCurrentIndex(index)
                self.printer_state.set_status(f"Detected: {label_size}")
            else:
                logger.warning(f"Label size {label_size} not in dropdown")
        else:
            logger.info(f"Unknown barcode: {barcode}, total_len: {total_len}mm")
            self.printer_state.set_status(f"Connected (unknown label type)")
    
    def _disconnect(self):
        self.connect_btn.setText("Disconnecting...")
        self.connect_btn.setEnabled(False)
        
        if self._bt_worker:
            self._bt_worker.disconnect()
        else:
            self._on_disconnected()
    
    def _on_disconnected(self):
        self.printer_state.connected = False
        self.printer_state.current_device = None
        self._reset_connect_button()
    
    def _on_error(self, error: str):
        QMessageBox.critical(self, "Connection Error", error)
        self._reset_connect_button()
        self.printer_state.set_status(f"Error: {error}")
    
    def _reset_connect_button(self):
        self.connect_btn.setText("Connect")
        self.connect_btn.setEnabled(True)
        self.connect_btn.setChecked(False)
    
    def _on_connection_changed(self, connected: bool):
        if connected:
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setChecked(True)
            self.print_btn.setEnabled(True)
        else:
            self.connect_btn.setText("Connect")
            self.connect_btn.setChecked(False)
            self.print_btn.setEnabled(False)
    
    def _on_status_changed(self, status: str):
        pass
    
    def _on_print_clicked(self):
        self.print_requested.emit()
    
    def get_bt_worker(self):
        return self._bt_worker
