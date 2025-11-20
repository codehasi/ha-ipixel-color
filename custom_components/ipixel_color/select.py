"""Select entity for iPIXEL Color font selection."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .api import iPIXELAPI
from .const import DOMAIN, CONF_ADDRESS, CONF_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the iPIXEL Color select entities."""
    address = entry.data[CONF_ADDRESS]
    name = entry.data[CONF_NAME]
    
    api = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        iPIXELFontSelect(api, entry, address, name),
    ])


class iPIXELFontSelect(SelectEntity):
    """Representation of an iPIXEL Color font selection."""

    def __init__(
        self, 
        api: iPIXELAPI, 
        entry: ConfigEntry, 
        address: str, 
        name: str
    ) -> None:
        """Initialize the font select."""
        self._api = api
        self._entry = entry
        self._address = address
        self._name = name
        self._attr_name = f"{name} Font"
        self._attr_unique_id = f"{address}_font_select"
        
        # Get available fonts from fonts/ folder
        self._attr_options = self._get_available_fonts()
        self._attr_current_option = "Default" if "Default" in self._attr_options else self._attr_options[0]
        
        # Device info for grouping in device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="iPIXEL",
            model="LED Matrix Display",
            sw_version="1.0",
        )

    def _get_available_fonts(self) -> list[str]:
        """Get list of available fonts from fonts/ folder."""
        fonts = ["Default"]  # Always include default option
        
        # Look for fonts in the fonts/ directory
        fonts_dir = Path(__file__).parent / "fonts"
        if fonts_dir.exists():
            for font_file in fonts_dir.glob("*.ttf"):
                fonts.append(font_file.name)
            for font_file in fonts_dir.glob("*.otf"):
                fonts.append(font_file.name)
        
        return sorted(fonts)

    @property
    def current_option(self) -> str | None:
        """Return the current selected font."""
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Select a font option."""
        if option in self._attr_options:
            self._attr_current_option = option
            _LOGGER.debug("Font changed to: %s", option)
            # Note: The actual font will be used when text is displayed
        else:
            _LOGGER.error("Invalid font option: %s", option)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True