import os
import base64
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPixmap, QImage, QPen, QColor, QBrush

from ..models import AppConfig, ImageItem


class ImageGraphicsItem(QGraphicsObject):
    def __init__(self, image_source, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self._image_path: str = ""
        self._image_data: Optional[bytes] = None
        self._pixmap: Optional[QPixmap] = None
        self._bounding_rect = QRectF()
        
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        if isinstance(image_source, str):
            self._image_path = image_source
            self._load_from_path(image_source)
        elif isinstance(image_source, ImageItem):
            if image_source.image_data:
                self._load_from_data(image_source.image_data)
            elif image_source.image_path:
                self._image_path = image_source.image_path
                self._load_from_path(image_source.image_path)
    
    def _load_from_path(self, path: str):
        if os.path.exists(path):
            self._pixmap = QPixmap(path)
            if not self._pixmap.isNull():
                self._bounding_rect = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
    
    def _load_from_data(self, data: bytes):
        image = QImage()
        if image.loadFromData(data):
            self._pixmap = QPixmap.fromImage(image)
            self._bounding_rect = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
    
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
    
    def get_image_data(self) -> ImageItem:
        item = ImageItem(
            image_path=self._image_path,
            x=self.pos().x(),
            y=self.pos().y(),
            width=self._bounding_rect.width(),
            height=self._bounding_rect.height()
        )
        if self._pixmap:
            buffer = QByteArray()
            buffer_device = QBuffer(buffer)
            buffer_device.open(QIODevice.OpenModeFlag.WriteOnly)
            self._pixmap.save(buffer_device, "PNG")
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
        }
        if self._pixmap:
            buffer = QByteArray()
            buffer_device = QBuffer(buffer)
            buffer_device.open(QIODevice.OpenModeFlag.WriteOnly)
            self._pixmap.save(buffer_device, "PNG")
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
        if 'image_data' in data:
            item.image_data = base64.b64decode(data['image_data'])
        return cls(item, app_config)


from PyQt6.QtCore import QByteArray, QBuffer
