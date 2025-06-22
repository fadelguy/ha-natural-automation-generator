"""Coordinator for Natural Automation Generator integration."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    ANALYSIS_PROMPT_TEMPLATE,
    APPROVAL_ANALYSIS_PROMPT,
    CANCELLATION_RESPONSE_PROMPT,
    CLARIFICATION_PROMPT_TEMPLATE,
    CONF_LLM_PROVIDER,
    ERROR_RESPONSE_PROMPT,
    GENERAL_RESPONSE_PROMPT,
    PREVIEW_PROMPT_TEMPLATE,
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
    SUCCESS_RESPONSE_PROMPT,
    SYSTEM_PROMPT_TEMPLATE,
)
from .llm_providers.base import BaseLLMProvider
from .llm_providers.openai_provider import OpenAIProvider
# from .llm_providers.gemini_provider import GeminiProvider  # Disabled for now due to dependency issues

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
        # elif provider_type == PROVIDER_GEMINI:
        #     self._provider = GeminiProvider(self.hass, self.entry)  # Disabled for now
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}. Only OpenAI is currently supported.")
        
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

    async def analyze_request(self, user_request: str) -> dict[str, Any]:
        """Analyze user request to identify missing information and ambiguities."""
        try:
            entities_info = await self.get_entities_info()
            areas_info = await self.get_areas_info()
            
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                entities=entities_info,
                areas=areas_info,
                user_request=user_request
            )
            
            response = await self.provider.generate_response(prompt)
            
            # Parse JSON response
            try:
                analysis_result = json.loads(response)
                _LOGGER.debug("Analysis result for '%s': %s", user_request, analysis_result)
                return {
                    "success": True,
                    "analysis": analysis_result
                }
            except json.JSONDecodeError as json_err:
                _LOGGER.error("Failed to parse analysis JSON: %s", json_err)
                _LOGGER.error("Raw response: %s", response)
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {json_err}"
                }
        except Exception as err:
            _LOGGER.error("Failed to analyze request: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def generate_clarification(self, original_request: str, analysis_results: dict[str, Any]) -> dict[str, Any]:
        """Generate a clarifying question based on analysis results."""
        try:
            language = analysis_results.get("language", "en")
            
            prompt = CLARIFICATION_PROMPT_TEMPLATE.format(
                language=language,
                original_request=original_request,
                analysis_results=json.dumps(analysis_results, indent=2)
            )
            
            response = await self.provider.generate_response(prompt)
            
            _LOGGER.debug("Generated clarification for request: %s", original_request)
            return {
                "success": True,
                "question": response.strip(),
                "language": language
            }
        except Exception as err:
            _LOGGER.error("Failed to generate clarification: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def generate_preview(self, context: dict[str, Any], language: str = "en") -> dict[str, Any]:
        """Generate a preview of the automation to be created."""
        try:
            entities_info = await self.get_entities_info()
            areas_info = await self.get_areas_info()
            
            prompt = PREVIEW_PROMPT_TEMPLATE.format(
                language=language,
                context=json.dumps(context, indent=2),
                entities=entities_info,
                areas=areas_info
            )
            
            response = await self.provider.generate_response(prompt)
            
            _LOGGER.debug("Generated preview for context: %s", context)
            return {
                "success": True,
                "preview": response.strip(),
                "language": language
            }
        except Exception as err:
            _LOGGER.error("Failed to generate preview: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def analyze_user_intent(self, user_response: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze user's response to determine their intent (approve/reject/modify)."""
        try:
            prompt = APPROVAL_ANALYSIS_PROMPT.format(
                user_response=user_response,
                context=json.dumps(context, indent=2)
            )
            
            response = await self.provider.generate_response(prompt)
            
            # Parse JSON response
            try:
                intent_result = json.loads(response)
                _LOGGER.debug("Intent analysis for '%s': %s", user_response, intent_result)
                return {
                    "success": True,
                    "intent": intent_result
                }
            except json.JSONDecodeError as json_err:
                _LOGGER.error("Failed to parse intent JSON: %s", json_err)
                _LOGGER.error("Raw response: %s", response)
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {json_err}"
                }
        except Exception as err:
            _LOGGER.error("Failed to analyze user intent: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def generate_automation(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate automation configuration from collected context information."""
        try:
            system_prompt = await self.build_system_prompt()
            
            # Create a descriptive text from context for the LLM
            description_parts = []
            if "action" in context:
                description_parts.append(f"Action: {context['action']}")
            if "entity_id" in context:
                description_parts.append(f"Entity: {context['entity_id']}")
            if "time" in context:
                description_parts.append(f"Time: {context['time']}")
            if "conditions" in context:
                description_parts.append(f"Conditions: {context['conditions']}")
            
            description = "; ".join(description_parts)
            if "original_request" in context:
                description = f"{context['original_request']} ({description})"
            
            result = await self.provider.generate_automation(system_prompt, description)
            
            _LOGGER.debug("Generated automation from context: %s", context)
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
                "description": context.get("original_request", "Unknown request"),
            }

    async def generate_general_response(self, user_request: str, language: str = "en") -> dict[str, Any]:
        """Generate response for non-automation requests."""
        try:
            entities_info = await self.get_entities_info()
            areas_info = await self.get_areas_info()
            
            prompt = GENERAL_RESPONSE_PROMPT.format(
                user_request=user_request,
                language=language,
                entities=entities_info,
                areas=areas_info
            )
            
            response = await self.provider.generate_response(prompt)
            
            _LOGGER.debug("Generated general response for: %s", user_request)
            return {
                "success": True,
                "response": response.strip()
            }
        except Exception as err:
            _LOGGER.error("Failed to generate general response: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def generate_success_response(self, language: str, automation_name: str, description: str, yaml_config: str) -> dict[str, Any]:
        """Generate success message for completed automation."""
        try:
            prompt = SUCCESS_RESPONSE_PROMPT.format(
                language=language,
                automation_name=automation_name,
                description=description,
                yaml_config=yaml_config
            )
            
            response = await self.provider.generate_response(prompt)
            
            _LOGGER.debug("Generated success response for automation: %s", automation_name)
            return {
                "success": True,
                "response": response.strip()
            }
        except Exception as err:
            _LOGGER.error("Failed to generate success response: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def generate_cancellation_response(self, language: str) -> dict[str, Any]:
        """Generate cancellation message."""
        try:
            prompt = CANCELLATION_RESPONSE_PROMPT.format(language=language)
            
            response = await self.provider.generate_response(prompt)
            
            _LOGGER.debug("Generated cancellation response")
            return {
                "success": True,
                "response": response.strip()
            }
        except Exception as err:
            _LOGGER.error("Failed to generate cancellation response: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def generate_error_response(self, language: str, error: str, context: str = "") -> dict[str, Any]:
        """Generate error message."""
        try:
            prompt = ERROR_RESPONSE_PROMPT.format(
                language=language,
                error=error,
                context=context
            )
            
            response = await self.provider.generate_response(prompt)
            
            _LOGGER.debug("Generated error response")
            return {
                "success": True,
                "response": response.strip()
            }
        except Exception as err:
            _LOGGER.error("Failed to generate error response: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

 