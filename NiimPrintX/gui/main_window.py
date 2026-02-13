from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

from .models import AppConfig, PrinterState
from .widgets import DesignCanvas, TextPanel, IconPanel, StatusBar, DeviceSelector
from .widgets import PrintDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.app_config = AppConfig()
        self.printer_state = PrinterState()
        self.current_file: Optional[str] = None
        
        self.setWindowTitle("NiimPrintX")
        self.setMinimumSize(1100, 800)
        self.resize(1100, 800)
        
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()
        self._connect_signals()
        
        self._center_window()

    def _center_window(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("&File")
        
        new_action = file_menu.addAction("&New")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_file)
        
        open_action = file_menu.addAction("&Open...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        
        save_action = file_menu.addAction("&Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_file)
        
        save_as_action = file_menu.addAction("Save &As...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_file_as)
        
        file_menu.addSeparator()
        
        export_action = file_menu.addAction("&Export as PNG...")
        export_action.triggered.connect(self._export_png)
        
        file_menu.addSeparator()
        
        quit_action = file_menu.addAction("&Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

    def _create_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.control_panel = QWidget()
        control_layout = QVBoxLayout(self.control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_panel = TextPanel(self.app_config)
        self.icon_panel = IconPanel(self.app_config)
        
        control_layout.addWidget(self.text_panel)
        control_layout.addWidget(self.icon_panel)
        control_layout.addStretch()
        
        self.canvas = DesignCanvas(self.app_config)
        
        self.splitter.addWidget(self.control_panel)
        self.splitter.addWidget(self.canvas)
        self.splitter.setSizes([300, 800])
        
        main_layout.addWidget(self.splitter, stretch=1)
        
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        self.device_selector = DeviceSelector(self.app_config, self.printer_state)
        bottom_layout.addWidget(self.device_selector)
        bottom_layout.addStretch()
        
        main_layout.addWidget(bottom_widget)

    def _create_status_bar(self):
        self.status_bar = StatusBar(self.app_config, self.printer_state)
        self.setStatusBar(self.status_bar)

    def _connect_signals(self):
        self.text_panel.text_added.connect(self._on_text_added)
        self.text_panel.text_updated.connect(self._on_text_updated)
        self.text_panel.text_deleted.connect(self._on_text_deleted)
        
        self.icon_panel.icon_added.connect(self._on_icon_added)
        
        self.canvas.item_selected.connect(self._on_item_selected)
        self.canvas.selection_cleared.connect(self._on_selection_cleared)
        
        self.device_selector.print_requested.connect(self._on_print_requested)

    def _new_file(self):
        self.canvas.clear_all()
        self.current_file = None
        self.setWindowTitle("NiimPrintX - Untitled")

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Label File",
            "",
            "NiimPrintX Files (*.niim);;All Files (*)"
        )
        if file_path:
            try:
                self.canvas.load_from_file(file_path)
                self.current_file = file_path
                self.setWindowTitle(f"NiimPrintX - {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def _save_file(self):
        if self.current_file:
            try:
                self.canvas.save_to_file(self.current_file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
        else:
            self._save_file_as()

    def _save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Label File",
            "",
            "NiimPrintX Files (*.niim);;All Files (*)"
        )
        if file_path:
            if not file_path.endswith('.niim'):
                file_path += '.niim'
            try:
                self.canvas.save_to_file(file_path)
                self.current_file = file_path
                self.setWindowTitle(f"NiimPrintX - {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def _export_png(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export as PNG",
            "",
            "PNG Files (*.png);;All Files (*)"
        )
        if file_path:
            if not file_path.endswith('.png'):
                file_path += '.png'
            try:
                self.canvas.export_to_png(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")

    def _on_text_added(self, text_item):
        self.canvas.add_text_item(text_item)

    def _on_text_updated(self, text_item):
        self.canvas.update_text_item(text_item)

    def _on_text_deleted(self):
        self.canvas.delete_selected()

    def _on_icon_added(self, icon_path):
        self.canvas.add_image_item(icon_path)

    def _on_item_selected(self, item):
        if hasattr(item, 'get_text_data'):
            self.text_panel.load_text_item(item)

    def _on_selection_cleared(self):
        self.text_panel.clear_selection()

    def _on_print_requested(self):
        bt_worker = self.device_selector.get_bt_worker()
        dialog = PrintDialog(self, self.app_config, self.printer_state, self.canvas, bt_worker)
        dialog.exec()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Quit",
            "Do you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
