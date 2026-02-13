import asyncio
from bleak import BleakClient, BleakScanner

from .exception import BLEException
from .logger_config import get_logger

logger = get_logger()


async def find_device(device_name_prefix=None):
    logger.info(f"Scanning for BLE devices with prefix '{device_name_prefix}'...")
    devices = await BleakScanner.discover()
    logger.debug(f"Found {len(devices)} BLE devices")
    for device in devices:
        logger.debug(f"  - {device.name} ({device.address})")
        if device.name and device.name.lower().startswith(device_name_prefix.lower()):
            logger.info(f"Matched device: {device.name} at {device.address}")
            return device
    logger.error(f"Device '{device_name_prefix}' not found among {len(devices)} discovered devices")
    raise BLEException(f"Failed to find device {device_name_prefix}")


async def scan_devices(device_name=None):
    print("Scanning for devices...")
    devices = await BleakScanner.discover()
    for device in devices:
        if device_name:
            if device.name and device_name.lower() in device.name.lower():
                print(f"Found device: {device.name} at {device.address}")
                return device
        else:
            print(f"Found device: {device.name} at {device.address}")
    return None


class BLETransport:
    def __init__(self, address=None):
        self.address = address
        self.client = None

    async def __aenter__(self):
        # Automatically connect if address is provided during initialization
        if self.address:
            self.client = BleakClient(self.address)
            if await self.client.connect():
                logger.info(f"Connected to {self.address}")
                return self
            else:
                raise BLEException(f"Failed to connect to the BLE device at {self.address}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected.")

    async def connect(self, address, timeout=10):
        logger.debug(f"BLETransport.connect() called with address={address}")
        if self.client is None:
            logger.debug(f"Creating new BleakClient for {address}")
            self.client = BleakClient(address, timeout=timeout)
        if not self.client.is_connected:
            logger.info(f"Attempting to connect to {address}...")
            try:
                result = await asyncio.wait_for(self.client.connect(), timeout=timeout)
                if result or self.client.is_connected:
                    logger.info(f"Successfully connected to {address}")
                    return True
                else:
                    logger.warning(f"BleakClient.connect() returned False, but checking actual state...")
                    await asyncio.sleep(0.5)
                    if self.client.is_connected:
                        logger.info(f"Device is actually connected to {address}")
                        return True
                    raise BLEException(f"Failed to connect to {address}")
            except asyncio.TimeoutError:
                logger.error(f"Connection timeout for {address}")
                raise BLEException(f"Connection timeout for {address}")
            except Exception as e:
                logger.error(f"Failed to connect to {address}: {e}", exc_info=True)
                raise
        logger.debug(f"Client already connected to {address}")
        return True

    async def disconnect(self):
        if self.client and self.client.is_connected:
            logger.info(f"Disconnecting from {self.client.address}...")
            try:
                await self.client.disconnect()
                logger.info("Disconnected.")
            except EOFError:
                logger.warning("Disconnect failed with EOFError - connection likely already closed")
            except Exception as e:
                logger.warning(f"Disconnect error: {e}")

    async def write(self, data, char_specifier):
        if self.client and self.client.is_connected:
            if hasattr(char_specifier, 'handle'):
                handle = char_specifier.handle
            else:
                handle = char_specifier
            logger.trace(f"write_gatt_char: handle={handle}, len={len(data)}")
            await self.client.write_gatt_char(handle, data)
        else:
            logger.error("Write failed: BLE client is not connected")
            raise BLEException("BLE client is not connected.")

    async def start_notification(self, char_specifier, handler):
        if self.client and self.client.is_connected:
            if hasattr(char_specifier, 'handle'):
                handle = char_specifier.handle
            else:
                handle = char_specifier
            logger.trace(f"start_notify: handle={handle}")
            await self.client.start_notify(handle, handler)
        else:
            logger.error("start_notification failed: BLE client is not connected")
            raise BLEException("BLE client is not connected.")

    async def stop_notification(self, char_specifier):
        if self.client and self.client.is_connected:
            if hasattr(char_specifier, 'handle'):
                handle = char_specifier.handle
            else:
                handle = char_specifier
            logger.trace(f"stop_notify: handle={handle}")
            await self.client.stop_notify(handle)
        else:
            logger.error("stop_notification failed: BLE client is not connected")
            raise BLEException("BLE client is not connected.")
