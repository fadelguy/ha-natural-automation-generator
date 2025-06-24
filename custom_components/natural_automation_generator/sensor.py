"""Sensor platform for Natural Automation Generator."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NaturalAutomationGeneratorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: NaturalAutomationGeneratorCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([
        NaturalAutomationGeneratorSensor(coordinator, config_entry)
    ])


class NaturalAutomationGeneratorSensor(SensorEntity):
    """Sensor entity for Natural Automation Generator status."""

    def __init__(
        self,
        coordinator: NaturalAutomationGeneratorCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._config_entry = config_entry
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_status"
        self._attr_name = "Natural Automation Generator Status"
        self._attr_icon = "mdi:robot"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "Natural Automation Generator",
            "manufacturer": "Natural Automation Generator",
            "model": "Automation Generator",
            "sw_version": "2.3.0",
        }

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        try:
            provider = self._coordinator.provider
            return f"Ready ({provider.provider_name})"
        except Exception:
            return "Not Ready"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        try:
            provider = self._coordinator.provider
            return {
                "provider": provider.provider_name,
                "integration_status": "Active",
                "conversation_agent": "Available",
                "description": "Create Home Assistant automations using natural language through Voice Assistants"
            }
        except Exception as err:
            return {
                "provider": "Unknown",
                "integration_status": "Error",
                "error": str(err),
                "description": "Create Home Assistant automations using natural language through Voice Assistants"
            } 