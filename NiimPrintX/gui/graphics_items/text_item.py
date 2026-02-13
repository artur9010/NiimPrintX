from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QGraphicsObject, QGraphicsRectItem
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPixmap, QFont, QFontMetrics

from ..models import AppConfig, TextItem
from ..utils import ImageRenderer


class TextGraphicsItem(QGraphicsObject):
    item_changed = pyqtSignal()
    
    def __init__(self, text_item: TextItem, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self._text_item = text_item
        self._pixmap: Optional[QPixmap] = None
        self._bounding_rect = QRectF()
        
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        self._selection_box: Optional[QGraphicsRectItem] = None
        self._resize_handle: Optional[QGraphicsRectItem] = None
        self._is_resizing = False
        self._resize_start_pos = QPointF()
        self._resize_start_size = 0
        
        self._render_pixmap()
    
    def _render_pixmap(self):
        renderer = ImageRenderer()
        self._pixmap = renderer.render_text(self._text_item)
        
        if self._pixmap:
            self._bounding_rect = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
        else:
            fm = QFontMetrics(QFont(self._text_item.font_family, self._text_item.font_size))
            width = fm.horizontalAdvance(self._text_item.content) + 10
            height = fm.height() + 10
            self._bounding_rect = QRectF(0, 0, width, height)
        
        self.update()
    
    def boundingRect(self) -> QRectF:
        return self._bounding_rect
    
    def paint(self, painter, option, widget=None):
        if self._pixmap:
            painter.drawPixmap(0, 0, self._pixmap)
        
        if self.isSelected():
            pen = QPen(QColor(0, 120, 212), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self._bounding_rect)
            
            handle_size = 8
            handle_rect = QRectF(
                self._bounding_rect.right() - handle_size / 2,
                self._bounding_rect.bottom() - handle_size / 2,
                handle_size,
                handle_size
            )
            painter.setBrush(QBrush(QColor(0, 120, 212)))
            painter.drawRect(handle_rect)
    
    def itemChange(self, change, value):
        if change == QGraphicsObject.GraphicsItemChange.ItemSelectedChange:
            self.update()
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        if self.isSelected():
            handle_size = 8
            handle_rect = QRectF(
                self._bounding_rect.right() - handle_size,
                self._bounding_rect.bottom() - handle_size,
                handle_size * 2,
                handle_size * 2
            )
            
            if handle_rect.contains(event.pos()):
                self._is_resizing = True
                self._resize_start_pos = event.pos()
                self._resize_start_size = self._text_item.font_size
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self._is_resizing:
            dy = event.pos().y() - self._resize_start_pos.y()
            new_size = max(8, self._resize_start_size + int(dy / 5))
            
            if new_size != self._text_item.font_size:
                self._text_item.font_size = new_size
                self._render_pixmap()
                self.item_changed.emit()
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._is_resizing = False
        super().mouseReleaseEvent(event)
    
    def get_text_data(self) -> TextItem:
        self._text_item.x = self.pos().x()
        self._text_item.y = self.pos().y()
        self._text_item.width = self._bounding_rect.width()
        self._text_item.height = self._bounding_rect.height()
        return self._text_item
    
    def update_from_data(self, text_item: TextItem):
        self._text_item.content = text_item.content
        self._text_item.font_family = text_item.font_family
        self._text_item.font_size = text_item.font_size
        self._text_item.font_weight = text_item.font_weight
        self._text_item.font_slant = text_item.font_slant
        self._text_item.underline = text_item.underline
        self._text_item.kerning = text_item.kerning
        self._render_pixmap()
        self.item_changed.emit()
    
    def to_dict(self) -> Dict[str, Any]:
        data = self.get_text_data()
        return data.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], app_config: AppConfig) -> 'TextGraphicsItem':
        text_item = TextItem.from_dict(data)
        return cls(text_item, app_config)
