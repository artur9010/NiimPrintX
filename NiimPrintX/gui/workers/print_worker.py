import asyncio
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from ..models import AppConfig


class PrintWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)
    
    def __init__(self, canvas, app_config: AppConfig, quantity: int, density: int):
        super().__init__()
        self.canvas = canvas
        self.app_config = app_config
        self.quantity = quantity
        self.density = density
        self._cancelled = False
    
    def run(self):
        try:
            image = self.canvas.get_print_image()
            if image is None:
                self.error.emit("No image to print")
                return
            
            printer_client = self.app_config.printer_client
            if printer_client is None:
                self.error.emit("Printer not connected")
                return
            
            buffer = self._image_to_buffer(image)
            
            for i in range(self.quantity):
                if self._cancelled:
                    self.finished.emit(False)
                    return
                
                try:
                    asyncio.run(self._print_one(printer_client, buffer))
                except RuntimeError as e:
                    if "asyncio.run() cannot be called from a running event loop" in str(e):
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(self._print_one(printer_client, buffer))
                    else:
                        raise
                except Exception as e:
                    self.error.emit(f"Print error: {str(e)}")
                    return
                
                self.progress.emit(i + 1)
            
            self.finished.emit(True)
            
        except Exception as e:
            self.error.emit(f"Print failed: {str(e)}")
    
    async def _print_one(self, printer_client, buffer):
        await printer_client.print_image(buffer, density=self.density)
    
    def _image_to_buffer(self, image):
        from PyQt6.QtCore import QByteArray, QBuffer
        from PyQt6.QtGui import QImage
        
        if isinstance(image, QImage):
            buffer = QByteArray()
            buffer_device = QBuffer(buffer)
            buffer_device.open(QBuffer.OpenModeFlag.WriteOnly)
            image.save(buffer_device, "PNG")
            return bytes(buffer.data())
        return image
    
    def cancel(self):
        self._cancelled = True
