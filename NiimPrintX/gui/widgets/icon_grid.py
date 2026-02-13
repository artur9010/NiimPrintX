import os
from typing import List, Dict, Optional
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QScrollArea, QLabel, QTabWidget, QApplication
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QThread, QUrl
from PyQt6.QtGui import QPixmap, QCursor, QImage, QColor, QPainter
from loguru import logger


_is_dark_theme_cache: Optional[bool] = None


def is_dark_theme() -> bool:
    global _is_dark_theme_cache
    
    if _is_dark_theme_cache is not None:
        return _is_dark_theme_cache
    
    app = QApplication.instance()
    if app is None:
        _is_dark_theme_cache = False
        return False
    
    palette = app.palette()
    bg_color = palette.color(palette.ColorRole.Window)
    
    bg_luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
    
    _is_dark_theme_cache = bg_luminance < 128
    logger.info(f"Theme detection: bg_luminance={bg_luminance:.3f}, is_dark={_is_dark_theme_cache}")
    return _is_dark_theme_cache


def reset_theme_cache():
    global _is_dark_theme_cache
    _is_dark_theme_cache = None
    logger.info("Theme cache reset")


def invert_pixmap(pixmap: QPixmap) -> QPixmap:
    image = pixmap.toImage()
    result = QImage(image.width(), image.height(), QImage.Format.Format_ARGB32)
    
    for y in range(image.height()):
        for x in range(image.width()):
            color = image.pixelColor(x, y)
            if color.alpha() > 0:
                inverted = QColor(
                    255 - color.red(),
                    255 - color.green(),
                    255 - color.blue(),
                    color.alpha()
                )
                result.setPixelColor(x, y, inverted)
            else:
                result.setPixelColor(x, y, color)
    
    return QPixmap.fromImage(result)


class IconLoaderThread(QThread):
    icons_loaded = pyqtSignal(list)
    
    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
    
    def run(self):
        icons = []
        logger.info(f"IconLoader: Scanning folder {self.folder_path}")
        
        if not os.path.isdir(self.folder_path):
            logger.warning(f"IconLoader: Folder does not exist: {self.folder_path}")
            self.icons_loaded.emit(icons)
            return
        
        subdirs = []
        files = []
        
        for item in os.listdir(self.folder_path):
            item_path = os.path.join(self.folder_path, item)
            if os.path.isdir(item_path):
                subdirs.append(item)
            elif os.path.isfile(item_path):
                files.append(item)
        
        logger.info(f"IconLoader: Found {len(subdirs)} subdirs and {len(files)} files in {self.folder_path}")
        
        if files:
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')):
                    icons.append(os.path.join(self.folder_path, file))
            logger.info(f"IconLoader: Found {len(icons)} icons directly in {self.folder_path}")
        else:
            size_folder = os.path.join(self.folder_path, "50x50")
            if os.path.isdir(size_folder):
                logger.info(f"IconLoader: Looking in size folder {size_folder}")
                for file in os.listdir(size_folder):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')):
                        icons.append(os.path.join(size_folder, file))
                logger.info(f"IconLoader: Found {len(icons)} icons in {size_folder}")
            else:
                logger.warning(f"IconLoader: No 50x50 folder found in {self.folder_path}")
        
        logger.info(f"IconLoader: Returning {len(icons)} icons from {self.folder_path}")
        self.icons_loaded.emit(icons)


class IconGridWidget(QLabel):
    clicked = pyqtSignal(str)
    
    def __init__(self, icon_path: str, size: int = 64, invert_for_dark: bool = False, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self._invert_for_dark = invert_for_dark
        self._original_pixmap: Optional[QPixmap] = None
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._load_icon()
    
    def _load_icon(self):
        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            self._original_pixmap = pixmap
            display_pixmap = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            if self._invert_for_dark and is_dark_theme():
                display_pixmap = invert_pixmap(display_pixmap)
            
            self.setPixmap(display_pixmap)
    
    def update_theme(self):
        if self._original_pixmap:
            display_pixmap = self._original_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            if self._invert_for_dark and is_dark_theme():
                display_pixmap = invert_pixmap(display_pixmap)
            
            self.setPixmap(display_pixmap)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.icon_path)


class IconGrid(QScrollArea):
    icon_selected = pyqtSignal(str)
    
    def __init__(self, folder_path: str = "", invert_for_dark: bool = True, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self._icons: List[str] = []
        self._icon_widgets: List[IconGridWidget] = []
        self._invert_for_dark = invert_for_dark
        self._icon_size = 48
        self._loader_thread: Optional[IconLoaderThread] = None
        
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
        self._icon_widgets.clear()
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _calculate_columns(self) -> int:
        available_width = self.viewport().width() - 10
        cols = max(1, available_width // (self._icon_size + 5))
        return cols
    
    def _populate_grid(self):
        self._clear_grid()
        
        cols = self._calculate_columns()
        logger.info(f"IconGrid: Populating grid with {len(self._icons)} icons in {cols} columns")
        
        for index, icon_path in enumerate(self._icons):
            row = index // cols
            col = index % cols
            
            icon_widget = IconGridWidget(icon_path, self._icon_size, self._invert_for_dark)
            icon_widget.clicked.connect(self._on_icon_clicked)
            self._icon_widgets.append(icon_widget)
            self._layout.addWidget(icon_widget, row, col)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._icons:
            self._populate_grid()
    
    def update_theme(self):
        for widget in self._icon_widgets:
            widget.update_theme()
    
    def _on_icon_clicked(self, icon_path: str):
        self.icon_selected.emit(icon_path)


class TabbedIconGrid(QWidget):
    icon_selected = pyqtSignal(str)
    
    def __init__(self, icon_folder: str, invert_for_dark: bool = True, parent=None):
        super().__init__(parent)
        self.icon_folder = icon_folder
        self._invert_for_dark = invert_for_dark
        self._loaded_tabs: Dict[str, IconGrid] = {}
        
        logger.info(f"TabbedIconGrid: Initializing with folder {icon_folder}")
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
            logger.warning(f"TabbedIconGrid: Icon folder not found: {self.icon_folder}")
            self.tab_widget.addTab(QLabel("No icons folder found"), "Empty")
            return
        
        logger.info(f"TabbedIconGrid: Loading tabs from {self.icon_folder}")
        
        subdirs = []
        for item in os.listdir(self.icon_folder):
            item_path = os.path.join(self.icon_folder, item)
            if os.path.isdir(item_path):
                subdirs.append(item)
        
        logger.info(f"TabbedIconGrid: Found {len(subdirs)} subdirs: {subdirs}")
        
        if not subdirs:
            grid = IconGrid(self.icon_folder, self._invert_for_dark)
            grid.icon_selected.connect(self.icon_selected.emit)
            self.tab_widget.addTab(grid, "Icons")
            self._loaded_tabs["Icons"] = grid
        else:
            for subdir in sorted(subdirs):
                placeholder = QLabel("Loading...")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tab_widget.addTab(placeholder, subdir)
                logger.info(f"TabbedIconGrid: Added tab '{subdir}'")
    
    def _on_tab_changed(self, index: int):
        tab_name = self.tab_widget.tabText(index)
        logger.info(f"TabbedIconGrid: Tab changed to '{tab_name}' (index {index})")
        
        if tab_name in self._loaded_tabs:
            logger.info(f"TabbedIconGrid: Tab '{tab_name}' already loaded")
            return
        
        current_widget = self.tab_widget.widget(index)
        if isinstance(current_widget, QLabel):
            folder_path = os.path.join(self.icon_folder, tab_name)
            logger.info(f"TabbedIconGrid: Loading icons from {folder_path}")
            grid = IconGrid(folder_path, self._invert_for_dark)
            grid.icon_selected.connect(self.icon_selected.emit)
            self.tab_widget.removeTab(index)
            self.tab_widget.insertTab(index, grid, tab_name)
            self.tab_widget.setCurrentIndex(index)
            self._loaded_tabs[tab_name] = grid
            logger.info(f"TabbedIconGrid: Loaded tab '{tab_name}'")
    
    def update_theme(self):
        logger.info("TabbedIconGrid: Updating theme for all loaded tabs")
        for tab_name, grid in self._loaded_tabs.items():
            if grid:
                grid.update_theme()
                logger.info(f"TabbedIconGrid: Updated theme for tab '{tab_name}'")
