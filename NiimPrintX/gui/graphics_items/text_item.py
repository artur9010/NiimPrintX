from typing import Optional, Dict, Any
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics

from ..models import AppConfig, TextItem
from ..utils import ImageRenderer
from .base_item import BaseGraphicsItem


class TextGraphicsItem(BaseGraphicsItem):
    item_changed = pyqtSignal()
    def __init__(self, text_item: TextItem, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self._text_item = text_item
        self._pixmap: Optional[QPixmap] = None
        self._original_pixmap: Optional[QPixmap] = None
        
        self._render_pixmap()
    
    def _render_pixmap(self):
        renderer = ImageRenderer()
        self._pixmap = renderer.render_text(self._text_item)
        self._original_pixmap = self._pixmap
        
        if self._pixmap:
            self._bounding_rect = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
        else:
            fm = QFontMetrics(QFont(self._text_item.font_family, self._text_item.font_size))
            width = fm.horizontalAdvance(self._text_item.content) + 10
            height = fm.height() + 10
            self._bounding_rect = QRectF(0, 0, width, height)
        
        self.update()
    
    def paint(self, painter, option, widget=None):
        if self._pixmap:
            painter.drawPixmap(0, 0, self._pixmap)
        
        self._draw_selection_hints(painter)
    
    def mouseMoveEvent(self, event):
        if self._is_resizing and self._original_pixmap:
            delta = event.pos() - self._resize_start_pos
            factor = self._get_resize_factor(delta)
            
            new_scale = max(0.2, self._resize_start_scale + factor)
            
            if new_scale != self._scale:
                self._scale = new_scale
                scaled_size = self._original_pixmap.size() * new_scale
                self._pixmap = self._original_pixmap.scaled(
                    scaled_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._bounding_rect = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
                self.update()
                self.item_changed.emit()
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def get_text_data(self) -> TextItem:
        self._text_item.x = self.pos().x()
        self._text_item.y = self.pos().y()
        self._text_item.width = self._bounding_rect.width()
        self._text_item.height = self._bounding_rect.height()
        self._text_item.data['scale'] = self._scale
        return self._text_item
    
    def update_from_data(self, text_item: TextItem):
        self._text_item.content = text_item.content
        self._text_item.font_family = text_item.font_family
        self._text_item.font_size = text_item.font_size
        self._text_item.font_weight = text_item.font_weight
        self._text_item.font_slant = text_item.font_slant
        self._text_item.underline = text_item.underline
        self._text_item.kerning = text_item.kerning
        self._scale = text_item.data.get('scale', 1.0)
        self._render_pixmap()
        self.item_changed.emit()
    
    def to_dict(self) -> Dict[str, Any]:
        data = self.get_text_data()
        return data.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], app_config: AppConfig) -> 'TextGraphicsItem':
        text_item = TextItem.from_dict(data)
        item = cls(text_item, app_config)
        item._scale = data.get('data', {}).get('scale', 1.0)
        if item._scale != 1.0 and item._original_pixmap:
            scaled_size = item._original_pixmap.size() * item._scale
            item._pixmap = item._original_pixmap.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            item._bounding_rect = QRectF(0, 0, item._pixmap.width(), item._pixmap.height())
        return item
