# Bluetooth Connection Fixes

## Issues Fixed

### 1. Silent Logs Made Visible

**Files:** `NiimPrintX/ui/widget/PrinterOperation.py`, `NiimPrintX/nimmy/bluetooth.py`, `NiimPrintX/nimmy/printer.py`

- Replaced commented-out `debug(e)` calls with proper `logger.error()` with `exc_info=True`
- Added logging for device scanning (devices found, matching)
- Added logging for connection attempts, success, and failure
- Added logging for disconnect, write, and notification operations
- Added debug logs for connect/disconnect calls
- Added logging for characteristic discovery

### 2. UUID to Handle-Based GATT Operations

**Files:** `NiimPrintX/nimmy/printer.py`, `NiimPrintX/nimmy/bluetooth.py`

- Changed from UUID-based to handle-based GATT operations
- BlueZ was returning malformed UUIDs like `0000None00001000800000805f9b34fb`
- Added `hasattr(char_specifier, 'handle')` check to support both characteristic objects and raw handles
- Cached characteristic object (`self._characteristic`) to avoid repeated UUID lookups

### 3. Connection Failure Handling

**Files:** `NiimPrintX/nimmy/bluetooth.py`, `NiimPrintX/nimmy/printer.py`

- `connect()` now properly raises `BLEException` on failure instead of returning `False`
- Added connection timeout (10s default)
- Added workaround for Bleak BlueZ bug where `connect()` returns `False` but device is actually connected
- Added post-connect sleep and `is_connected` check as fallback

### 4. Race Condition - BLE Operations Mutex

**File:** `NiimPrintX/nimmy/printer.py`

- Added `asyncio.Lock()` (`self._ble_lock`) to serialize BLE operations
- Prevents `[org.bluez.Error.InProgress] Operation already in progress` errors
- Wrapped `send_command()`, `write_raw()`, and `write_no_notify()` with lock

### 5. Timeout Handler Notification Leak

**File:** `NiimPrintX/nimmy/printer.py`

- Fixed `send_command()` to properly call `stop_notification()` on timeout
- Previously left stale notification subscriptions active

### 6. Disconnect Error Handling

**Files:** `NiimPrintX/nimmy/printer.py`, `NiimPrintX/nimmy/bluetooth.py`

- Added try/except for `EOFError` during disconnect
- BlueZ D-Bus connection can be closed before disconnect completes
- Errors are logged as warnings instead of crashing

### 7. Service Discovery Error Handling

**File:** `NiimPrintX/nimmy/printer.py`

- Added try/except around `service.uuid` and `char.uuid` access
- Catches `ValueError` from malformed UUID parsing
- Continues discovery even when some characteristics have bad UUIDs

## Summary of Changes

| File | Changes |
|------|---------|
| `bluetooth.py` | Connection timeout, connect fallback check, disconnect error handling, handle-based GATT ops |
| `printer.py` | BLE mutex lock, cached characteristic, UUID error handling, proper exception on connect failure |
| `PrinterOperation.py` | Enabled error logging with stack traces |

## Known Remaining Issues

1. **BlueZ cached malformed UUIDs** - May need to remove device from bluetoothctl (`remove <mac>`) and rediscover
2. **No retry mechanism** - Transient BLE failures still cause immediate failure
3. **No reconnection logic** - Connection drops require manual reconnect
4. **No MTU negotiation** - Could improve transfer speed
