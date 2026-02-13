from tkinter import messagebox

from NiimPrintX.nimmy.bluetooth import find_device
from NiimPrintX.nimmy.printer import PrinterClient
from NiimPrintX.nimmy.logger_config import get_logger

logger = get_logger()


class PrinterOperation:
    def __init__(self, config):
        self.config = config
        self.printer = None

    async def printer_connect(self, model):
        try:
            device = await find_device(model)
            self.printer = PrinterClient(device)
            if await self.printer.connect():
                self.config.printer_connected = True
                return True
        except Exception as e:
            logger.error(f"Failed to connect to printer {model}: {e}", exc_info=True)
            messagebox.showerror("Error", f"Cannot connect to printer {model}.")
            return False

    async def printer_disconnect(self):
        try:
            if self.config.printer_connected or self.printer:
                await self.printer.disconnect()
            self.config.printer_connected = False
            self.printer = None
            return True
        except Exception as e:
            self.config.printer_connected = False
            messagebox.showerror("Error", f"{str(e)}.")
            return False

    async def print(self, image, density, quantity):
        try:
            if not self.config.printer_connected or not self.printer:
                await self.printer_connect(self.config.device)

            await self.printer.print_image(image, density, quantity)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"{str(e)}.")
            return False

    async def heartbeat(self):
        try:
            if self.printer:
                hb = await self.printer.heartbeat()
                return True, hb
        except Exception as e:
            logger.warning(f"Heartbeat failed, printer disconnected: {e}")
            self.printer = None
            return False, {}
