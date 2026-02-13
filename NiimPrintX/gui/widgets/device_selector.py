from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QSpinBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QThread

from ..models import AppConfig, PrinterState
from ..workers import BluetoothWorker


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
        self._bt_worker.cloud_label_detected.connect(self._on_cloud_label_detected)
        
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
    
    def _on_cloud_label_detected(self, label_info):
        from loguru import logger
        logger.info(f"Cloud label detected: {label_info.width_mm}x{label_info.height_mm}mm - {label_info.name_en}")
        
        label_size = f"{label_info.width_mm}mm x {label_info.height_mm}mm"
        
        index = self.label_size_combo.findText(label_size)
        if index >= 0:
            self.label_size_combo.setCurrentIndex(index)
            self.printer_state.set_status(f"Detected: {label_info.name_en}")
        else:
            logger.info(f"Label size {label_size} not in dropdown, checking alternatives...")
            self._find_closest_label_size(label_info.width_mm, label_info.height_mm, label_info.name_en)
    
    def _find_closest_label_size(self, width_mm: int, height_mm: int, label_name: str):
        from loguru import logger
        
        device = self.app_config.device
        if not device:
            return
        
        sizes = self.app_config.label_sizes.get(device, {}).get('size', {})
        
        best_match = None
        best_diff = float('inf')
        
        for size_name, (size_w, size_h) in sizes.items():
            diff = abs(size_w - width_mm) + abs(size_h - height_mm)
            if diff < best_diff:
                best_diff = diff
                best_match = size_name
        
        if best_match and best_diff <= 2:
            index = self.label_size_combo.findText(best_match)
            if index >= 0:
                self.label_size_combo.setCurrentIndex(index)
                self.printer_state.set_status(f"Detected: {label_name} (~{best_match})")
                logger.info(f"Matched to closest size: {best_match}")
        else:
            self.printer_state.set_status(f"Detected: {label_name}")
            logger.warning(f"No close match found for {width_mm}x{height_mm}mm")
    
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
