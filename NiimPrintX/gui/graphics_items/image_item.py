import os
import base64
from typing import Optional, Dict, Any
from PyQt6.QtCore import Qt, QRectF, QByteArray, QBuffer
from PyQt6.QtGui import QPixmap, QImage, QColor

from ..models import AppConfig, ImageItem
from .base_item import BaseGraphicsItem


class ImageGraphicsItem(BaseGraphicsItem):
    def __init__(self, image_source, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self._image_path: str = ""
        self._image_data: Optional[bytes] = None
        self._pixmap: Optional[QPixmap] = None
        self._grayscale_pixmap: Optional[QPixmap] = None
        
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
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
        
        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                if color.alpha() > 0:
                    gray = int(0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue())
                    gray_color = QColor(gray, gray, gray, color.alpha())
                    image.setPixelColor(x, y, gray_color)
        
        return QPixmap.fromImage(image)
    
    def _apply_scale(self):
        if self._grayscale_pixmap and not self._grayscale_pixmap.isNull():
            scaled_size = self._grayscale_pixmap.size() * self._scale
            self._pixmap = self._grayscale_pixmap.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._bounding_rect = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
    
    def paint(self, painter, option, widget=None):
        if self._pixmap:
            painter.drawPixmap(0, 0, self._pixmap)
        
        self._draw_selection_hints(painter)
    
    def mouseMoveEvent(self, event):
        if self._is_resizing and self._grayscale_pixmap:
            delta = event.pos() - self._resize_start_pos
            factor = self._get_resize_factor(delta)
            
            new_scale = max(0.1, self._resize_start_scale + factor)
            
            if new_scale != self._scale:
                self._scale = new_scale
                self._apply_scale()
                self.update()
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
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
