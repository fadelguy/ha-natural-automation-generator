"""Coordinator for Natural Automation Generator integration."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    CONF_LLM_PROVIDER,
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
    UNIFIED_CONVERSATION_PROMPT,
    UNIFIED_CONVERSATION_JSON_SCHEMA,
)
from .llm_providers.base import BaseLLMProvider
from .llm_providers.openai_provider import OpenAIProvider
from .llm_providers.gemini_provider import GeminiProvider

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
            raise ValueError(f"Unsupported provider type: {provider_type}. Both OpenAI and Gemini are supported.")
        
        _LOGGER.debug("Set up LLM provider: %s", provider_type)

    @property
    def provider(self) -> BaseLLMProvider:
        """Get the current LLM provider."""
        if self._provider is None:
            raise RuntimeError("LLM provider not initialized")
        return self._provider

    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response, removing markdown formatting and fixing truncated JSON."""
        # Remove markdown code blocks
        clean = re.sub(r'```json\s*', '', response)
        clean = re.sub(r'```\s*$', '', clean)
        clean = clean.strip()
        
        # Try to fix truncated JSON
        if clean and not clean.endswith('}'):
            # Count open and close braces to try to balance
            open_braces = clean.count('{')
            close_braces = clean.count('}')
            missing_braces = open_braces - close_braces
            
            # Try to close incomplete string if needed
            if clean.endswith('"') and clean.count('"') % 2 == 1:
                # Odd number of quotes means unclosed string
                pass  # Leave as is, might be intentionally unclosed
            elif not clean.endswith('"') and '"' in clean[-50:]:
                # Looks like string was cut off
                last_quote_pos = clean.rfind('"')
                if last_quote_pos > -1:
                    # Find the previous quote to see if string is open
                    before_last = clean[:last_quote_pos].count('"') 
                    if before_last % 2 == 0:  # Even means string is open
                        clean += '"'
            
            # Add missing closing braces
            clean += '}' * missing_braces
            
            _LOGGER.debug("Fixed truncated JSON: %s", clean)
        
        return clean

    async def get_entities_info(self, max_entities_per_domain: int = None) -> str:
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
        total_entities = 0
        
        for domain, entities in domains.items():
            formatted_entities.append(f"\n{domain.upper()} ENTITIES:")
            
            # Use all entities if no limit specified
            entities_to_show = entities
            if max_entities_per_domain and len(entities) > max_entities_per_domain:
                entities_to_show = entities[:max_entities_per_domain]
                
            for entity in entities_to_show:
                area_info = f" (Area: {entity['area']})" if entity['area'] else ""
                formatted_entities.append(
                    f"  - {entity['entity_id']}: {entity['name']}{area_info}"
                )
                total_entities += 1
            
            # Show remaining count if truncated
            if max_entities_per_domain and len(entities) > max_entities_per_domain:
                remaining = len(entities) - max_entities_per_domain
                formatted_entities.append(f"  ... and {remaining} more {domain} entities")
        
        _LOGGER.debug(f"Returning {total_entities} entities to LLM")
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





    async def get_smart_entities_info(self, user_request: str = None) -> str:
        """Get entities intelligently - returns full list with fallback to limited if too large."""
        try:
            # Try to get full entities list
            full_entities = await self.get_entities_info()
            
            # Check if the result is too large (rough token estimation)
            # Approximate: 1 token ≈ 4 characters
            estimated_tokens = len(full_entities) / 4
            
            # If estimated tokens > 15000, use limited version (leaving room for other content)
            if estimated_tokens > 15000:
                _LOGGER.warning(f"Entities list too large ({estimated_tokens:.0f} tokens), limiting to 50 per domain")
                return await self.get_entities_info(max_entities_per_domain=50)
            
            return full_entities
                    
        except Exception as err:
            _LOGGER.error("Error in smart entity info: %s", err)
            # Last resort - return minimal info
            return "Entity information temporarily unavailable."

    async def handle_unified_conversation(self, user_message: str, conversation_history: str) -> dict[str, Any]:
        """Handle conversation with unified approach - single LLM call for everything."""
        try:
            entities_info = await self.get_entities_info()
            areas_info = await self.get_areas_info()
            
            prompt = UNIFIED_CONVERSATION_PROMPT.format(
                entities=entities_info,
                areas=areas_info,
                conversation_history=conversation_history,
                user_message=user_message
            )
            
            response = await self.provider.generate_response(prompt, UNIFIED_CONVERSATION_JSON_SCHEMA)
            
            # Clean and parse JSON response
            try:
                clean_response = self._clean_json_response(response)
                result = json.loads(clean_response)
                _LOGGER.debug("Unified conversation result: %s", result)
                return {
                    "success": True,
                    "result": result
                }
            except json.JSONDecodeError as json_err:
                _LOGGER.error("Failed to parse unified conversation JSON: %s", json_err)
                _LOGGER.error("Raw response: %s", response)
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {json_err}"
                }
        except Exception as err:
            _LOGGER.error("Failed to handle unified conversation: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

 