import os
import base64
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import Qt, QRectF, QPointF, QByteArray, QBuffer
from PyQt6.QtGui import QPixmap, QImage, QPen, QColor, QBrush, QCursor

from ..models import AppConfig, ImageItem


class ImageGraphicsItem(QGraphicsObject):
    HANDLE_SIZE = 10
    
    def __init__(self, image_source, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self._image_path: str = ""
        self._image_data: Optional[bytes] = None
        self._pixmap: Optional[QPixmap] = None
        self._grayscale_pixmap: Optional[QPixmap] = None
        self._bounding_rect = QRectF()
        self._scale = 1.0
        
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        self._is_resizing = False
        self._resize_handle = None
        self._resize_start_pos = QPointF()
        self._resize_start_scale = 1.0
        
        if isinstance(image_source, str):
            self._image_path = image_source
            self._load_from_path(image_source)
        elif isinstance(image_source, ImageItem):
            if image_source.image_data:
                self._load_from_data(image_source.image_data)
            elif image_source.image_path:
                self._image_path = image_source.image_path
                self._load_from_path(image_source.image_path)
            
            if image_source.data.get('scale'):
                self._scale = image_source.data['scale']
                self._apply_scale()
    
    def _load_from_path(self, path: str):
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._grayscale_pixmap = self._to_grayscale(pixmap)
                self._pixmap = self._grayscale_pixmap
                self._bounding_rect = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
    
    def _load_from_data(self, data: bytes):
        image = QImage()
        if image.loadFromData(data):
            pixmap = QPixmap.fromImage(image)
            self._grayscale_pixmap = self._to_grayscale(pixmap)
            self._pixmap = self._grayscale_pixmap
            self._bounding_rect = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
    
    def _to_grayscale(self, pixmap: QPixmap) -> QPixmap:
        image = pixmap.toImage()
        result = image.convertToFormat(QImage.Format.Format_Grayscale8)
        return QPixmap.fromImage(result.convertToFormat(QImage.Format.Format_ARGB32))
    
    def _apply_scale(self):
        if self._grayscale_pixmap and not self._grayscale_pixmap.isNull():
            scaled_size = self._grayscale_pixmap.size() * self._scale
            self._pixmap = self._grayscale_pixmap.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._bounding_rect = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
    
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
        if self._is_resizing and self._grayscale_pixmap:
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
            
            new_scale = max(0.1, self._resize_start_scale + factor)
            
            if new_scale != self._scale:
                self._scale = new_scale
                self._apply_scale()
                self.update()
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._is_resizing = False
        self._resize_handle = None
        super().mouseReleaseEvent(event)
    
    def get_image_data(self) -> ImageItem:
        item = ImageItem(
            image_path=self._image_path,
            x=self.pos().x(),
            y=self.pos().y(),
            width=self._bounding_rect.width(),
            height=self._bounding_rect.height()
        )
        item.data['scale'] = self._scale
        if self._grayscale_pixmap:
            buffer = QByteArray()
            buffer_device = QBuffer(buffer)
            buffer_device.open(QBuffer.OpenModeFlag.WriteOnly)
            self._grayscale_pixmap.save(buffer_device, "PNG")
            item.image_data = bytes(buffer.data())
        return item
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'item_type': 'image',
            'x': self.pos().x(),
            'y': self.pos().y(),
            'width': self._bounding_rect.width(),
            'height': self._bounding_rect.height(),
            'image_path': self._image_path,
            'data': {'scale': self._scale}
        }
        if self._grayscale_pixmap:
            buffer = QByteArray()
            buffer_device = QBuffer(buffer)
            buffer_device.open(QBuffer.OpenModeFlag.WriteOnly)
            self._grayscale_pixmap.save(buffer_device, "PNG")
            data['image_data'] = base64.b64encode(bytes(buffer.data())).decode('ascii')
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], app_config: AppConfig) -> 'ImageGraphicsItem':
        item = ImageItem(
            image_path=data.get('image_path', ''),
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 0),
            height=data.get('height', 0)
        )
        item.data = data.get('data', {})
        if 'image_data' in data:
            item.image_data = base64.b64decode(data['image_data'])
        return cls(item, app_config)
