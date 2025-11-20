"""Text entity for iPIXEL Color."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .api import iPIXELAPI, iPIXELConnectionError
from .const import DOMAIN, CONF_ADDRESS, CONF_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the iPIXEL Color text input."""
    address = entry.data[CONF_ADDRESS]
    name = entry.data[CONF_NAME]
    
    api = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([iPIXELTextDisplay(hass, api, entry, address, name)])


class iPIXELTextDisplay(TextEntity):
    """Representation of an iPIXEL Color text display."""

    _attr_mode = TextMode.TEXT
    _attr_native_max = 500  # Maximum 500 characters per protocol

    def __init__(
        self, 
        hass: HomeAssistant,
        api: iPIXELAPI, 
        entry: ConfigEntry, 
        address: str, 
        name: str
    ) -> None:
        """Initialize the text display."""
        self.hass = hass
        self._api = api
        self._entry = entry
        self._address = address
        self._name = name
        self._attr_name = f"{name} Display"
        self._attr_unique_id = f"{address}_text_display"
        self._current_text = ""
        self._available = True
        
        # Store current settings (could be exposed as additional entities later)
        self._effect = "scroll_ltr"  # Default to left-to-right scrolling
        self._speed = 50
        self._color_fg = (255, 255, 255)  # White text
        self._color_bg = (0, 0, 0)  # Black background

        # Device info for grouping in device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="iPIXEL",
            model="LED Matrix Display",
            sw_version="1.0",
        )

    @property
    def native_value(self) -> str | None:
        """Return the current text value."""
        return self._current_text

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Always return True to allow reconnection attempts
        # The actual connection state will be handled in the async_set_value method
        return True

    async def async_set_value(self, value: str) -> None:
        """Set the text to display."""
        try:
            if not self._api.is_connected:
                _LOGGER.debug("Reconnecting to device before displaying text")
                await self._api.connect()
            
            # Get font settings from other entities
            font_name = await self._get_font_setting()
            font_size = await self._get_font_size_setting()
            antialias = await self._get_antialiasing_setting()
            
            # Send text to display with settings
            success = await self._api.display_text(value, antialias, font_size, font_name)
            
            if success:
                self._current_text = value
                _LOGGER.debug("Successfully displayed text: %s (font: %s, size: %s, antialias: %s)", 
                            value, font_name or "Default", font_size or "Auto", antialias)
            else:
                _LOGGER.error("Failed to display text on iPIXEL")
                
        except iPIXELConnectionError as err:
            _LOGGER.error("Connection error while displaying text: %s", err)
            # Don't set unavailable to allow retry
        except Exception as err:
            _LOGGER.error("Unexpected error while displaying text: %s", err)

    async def _get_font_setting(self) -> str | None:
        """Get the current font setting from the font select entity."""
        try:
            # Get the font select entity
            entity_id = f"select.{self._name.lower().replace(' ', '_')}_font"
            state = self.hass.states.get(entity_id)
            if state and state.state != "Default":
                return state.state
        except Exception as err:
            _LOGGER.debug("Could not get font setting: %s", err)
        return None

    async def _get_font_size_setting(self) -> int | None:
        """Get the current font size setting from the number entity."""
        try:
            # Get the font size number entity
            entity_id = f"number.{self._name.lower().replace(' ', '_')}_font_size"
            state = self.hass.states.get(entity_id)
            if state and state.state not in ("unknown", "unavailable", ""):
                return int(float(state.state))
        except Exception as err:
            _LOGGER.debug("Could not get font size setting: %s", err)
        return None

    async def _get_antialiasing_setting(self) -> bool:
        """Get the current antialiasing setting from the switch entity."""
        try:
            # Get the antialiasing switch entity
            entity_id = f"switch.{self._name.lower().replace(' ', '_')}_antialiasing"
            state = self.hass.states.get(entity_id)
            if state:
                return state.state == "on"
        except Exception as err:
            _LOGGER.debug("Could not get antialiasing setting: %s", err)
        return True  # Default to antialiasing enabled

    async def async_update(self) -> None:
        """Update the entity state."""
        try:
            # Check connection status
            if self._api.is_connected:
                self._available = True
            else:
                self._available = False
                _LOGGER.debug("Device not connected, marking as unavailable")
                
        except Exception as err:
            _LOGGER.error("Error updating entity state: %s", err)
            self._available = False