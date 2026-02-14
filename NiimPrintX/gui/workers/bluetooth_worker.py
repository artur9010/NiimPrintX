import asyncio
import threading
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from ..models.printer_state import DiscoveredDevice
from ..services import NiimbotCloudService, CloudLabelInfo


class BluetoothWorker(QObject):
    devices_found = pyqtSignal(list)
    connected = pyqtSignal(object)
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    rfid_detected = pyqtSignal(dict)
    cloud_label_detected = pyqtSignal(object)
    print_progress = pyqtSignal(int)
    print_finished = pyqtSignal(bool)
    print_error = pyqtSignal(str)
    
    _shared_loop: Optional[asyncio.AbstractEventLoop] = None
    _loop_thread: Optional[threading.Thread] = None
    _printer_client = None
    _connected_device: Optional[DiscoveredDevice] = None
    _rfid_info: Optional[Dict[str, Any]] = None
    _cloud_label_info: Optional[CloudLabelInfo] = None
    _cloud_service: Optional[NiimbotCloudService] = None
    
    def __init__(self):
        super().__init__()
        self._ensure_loop_running()
        self._cloud_service = NiimbotCloudService()
    
    def _ensure_loop_running(self):
        if BluetoothWorker._shared_loop is None or not BluetoothWorker._shared_loop.is_running():
            BluetoothWorker._shared_loop = asyncio.new_event_loop()
            BluetoothWorker._loop_thread = threading.Thread(
                target=self._run_loop,
                daemon=True
            )
            BluetoothWorker._loop_thread.start()
            import time
            time.sleep(0.1)
    
    def _run_loop(self):
        asyncio.set_event_loop(BluetoothWorker._shared_loop)
        BluetoothWorker._shared_loop.run_forever()
    
    def _run_async(self, coro, on_success=None, on_error=None):
        def done_callback(future):
            try:
                result = future.result()
                if on_success:
                    on_success(result)
            except (RuntimeError, OSError, IOError, asyncio.TimeoutError) as e:
                if on_error:
                    on_error(str(e))
        
        future = asyncio.run_coroutine_threadsafe(coro, BluetoothWorker._shared_loop)
        future.add_done_callback(done_callback)
        return future
    
    def connect_by_model(self, model: str):
        def on_success(_):
            self._query_rfid()
            if BluetoothWorker._connected_device:
                self.connected.emit(BluetoothWorker._connected_device)
        
        def on_error(msg):
            self.error.emit(f"Connection failed: {msg}")
        
        self._run_async(
            self._connect_printer_by_model(model),
            on_success=on_success,
            on_error=on_error
        )
    
    async def _connect_printer_by_model(self, model: str):
        from NiimPrintX.nimmy.bluetooth import find_device
        from NiimPrintX.nimmy.printer import PrinterClient
        
        device = await find_device(model)
        BluetoothWorker._printer_client = PrinterClient(device)
        await BluetoothWorker._printer_client.connect()
        
        BluetoothWorker._connected_device = DiscoveredDevice(
            address=device.address,
            name=device.name or model.upper(),
            rssi=getattr(device, 'rssi', 0)
        )
    
    def _query_rfid(self):
        def on_success(rfid_info):
            if rfid_info:
                from loguru import logger
                logger.info(f"RFID detected: {rfid_info}")
                BluetoothWorker._rfid_info = rfid_info
                self.rfid_detected.emit(rfid_info)
                
                barcode = rfid_info.get('barcode', '')
                if barcode:
                    self._query_cloud_label(barcode)
        
        def on_error(msg):
            from loguru import logger
            logger.warning(f"Failed to query RFID: {msg}")
        
        if BluetoothWorker._printer_client:
            self._run_async(
                self._get_rfid(),
                on_success=on_success,
                on_error=on_error
            )
    
    async def _get_rfid(self):
        if BluetoothWorker._printer_client:
            return await BluetoothWorker._printer_client.get_rfid()
        return None
    
    def _query_cloud_label(self, barcode: str):
        def on_success(label_info):
            if label_info:
                from loguru import logger
                logger.info(f"Cloud label: {label_info.width_mm}x{label_info.height_mm}mm - {label_info.name_en}")
                BluetoothWorker._cloud_label_info = label_info
                self.cloud_label_detected.emit(label_info)
        
        def on_error(msg):
            from loguru import logger
            logger.warning(f"Failed to query cloud label: {msg}")
        
        if self._cloud_service:
            self._run_async(
                self._cloud_service.get_label_by_barcode(barcode),
                on_success=on_success,
                on_error=on_error
            )
    
    def disconnect(self):
        def on_success(_):
            self.disconnected.emit()
        
        def on_error(msg):
            self.error.emit(f"Disconnect failed: {msg}")
        
        if BluetoothWorker._printer_client:
            self._run_async(
                self._disconnect_printer(),
                on_success=on_success,
                on_error=on_error
            )
        else:
            self.disconnected.emit()
    
    async def _disconnect_printer(self):
        if BluetoothWorker._printer_client and hasattr(BluetoothWorker._printer_client, 'disconnect'):
            await BluetoothWorker._printer_client.disconnect()
        BluetoothWorker._printer_client = None
        BluetoothWorker._connected_device = None
        BluetoothWorker._rfid_info = None
        BluetoothWorker._cloud_label_info = None
    
    def print_image(self, pil_image, density: int, quantity: int, device: str = ""):
        def on_success(_):
            self.print_finished.emit(True)
        
        def on_error(msg):
            self.print_error.emit(f"Print failed: {msg}")
        
        self._run_async(
            self._print_images(pil_image, density, quantity, device),
            on_success=on_success,
            on_error=on_error
        )
    
    async def _print_images(self, pil_image, density: int, quantity: int, device: str = ""):
        from loguru import logger
        
        if BluetoothWorker._printer_client is None:
            raise RuntimeError("Printer not connected")
        
        logger.info(f"Print image dimensions: width={pil_image.width}, height={pil_image.height}")
        logger.info(f"Device: {device}")
        
        # Use V2 print method for B1 printer
        if device and device.lower() == 'b1':
            logger.info("Using print_imageV2 for B1")
            await BluetoothWorker._printer_client.print_imageV2(pil_image, density=density, quantity=quantity)
            self.print_progress.emit(quantity)
        else:
            for i in range(quantity):
                await BluetoothWorker._printer_client.print_image(pil_image, density=density)
                self.print_progress.emit(i + 1)
    
    def get_printer_client(self):
        return BluetoothWorker._printer_client
    
    def get_connected_device(self):
        return BluetoothWorker._connected_device
    
    def get_rfid_info(self):
        return BluetoothWorker._rfid_info
    
    def get_cloud_label_info(self):
        return BluetoothWorker._cloud_label_info
    
    @classmethod
    def is_connected(cls):
        return cls._printer_client is not None
