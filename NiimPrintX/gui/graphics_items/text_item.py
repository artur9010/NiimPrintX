from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPixmap, QFont, QFontMetrics, QCursor

from ..models import AppConfig, TextItem
from ..utils import ImageRenderer


class TextGraphicsItem(QGraphicsObject):
    item_changed = pyqtSignal()
    HANDLE_SIZE = 10
    
    def __init__(self, text_item: TextItem, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self._text_item = text_item
        self._pixmap: Optional[QPixmap] = None
        self._bounding_rect = QRectF()
        self._original_pixmap: Optional[QPixmap] = None
        self._scale = 1.0
        
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        self._is_resizing = False
        self._resize_handle = None
        self._resize_start_pos = QPointF()
        self._resize_start_scale = 1.0
        
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
    
    def _get_handle_rect(self, corner: str) -> QRectF:
        hs = self.HANDLE_SIZE
        if corner == 'br':
            return QRectF(
                self._bounding_rect.right() - hs / 2,
                self._bounding_rect.bottom() - hs / 2,
                hs, hs
            )
        elif corner == 'bl':
            return QRectF(
                self._bounding_rect.left() - hs / 2,
                self._bounding_rect.bottom() - hs / 2,
                hs, hs
            )
        elif corner == 'tr':
            return QRectF(
                self._bounding_rect.right() - hs / 2,
                self._bounding_rect.top() - hs / 2,
                hs, hs
            )
        elif corner == 'tl':
            return QRectF(
                self._bounding_rect.left() - hs / 2,
                self._bounding_rect.top() - hs / 2,
                hs, hs
            )
        return QRectF()
    
    def _get_handle_at_pos(self, pos: QPointF) -> Optional[str]:
        for corner in ['br', 'bl', 'tr', 'tl']:
            if self._get_handle_rect(corner).contains(pos):
                return corner
        return None
    
    def boundingRect(self) -> QRectF:
        return self._bounding_rect.adjusted(-self.HANDLE_SIZE, -self.HANDLE_SIZE, 
                                              self.HANDLE_SIZE, self.HANDLE_SIZE)
    
    def paint(self, painter, option, widget=None):
        if self._pixmap:
            painter.drawPixmap(0, 0, self._pixmap)
        
        if self.isSelected():
            pen = QPen(QColor(0, 120, 212), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self._bounding_rect)
            
            painter.setBrush(QBrush(QColor(0, 120, 212)))
            for corner in ['br', 'bl', 'tr', 'tl']:
                painter.drawRect(self._get_handle_rect(corner))
    
    def itemChange(self, change, value):
        if change == QGraphicsObject.GraphicsItemChange.ItemSelectedChange:
            self.update()
        return super().itemChange(change, value)
    
    def hoverMoveEvent(self, event):
        handle = self._get_handle_at_pos(event.pos())
        if handle in ['br', 'tl']:
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif handle in ['bl', 'tr']:
            self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverMoveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isSelected():
            handle = self._get_handle_at_pos(event.pos())
            if handle:
                self._is_resizing = True
                self._resize_handle = handle
                self._resize_start_pos = event.pos()
                self._resize_start_scale = self._scale
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self._is_resizing and self._original_pixmap:
            delta = event.pos() - self._resize_start_pos
            
            if self._resize_handle == 'br':
                factor = (delta.x() + delta.y()) / 100
            elif self._resize_handle == 'tl':
                factor = -(delta.x() + delta.y()) / 100
            elif self._resize_handle == 'tr':
                factor = (delta.x() - delta.y()) / 100
            elif self._resize_handle == 'bl':
                factor = (-delta.x() + delta.y()) / 100
            else:
                factor = 0
            
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
    
    def mouseReleaseEvent(self, event):
        self._is_resizing = False
        self._resize_handle = None
        super().mouseReleaseEvent(event)
    
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
