import pickle
import base64
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QColor, QPen, QBrush, QImage, QPainter

from ..models import AppConfig, TextItem, ImageItem
from ..graphics_items import TextGraphicsItem, ImageGraphicsItem


class LabelScene(QGraphicsScene):
    def __init__(self, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        
        self.label_box: Optional[QGraphicsRectItem] = None
        self.print_area_box: Optional[QGraphicsRectItem] = None
        self._label_width = 0
        self._label_height = 0
        self._print_width = 0
        self._print_height = 0
        
        self.setSceneRect(0, 0, 800, 600)
        self.setBackgroundBrush(QBrush(QColor(200, 200, 200)))
        
        self._create_label_boxes()
    
    def _create_label_boxes(self):
        width_mm, height_mm = self.app_config.get_label_size_mm()
        self._label_width = self.app_config.mm_to_pixels(width_mm)
        self._label_height = self.app_config.mm_to_pixels(height_mm)
        self._print_width = self._label_width - self.app_config.mm_to_pixels(2)
        self._print_height = self._label_height - self.app_config.mm_to_pixels(4)
        
        from loguru import logger
        logger.info(f"Label size: {width_mm}mm x {height_mm}mm -> {self._label_width}x{self._label_height} px")
        logger.info(f"Print area: {self._print_width}x{self._print_height} px")
        
        canvas_padding = 150
        scene_width = self._label_width + canvas_padding
        scene_height = self._label_height + canvas_padding
        self.setSceneRect(0, 0, scene_width, scene_height)
        
        center_x = scene_width / 2
        center_y = scene_height / 2
        
        if self.label_box:
            self.removeItem(self.label_box)
        if self.print_area_box:
            self.removeItem(self.print_area_box)
        
        label_rect = QRectF(
            center_x - self._label_width / 2,
            center_y - self._label_height / 2,
            self._label_width,
            self._label_height
        )
        self.label_box = self.addRect(
            label_rect,
            QPen(Qt.PenStyle.NoPen),
            QBrush(QColor(255, 255, 255))
        )
        self.label_box.setZValue(-100)
        self.label_box.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, False)
        
        self.print_area_box = None
    
    def update_label_size(self):
        self._create_label_boxes()
    
    def get_label_rect(self) -> QRectF:
        return self.label_box.rect() if self.label_box else QRectF()
    
    def get_print_rect(self) -> QRectF:
        return self.print_area_box.rect() if self.print_area_box else QRectF()
    
    def get_center(self) -> QPointF:
        return self.sceneRect().center()
    
    def get_all_items(self) -> List:
        items = []
        for item in self.items():
            if isinstance(item, (TextGraphicsItem, ImageGraphicsItem)):
                items.append(item)
        return items
    
    def clear_items(self):
        for item in self.get_all_items():
            self.removeItem(item)
    
    def to_dict(self) -> List[Dict[str, Any]]:
        items_data = []
        for item in self.get_all_items():
            items_data.append(item.to_dict())
        return items_data
    
    def from_dict(self, items_data):
        self.clear_items()
        
        if isinstance(items_data, list):
            self._load_new_format(items_data)
        elif isinstance(items_data, dict):
            self._load_old_format(items_data)
    
    def _load_new_format(self, items_data: List[Dict[str, Any]]):
        for item_data in items_data:
            item_type = item_data.get('item_type')
            if item_type == 'text':
                item = TextGraphicsItem.from_dict(item_data, self.app_config)
                item.setPos(item_data.get('x', 0), item_data.get('y', 0))
                self.addItem(item)
            elif item_type == 'image':
                item = ImageGraphicsItem.from_dict(item_data, self.app_config)
                item.setPos(item_data.get('x', 0), item_data.get('y', 0))
                self.addItem(item)
    
    def _load_old_format(self, data: Dict[str, Any]):
        import base64
        import io
        from PIL import Image
        
        label_rect = self.get_label_rect()
        offset_x = label_rect.left()
        offset_y = label_rect.top()
        
        if 'text' in data:
            for text_id, item_data in data['text'].items():
                coords = item_data.get('coords', [0, 0])
                font_props = item_data.get('font_props', {})
                
                text_item = TextItem(
                    content=item_data.get('content', ''),
                    font_family=font_props.get('family', 'Arial'),
                    font_size=font_props.get('size', 16),
                    font_weight='bold' if font_props.get('weight') == 'bold' else 'normal',
                    font_slant='italic' if font_props.get('slant') == 'italic' else 'roman',
                    underline=font_props.get('underline', False),
                    x=coords[0] if coords else 0,
                    y=coords[1] if len(coords) > 1 else 0
                )
                
                item = TextGraphicsItem(text_item, self.app_config)
                item.setPos(offset_x + coords[0] if coords else offset_x, 
                           offset_y + coords[1] if len(coords) > 1 else offset_y)
                self.addItem(item)
        
        if 'image' in data:
            for image_id, item_data in data['image'].items():
                coords = item_data.get('coords', [0, 0])
                
                image_data = item_data.get('original_image')
                if image_data:
                    img_bytes = base64.b64decode(image_data)
                    pil_image = Image.open(io.BytesIO(img_bytes))
                    
                    image_item = ImageItem(
                        x=coords[0] if coords else 0,
                        y=coords[1] if len(coords) > 1 else 0,
                        image_data=img_bytes
                    )
                    
                    item = ImageGraphicsItem(image_item, self.app_config)
                    item.setPos(offset_x + coords[0] if coords else offset_x,
                               offset_y + coords[1] if len(coords) > 1 else offset_y)
                    self.addItem(item)
    
    def render_to_image(self) -> QImage:
        label_box = self.label_box
        if label_box is None:
            return QImage()
        
        selected_items = self.selectedItems()
        for item in selected_items:
            item.setSelected(False)
        
        scene_rect = label_box.sceneBoundingRect()
        width = int(scene_rect.width())
        height = int(scene_rect.height())
        
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        target_rect = QRectF(0, 0, width, height)
        
        self.render(painter, target_rect, scene_rect)
        painter.end()
        
        for item in selected_items:
            item.setSelected(True)
        
        grayscale = image.convertToFormat(QImage.Format.Format_Grayscale8)
        return grayscale.convertToFormat(QImage.Format.Format_ARGB32)


class DesignCanvas(QGraphicsView):
    item_selected = pyqtSignal(object)
    selection_cleared = pyqtSignal()
    
    def __init__(self, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self._zoom = 1.0
        
        self.scene = LabelScene(app_config, self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self._connect_signals()
    
    def _connect_signals(self):
        self.app_config.label_size_changed.connect(self._on_label_size_changed)
        self.scene.selectionChanged.connect(self._on_selection_changed)
    
    def _on_label_size_changed(self, _):
        self.scene.update_label_size()
        self.centerOn(self.scene.get_center())
    
    def _on_selection_changed(self):
        selected = self.scene.selectedItems()
        if selected:
            for item in selected:
                if isinstance(item, (TextGraphicsItem, ImageGraphicsItem)):
                    self.item_selected.emit(item)
                    break
        else:
            self.selection_cleared.emit()
    
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.1 if delta > 0 else 0.9
            
            new_zoom = self._zoom * factor
            if 0.2 <= new_zoom <= 5.0:
                self._zoom = new_zoom
                self.scale(factor, factor)
        else:
            super().wheelEvent(event)
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
        elif event.key() == Qt.Key.Key_Escape:
            self.scene.clearSelection()
        else:
            super().keyPressEvent(event)
    
    def add_text_item(self, text_item) -> TextGraphicsItem:
        center = self.scene.get_center()
        item = TextGraphicsItem(text_item, self.app_config)
        item.setPos(center)
        self.scene.addItem(item)
        self.scene.clearSelection()
        item.setSelected(True)
        return item
    
    def add_image_item(self, image_path: str) -> ImageGraphicsItem:
        center = self.scene.get_center()
        item = ImageGraphicsItem(image_path, self.app_config)
        item.setPos(center)
        self.scene.addItem(item)
        self.scene.clearSelection()
        item.setSelected(True)
        return item
    
    def update_text_item(self, text_item):
        selected = self.scene.selectedItems()
        for item in selected:
            if isinstance(item, TextGraphicsItem):
                item.update_from_data(text_item)
                break
    
    def delete_selected(self):
        selected = self.scene.selectedItems()
        for item in selected:
            if isinstance(item, (TextGraphicsItem, ImageGraphicsItem)):
                self.scene.removeItem(item)
        self.selection_cleared.emit()
    
    def clear_all(self):
        self.scene.clear_items()
        self.selection_cleared.emit()
    
    def save_to_file(self, file_path: str):
        items_data = self.scene.to_dict()
        
        save_data = {
            'device': self.app_config.device,
            'label_size': self.app_config.current_label_size,
            'items': items_data
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(save_data, f)
    
    def load_from_file(self, file_path: str):
        with open(file_path, 'rb') as f:
            save_data = pickle.load(f)
        
        if 'device' in save_data:
            self.app_config.device = save_data['device']
        if 'label_size' in save_data:
            self.app_config.current_label_size = save_data['label_size']
        
        self.scene.update_label_size()
        
        if 'items' in save_data:
            self.scene.from_dict(save_data['items'])
        
        self.centerOn(self.scene.get_center())
    
    def export_to_png(self, file_path: str):
        image = self.scene.render_to_image()
        image.save(file_path, "PNG")
    
    def get_print_image(self) -> QImage:
        return self.scene.render_to_image()
