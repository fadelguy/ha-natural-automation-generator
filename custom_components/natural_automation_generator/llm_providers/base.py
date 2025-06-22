"""Base LLM Provider for Natural Automation Generator."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the LLM provider."""
        self.hass = hass
        self.entry = entry
        self._client = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""

    @abstractmethod
    async def _initialize_client(self) -> None:
        """Initialize the LLM client."""

    @abstractmethod
    async def generate_automation(self, system_prompt: str, user_description: str) -> str:
        """Generate automation YAML from natural language description."""

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate a text response from the LLM."""

    async def _ensure_client_initialized(self) -> None:
        """Ensure the client is initialized."""
        if self._client is None:
            await self._initialize_client()

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value, checking both options and data."""
        # Check options first (user can change these)
        if key in self.entry.options:
            return self.entry.options[key]
        # Fall back to entry data
        return self.entry.data.get(key, default)

    async def test_connection(self) -> bool:
        """Test the connection to the LLM provider."""
        try:
            await self._ensure_client_initialized()
            # Perform a simple test request
            await self.generate_automation(
                "You are a Home Assistant automation generator.",
                "Test connection"
            )
            return True
        except Exception as err:
            _LOGGER.error("Connection test failed for %s: %s", self.provider_name, err)
            return False 