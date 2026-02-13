from typing import Optional
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QByteArray, QBuffer

from ..models import TextItem


class ImageRenderer:
    def __init__(self):
        self.dpi = 300
    
    def render_text(self, text_item: TextItem) -> Optional[QPixmap]:
        try:
            from wand.image import Image as WandImage
            from wand.drawing import Drawing as WandDrawing
            from wand.color import Color
        except ImportError:
            return self._render_fallback(text_item)
        
        try:
            with WandDrawing() as draw:
                draw.font_family = text_item.font_family
                draw.font_size = text_item.font_size
                if text_item.font_slant == 'italic':
                    draw.font_style = 'italic'
                if text_item.font_weight == 'bold':
                    draw.font_weight = 700
                if text_item.underline:
                    draw.text_decoration = 'underline'
                draw.text_kerning = text_item.kerning
                draw.fill_color = Color('black')
                draw.resolution = (self.dpi, self.dpi)
                
                metrics = draw.get_font_metrics(
                    WandImage(width=1, height=1),
                    text_item.content,
                    multiline=False
                )
                text_width = int(metrics.text_width) + 10
                text_height = int(metrics.text_height) + 10
                
                with WandImage(width=text_width, height=text_height, background=Color('transparent')) as img:
                    draw.text(x=2, y=int(text_height / 2 + metrics.ascender / 2), body=text_item.content)
                    draw(img)
                    img.format = 'png'
                    img.alpha_channel = 'activate'
                    img_blob = img.make_blob('png32')
                    
                    q_image = QImage()
                    if q_image.loadFromData(QByteArray(img_blob)):
                        return QPixmap.fromImage(q_image)
        except Exception:
            pass
        
        return self._render_fallback(text_item)
    
    def _render_fallback(self, text_item: TextItem) -> Optional[QPixmap]:
        from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QColor
        
        font = QFont(text_item.font_family, text_item.font_size)
        font.setBold(text_item.font_weight == 'bold')
        font.setItalic(text_item.font_slant == 'italic')
        font.setUnderline(text_item.underline)
        
        fm = QFontMetrics(font)
        width = fm.horizontalAdvance(text_item.content) + 10
        height = fm.height() + 10
        
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(font)
        painter.setPen(QColor('black'))
        painter.drawText(5, fm.ascent() + 5, text_item.content)
        painter.end()
        
        return pixmap

from PyQt6.QtCore import Qt
