import os
from typing import List, Dict
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QScrollArea, QLabel, QTabWidget
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QThread, QUrl
from PyQt6.QtGui import QPixmap, QCursor


class IconLoaderThread(QThread):
    icons_loaded = pyqtSignal(list)
    
    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
    
    def run(self):
        icons = []
        if os.path.isdir(self.folder_path):
            for file in os.listdir(self.folder_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')):
                    icons.append(os.path.join(self.folder_path, file))
        self.icons_loaded.emit(icons)


class IconGridWidget(QLabel):
    clicked = pyqtSignal(str)
    
    def __init__(self, icon_path: str, size: int = 64, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._load_icon()
    
    def _load_icon(self):
        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.icon_path)


class IconGrid(QScrollArea):
    icon_selected = pyqtSignal(str)
    
    def __init__(self, folder_path: str = "", parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self._icons: List[str] = []
        self._loader_thread: IconLoaderThread = None
        
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self._container = QWidget()
        self._layout = QGridLayout(self._container)
        self._layout.setSpacing(5)
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self._container)
        
        if folder_path:
            self.load_icons(folder_path)
    
    def load_icons(self, folder_path: str):
        self.folder_path = folder_path
        self._clear_grid()
        
        if self._loader_thread and self._loader_thread.isRunning():
            self._loader_thread.terminate()
        
        self._loader_thread = IconLoaderThread(folder_path)
        self._loader_thread.icons_loaded.connect(self._on_icons_loaded)
        self._loader_thread.start()
    
    def _on_icons_loaded(self, icons: List[str]):
        self._icons = icons
        self._populate_grid()
    
    def _clear_grid(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _populate_grid(self):
        self._clear_grid()
        
        cols = 4
        for index, icon_path in enumerate(self._icons):
            row = index // cols
            col = index % cols
            
            icon_widget = IconGridWidget(icon_path, 48)
            icon_widget.clicked.connect(self._on_icon_clicked)
            self._layout.addWidget(icon_widget, row, col)
    
    def _on_icon_clicked(self, icon_path: str):
        self.icon_selected.emit(icon_path)
    
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() - delta // 2)


class TabbedIconGrid(QWidget):
    icon_selected = pyqtSignal(str)
    
    def __init__(self, icon_folder: str, parent=None):
        super().__init__(parent)
        self.icon_folder = icon_folder
        self._loaded_tabs: Dict[str, bool] = {}
        
        self._setup_ui()
        self._load_tabs()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_widget)
    
    def _load_tabs(self):
        if not os.path.isdir(self.icon_folder):
            self.tab_widget.addTab(QLabel("No icons folder found"), "Empty")
            return
        
        subdirs = []
        for item in os.listdir(self.icon_folder):
            item_path = os.path.join(self.icon_folder, item)
            if os.path.isdir(item_path):
                subdirs.append(item)
        
        if not subdirs:
            grid = IconGrid(self.icon_folder)
            grid.icon_selected.connect(self.icon_selected.emit)
            self.tab_widget.addTab(grid, "Icons")
            self._loaded_tabs["Icons"] = True
        else:
            for subdir in sorted(subdirs):
                placeholder = QLabel("Loading...")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tab_widget.addTab(placeholder, subdir)
    
    def _on_tab_changed(self, index: int):
        tab_name = self.tab_widget.tabText(index)
        
        if tab_name in self._loaded_tabs:
            return
        
        current_widget = self.tab_widget.widget(index)
        if isinstance(current_widget, QLabel):
            folder_path = os.path.join(self.icon_folder, tab_name)
            grid = IconGrid(folder_path)
            grid.icon_selected.connect(self.icon_selected.emit)
            self.tab_widget.removeTab(index)
            self.tab_widget.insertTab(index, grid, tab_name)
            self.tab_widget.setCurrentIndex(index)
            self._loaded_tabs[tab_name] = True
