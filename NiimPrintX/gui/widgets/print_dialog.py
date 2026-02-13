from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QProgressBar, QGroupBox, QFormLayout, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from ..models import AppConfig, PrinterState
from ..workers import BluetoothWorker


class PrintDialog(QDialog):
    def __init__(self, parent, app_config: AppConfig, printer_state: PrinterState, 
                 canvas, bt_worker: Optional[BluetoothWorker] = None, parent_widget=None):
        super().__init__(parent_widget)
        self.app_config = app_config
        self.printer_state = printer_state
        self.canvas = canvas
        self._bt_worker = bt_worker
        
        self.setWindowTitle("Print Label")
        self.setMinimumSize(400, 500)
        self.setModal(True)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        preview_group = QGroupBox("Preview (Actual Size)")
        preview_layout = QVBoxLayout(preview_group)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)
        scroll_area.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setWidget(self.preview_label)
        
        width_mm, height_mm = self.app_config.get_label_size_mm()
        label_width = self.app_config.mm_to_pixels(width_mm)
        label_height = self.app_config.mm_to_pixels(height_mm)
        
        max_preview_width = 400
        max_preview_height = 300
        scroll_area.setMinimumSize(
            min(label_width + 20, max_preview_width),
            min(label_height + 20, max_preview_height)
        )
        
        preview_layout.addWidget(scroll_area)
        
        layout.addWidget(preview_group)
        
        self._update_preview()
        
        settings_group = QGroupBox("Print Settings")
        settings_layout = QFormLayout(settings_group)
        
        label_size = self.app_config.current_label_size or "Unknown"
        device = self.app_config.device.upper() if self.app_config.device else "Unknown"
        self.label_size_label = QLabel(f"{label_size} ({device})")
        settings_layout.addRow("Label size:", self.label_size_label)
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100)
        self.quantity_spin.setValue(1)
        settings_layout.addRow("Quantity:", self.quantity_spin)
        
        self.density_spin = QSpinBox()
        self.density_spin.setRange(1, 5)
        self.density_spin.setValue(self.app_config.get_label_density())
        settings_layout.addRow("Density:", self.density_spin)
        
        layout.addWidget(settings_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.print_btn = QPushButton("Print")
        self.print_btn.clicked.connect(self._on_print_clicked)
        button_layout.addWidget(self.print_btn)
        
        layout.addLayout(button_layout)
    
    def _update_preview(self):
        image = self.canvas.get_print_image()
        if image:
            pixmap = QPixmap.fromImage(image)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setFixedSize(pixmap.size())
    
    def _on_print_clicked(self):
        if self._bt_worker is None:
            QMessageBox.critical(self, "Error", "Printer not connected")
            return
        
        quantity = self.quantity_spin.value()
        density = self.density_spin.value()
        
        self.print_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(quantity)
        self.progress_bar.setValue(0)
        self.status_label.setText("Printing...")
        
        qimage = self.canvas.get_print_image()
        if qimage is None:
            self._on_error("No image to print")
            return
        
        pil_image = self._qimage_to_pil(qimage)
        if pil_image is None:
            self._on_error("Failed to convert image")
            return
        
        self._bt_worker.print_progress.connect(self._on_progress)
        self._bt_worker.print_finished.connect(self._on_finished)
        self._bt_worker.print_error.connect(self._on_error)
        
        self._bt_worker.print_image(pil_image, density, quantity)
    
    def _on_progress(self, value: int):
        self.progress_bar.setValue(value)
    
    def _on_finished(self, success: bool):
        self.status_label.setText("Print completed!")
        self.accept()
    
    def _on_error(self, error: str):
        self.status_label.setText(f"Error: {error}")
        self.progress_bar.setVisible(False)
        self.print_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        QMessageBox.critical(self, "Print Error", error)
    
    def _qimage_to_pil(self, qimage):
        from PyQt6.QtCore import QByteArray, QBuffer
        from PIL import Image
        import io
        from loguru import logger
        
        logger.info(f"QImage dimensions: {qimage.width()}x{qimage.height()}")
        
        buffer = QByteArray()
        buffer_device = QBuffer(buffer)
        buffer_device.open(QBuffer.OpenModeFlag.WriteOnly)
        qimage.save(buffer_device, "PNG")
        
        pil_image = Image.open(io.BytesIO(bytes(buffer.data())))
        logger.info(f"PIL before rotation: {pil_image.width}x{pil_image.height}")
        
        pil_image = pil_image.rotate(-90, Image.NEAREST, expand=True)
        logger.info(f"PIL after rotation: {pil_image.width}x{pil_image.height}")
        
        return pil_image.convert("RGBA")
