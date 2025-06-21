"""Coordinator for Natural Automation Generator integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    CONF_LLM_PROVIDER,
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
    SYSTEM_PROMPT_TEMPLATE,
)
from .llm_providers.base import BaseLLMProvider
from .llm_providers.gemini_provider import GeminiProvider
from .llm_providers.openai_provider import OpenAIProvider

_LOGGER = logging.getLogger(__name__)


class NaturalAutomationGeneratorCoordinator:
    """Coordinator for managing LLM providers and entity discovery."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self._provider: BaseLLMProvider | None = None
        self._setup_provider()

    def _setup_provider(self) -> None:
        """Set up the LLM provider based on configuration."""
        provider_type = self.entry.data[CONF_LLM_PROVIDER]
        
        if provider_type == PROVIDER_OPENAI:
            self._provider = OpenAIProvider(self.hass, self.entry)
        elif provider_type == PROVIDER_GEMINI:
            self._provider = GeminiProvider(self.hass, self.entry)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        _LOGGER.debug("Set up LLM provider: %s", provider_type)

    @property
    def provider(self) -> BaseLLMProvider:
        """Get the current LLM provider."""
        if self._provider is None:
            raise RuntimeError("LLM provider not initialized")
        return self._provider

    async def get_entities_info(self) -> str:
        """Get formatted information about all entities."""
        entity_registry = async_get_entity_registry(self.hass)
        entities_info = []
        
        for entity in entity_registry.entities.values():
            if entity.disabled:
                continue
                
            state = self.hass.states.get(entity.entity_id)
            if state is None:
                continue
            
            # Get entity info
            entity_info = {
                "entity_id": entity.entity_id,
                "name": entity.name or state.attributes.get("friendly_name", entity.entity_id),
                "domain": entity.domain,
                "state": state.state,
                "area": entity.area_id,
            }
            
            # Add device class if available
            if device_class := state.attributes.get("device_class"):
                entity_info["device_class"] = device_class
            
            entities_info.append(entity_info)
        
        # Format entities by domain
        domains = {}
        for entity in entities_info:
            domain = entity["domain"]
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(entity)
        
        formatted_entities = []
        for domain, entities in domains.items():
            formatted_entities.append(f"\n{domain.upper()} ENTITIES:")
            for entity in entities[:20]:  # Limit to prevent token overflow
                area_info = f" (Area: {entity['area']})" if entity['area'] else ""
                state_info = f" [State: {entity['state']}]"
                formatted_entities.append(
                    f"  - {entity['entity_id']}: {entity['name']}{area_info}{state_info}"
                )
            if len(entities) > 20:
                formatted_entities.append(f"  ... and {len(entities) - 20} more {domain} entities")
        
        return "\n".join(formatted_entities)

    async def get_areas_info(self) -> str:
        """Get formatted information about all areas."""
        area_registry = async_get_area_registry(self.hass)
        areas_info = []
        
        for area in area_registry.areas.values():
            areas_info.append(f"  - {area.id}: {area.name}")
        
        if not areas_info:
            return "No areas configured."
        
        return "AREAS:\n" + "\n".join(areas_info)

    async def build_system_prompt(self) -> str:
        """Build the complete system prompt with current entities and areas."""
        entities_info = await self.get_entities_info()
        areas_info = await self.get_areas_info()
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            entities=entities_info,
            areas=areas_info
        )

    async def generate_automation(self, description: str) -> dict[str, Any]:
        """Generate automation configuration from natural language description."""
        try:
            system_prompt = await self.build_system_prompt()
            result = await self.provider.generate_automation(system_prompt, description)
            
            _LOGGER.debug("Generated automation for description: %s", description)
            return {
                "success": True,
                "yaml_config": result,
                "description": description,
            }
        except Exception as err:
            _LOGGER.error("Failed to generate automation: %s", err)
            return {
                "success": False,
                "error": str(err),
                "description": description,
            }

    async def validate_automation_config(self, config: dict[str, Any]) -> bool:
        """Validate the generated automation configuration."""
        try:
            # Basic validation - check required fields
            required_fields = ["alias", "trigger", "action"]
            for field in required_fields:
                if field not in config:
                    _LOGGER.error("Missing required field: %s", field)
                    return False
            
            # Validate trigger structure
            if not isinstance(config["trigger"], list):
                config["trigger"] = [config["trigger"]]
            
            # Validate action structure
            if not isinstance(config["action"], list):
                config["action"] = [config["action"]]
            
            return True
        except Exception as err:
            _LOGGER.error("Automation validation failed: %s", err)
            return False 