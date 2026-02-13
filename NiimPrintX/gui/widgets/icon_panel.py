import os
from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QFileDialog, QPushButton, QLabel, QGroupBox
from PyQt6.QtCore import pyqtSignal, Qt

from ..models import AppConfig
from .icon_grid import TabbedIconGrid


class IconPanel(QWidget):
    icon_added = pyqtSignal(str)
    
    def __init__(self, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Icons")
        group_layout = QVBoxLayout(group)
        
        self.tabbed_grid = TabbedIconGrid(self.app_config.icon_folder)
        self.tabbed_grid.icon_selected.connect(self._on_icon_selected)
        group_layout.addWidget(self.tabbed_grid)
        
        import_row = QWidget()
        import_layout = QVBoxLayout(import_row)
        import_layout.setContentsMargins(0, 0, 0, 0)
        
        import_btn = QPushButton("Import Image...")
        import_btn.clicked.connect(self._on_import_clicked)
        import_layout.addWidget(import_btn)
        
        group_layout.addWidget(import_row)
        
        layout.addWidget(group)
        layout.addStretch()
    
    def _on_icon_selected(self, icon_path: str):
        self.icon_added.emit(icon_path)
    
    def _on_import_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.svg);;All Files (*)"
        )
        if file_path:
            self.icon_added.emit(file_path)
