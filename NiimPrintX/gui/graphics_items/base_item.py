from typing import Optional
from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QCursor


class BaseGraphicsItem(QGraphicsObject):
    HANDLE_SIZE = 10
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bounding_rect = QRectF()
        self._scale = 1.0
        self._is_resizing = False
        self._resize_handle: Optional[str] = None
        self._resize_start_pos = QPointF()
        self._resize_start_scale = 1.0
        
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
    
    def _get_handle_rect(self, corner: str) -> QRectF:
        hs = self.HANDLE_SIZE
        if corner == 'br':
            return QRectF(
                self._bounding_rect.right() - hs / 2,
                self._bounding_rect.bottom() - hs / 2,
                hs, hs
            )
        if corner == 'bl':
            return QRectF(
                self._bounding_rect.left() - hs / 2,
                self._bounding_rect.bottom() - hs / 2,
                hs, hs
            )
        if corner == 'tr':
            return QRectF(
                self._bounding_rect.right() - hs / 2,
                self._bounding_rect.top() - hs / 2,
                hs, hs
            )
        if corner == 'tl':
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
    
    def _get_resize_factor(self, delta: QPointF) -> float:
        if self._resize_handle == 'br':
            return (delta.x() + delta.y()) / 100
        if self._resize_handle == 'tl':
            return -(delta.x() + delta.y()) / 100
        if self._resize_handle == 'tr':
            return (delta.x() - delta.y()) / 100
        if self._resize_handle == 'bl':
            return (-delta.x() + delta.y()) / 100
        return 0
    
    def boundingRect(self) -> QRectF:
        return self._bounding_rect.adjusted(-self.HANDLE_SIZE, -self.HANDLE_SIZE,
                                              self.HANDLE_SIZE, self.HANDLE_SIZE)
    
    def _draw_selection_hints(self, painter):
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
    
    def mouseReleaseEvent(self, event):
        self._is_resizing = False
        self._resize_handle = None
        super().mouseReleaseEvent(event)
