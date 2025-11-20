"""Bluetooth device discovery for iPIXEL Color devices."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakScanner
from bleak.exc import BleakError

from ..const import DEVICE_NAME_PREFIX

_LOGGER = logging.getLogger(__name__)


async def discover_ipixel_devices(timeout: int = 10) -> list[dict[str, Any]]:
    """Discover iPIXEL devices via Bluetooth scanning.
    
    Args:
        timeout: Scan duration in seconds
        
    Returns:
        List of discovered device information
    """
    _LOGGER.debug("Starting iPIXEL device discovery")
    devices = []

    def detection_callback(device, advertisement_data):
        """Handle device detection."""
        if device.name and device.name.startswith(DEVICE_NAME_PREFIX):
            device_info = {
                "address": device.address,
                "name": device.name,
                "rssi": advertisement_data.rssi,
            }
            devices.append(device_info)
            _LOGGER.debug("Found iPIXEL device: %s", device_info)

    try:
        scanner = BleakScanner(detection_callback)
        await scanner.start()
        await asyncio.sleep(timeout)
        await scanner.stop()
        
        _LOGGER.debug("Discovery completed, found %d devices", len(devices))
        return devices
        
    except BleakError as err:
        _LOGGER.error("Discovery failed: %s", err)
        return []