"""Device information management for iPIXEL Color devices."""
from __future__ import annotations

import logging
import time
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Device type mapping (exact copy from go-ipxl/consts.go deviceTypeMap)
DEVICE_TYPE_MAP = {
    129: 2,  # -127 -> Type 2 (32x32)
    128: 0,  # -128 -> Type 0 (64x64)
    130: 4,  # -126 -> Type 4 (32x16)
    131: 3,  # -125 -> Type 3 (64x16)
    132: 1,  # -124 -> Type 1 (96x16)
    133: 5,  # -123 -> Type 5 (64x20)
    134: 6,  # -122 -> Type 6 (128x32)
    135: 7,  # -121 -> Type 7 (144x16)
    136: 8,  # -120 -> Type 8 (192x16)
    137: 9,  # -119 -> Type 9 (48x24)
    138: 10, # -118 -> Type 10 (64x32)
    139: 11, # -117 -> Type 11 (96x32)
    140: 12, # -116 -> Type 12 (128x32)
    141: 13, # -115 -> Type 13 (96x32)
    142: 14, # -114 -> Type 14 (160x32)
    143: 15, # -113 -> Type 15 (192x32)
    144: 16, # -112 -> Type 16 (256x32)
    145: 17, # -111 -> Type 17 (320x32)
    146: 18, # -110 -> Type 18 (384x32)
    147: 19, # -109 -> Type 19 (448x32)
}

# LED size mapping (exact copy from go-ipxl/consts.go ledSizeMap) 
LED_SIZE_MAP = {
    0:  [64, 64],  # Type 0
    1:  [96, 16],  # Type 1
    2:  [32, 32],  # Type 2
    3:  [64, 16],  # Type 3
    4:  [32, 16],  # Type 4
    5:  [64, 20],  # Type 5
    6:  [128, 32], # Type 6
    7:  [144, 16], # Type 7
    8:  [192, 16], # Type 8
    9:  [48, 24],  # Type 9
    10: [64, 32],  # Type 10
    11: [96, 32],  # Type 11
    12: [128, 32], # Type 12
    13: [96, 32],  # Type 13
    14: [160, 32], # Type 14
    15: [192, 32], # Type 15
    16: [256, 32], # Type 16
    17: [320, 32], # Type 17
    18: [384, 32], # Type 18
    19: [448, 32], # Type 19
}


def build_device_info_command() -> bytes:
    """Build device info query command.
    
    Format: [8, 0, 1, 128, hour, minute, second, language]
    From go-ipxl device_info.go
    """
    now = time.localtime()
    return bytes([
        8,              # Command header
        0,              # Reserved 
        1,              # Sub-command
        128,            # 0x80 (corresponds to -128 in signed byte)
        now.tm_hour,    # Current hour
        now.tm_min,     # Current minute  
        now.tm_sec,     # Current second
        0               # Language (0 for default)
    ])


def parse_device_response(response: bytes) -> dict[str, Any]:
    """Parse device info response (from go-ipxl parseDeviceInfo)."""
    if len(response) < 5:
        raise Exception(f"Response too short: got {len(response)} bytes, need at least 5")
    
    _LOGGER.debug("Device response: %s", response.hex())
    _LOGGER.info("Raw device response bytes: %s", [hex(b) for b in response])
    
    # Device type from byte 4
    device_type_byte = response[4]
    _LOGGER.info("Device type byte: %d (0x%02x)", device_type_byte, device_type_byte)
    
    led_type = DEVICE_TYPE_MAP.get(device_type_byte, 0)
    width, height = LED_SIZE_MAP.get(led_type, [64, 64])
    
    device_info = {
        "width": width,
        "height": height,
        "device_type": f"Type {device_type_byte}",
    }
    
    # Parse version info if response is long enough
    if len(response) >= 8:
        # MCU Version (bytes 4-5)
        mcu_major = response[4]  
        mcu_minor = response[5]
        device_info["mcu_version"] = f"{mcu_major}.{mcu_minor:02d}"
        
        # WiFi Version (bytes 6-7)
        wifi_major = response[6]
        wifi_minor = response[7] 
        device_info["wifi_version"] = f"{wifi_major}.{wifi_minor:02d}"
    else:
        device_info["mcu_version"] = "Unknown"
        device_info["wifi_version"] = "Unknown"
        
    return device_info