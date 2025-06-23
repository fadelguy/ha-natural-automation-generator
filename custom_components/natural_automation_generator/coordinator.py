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
    ANALYSIS_PROMPT_TEMPLATE,
    APPROVAL_ANALYSIS_PROMPT,
    CANCELLATION_RESPONSE_PROMPT,
    CLARIFICATION_PROMPT_TEMPLATE,
    CLARIFICATION_RESPONSE_ANALYSIS_PROMPT,
    CLARIFICATION_RESPONSE_JSON_SCHEMA,
    CONF_LLM_PROVIDER,
    ERROR_RESPONSE_PROMPT,
    GENERAL_RESPONSE_PROMPT,
    PREVIEW_PROMPT_TEMPLATE,
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
    SUCCESS_RESPONSE_PROMPT,
    SYSTEM_PROMPT_TEMPLATE,
    ANALYSIS_JSON_SCHEMA,
    INTENT_ANALYSIS_JSON_SCHEMA,
    ENTITY_ANALYSIS_PROMPT,
    ENTITY_ANALYSIS_JSON_SCHEMA,
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

    async def get_entities_summary(self) -> str:
        """Get a very compact summary of available entities to save tokens."""
        entity_registry = async_get_entity_registry(self.hass)
        area_registry = async_get_area_registry(self.hass)
        
        # Count entities by domain (only major domains)
        domain_counts = {}
        main_domains = {'light', 'switch', 'sensor', 'binary_sensor', 'cover', 'climate', 'media_player', 'camera', 'lock'}
        
        for entity in entity_registry.entities.values():
            if entity.disabled:
                continue
                
            state = self.hass.states.get(entity.entity_id)
            if state is None:
                continue
            
            # Count only main domains
            domain = entity.domain
            if domain in main_domains:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Build ultra-compact summary
        summary_parts = []
        
        # Domain counts (only if > 0)
        if domain_counts:
            domain_list = [f"{domain}({count})" for domain, count in sorted(domain_counts.items())]
            summary_parts.append(f"DOMAINS: {', '.join(domain_list)}")
        
        # Areas (just count)
        area_count = len(area_registry.areas)
        if area_count > 0:
            area_names = [area.id for area in area_registry.areas.values()][:5]  # Only first 5
            summary_parts.append(f"AREAS({area_count}): {', '.join(area_names)}")
        
        return "\n".join(summary_parts)

    async def build_system_prompt(self) -> str:
        """Build the complete system prompt with current entities and areas."""
        entities_info = await self.get_smart_entities_info()  # ✅ השתמש בגרסה החכמה
        areas_info = await self.get_areas_info()
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            entities=entities_info,
            areas=areas_info
        )

    async def analyze_request(self, user_request: str) -> dict[str, Any]:
        """Analyze user request to identify missing information and ambiguities."""
        try:
            entities_info = await self.get_smart_entities_info(user_request)  # ✅ השתמש בגרסה החכמה
            areas_info = await self.get_areas_info()
            
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                entities=entities_info,
                areas=areas_info,
                user_request=user_request
            )
            
            response = await self.provider.generate_response(prompt, ANALYSIS_JSON_SCHEMA)
            
            # Clean and parse JSON response
            try:
                clean_response = self._clean_json_response(response)
                analysis_result = json.loads(clean_response)
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
            prompt = CLARIFICATION_PROMPT_TEMPLATE.format(
                original_request=original_request,
                analysis_results=json.dumps(analysis_results, indent=2)
            )
            
            response = await self.provider.generate_response(prompt)
            
            _LOGGER.debug("Generated clarification for request: %s", original_request)
            return {
                "success": True,
                "question": response.strip()
            }
        except Exception as err:
            _LOGGER.error("Failed to generate clarification: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def generate_preview(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a preview of the automation to be created."""
        try:
            # Use smart entities list for preview
            original_request = context.get("original_request", "")
            entities_info = await self.get_smart_entities_info(original_request)  # ✅ השתמש בגרסה החכמה
            areas_info = await self.get_areas_info()
            
            prompt = PREVIEW_PROMPT_TEMPLATE.format(
                context=json.dumps(context, indent=2),
                entities=entities_info,
                areas=areas_info
            )
            
            response = await self.provider.generate_response(prompt)
            
            _LOGGER.debug("Generated preview for context: %s", context)
            return {
                "success": True,
                "preview": response.strip()
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
            
            response = await self.provider.generate_response(prompt, INTENT_ANALYSIS_JSON_SCHEMA)
            
            # Clean and parse JSON response
            try:
                clean_response = self._clean_json_response(response)
                intent_result = json.loads(clean_response)
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

    async def generate_general_response(self, user_request: str) -> dict[str, Any]:
        """Generate response for non-automation requests."""
        try:
            # Get smart entities list for general questions too
            entities_info = await self.get_smart_entities_info(user_request)  # ✅ השתמש בגרסה החכמה
            areas_info = await self.get_areas_info()
            
            prompt = GENERAL_RESPONSE_PROMPT.format(
                user_request=user_request,
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

    async def generate_success_response(self, automation_name: str, description: str, yaml_config: str) -> dict[str, Any]:
        """Generate success message for completed automation."""
        try:
            prompt = SUCCESS_RESPONSE_PROMPT.format(
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

    async def generate_cancellation_response(self) -> dict[str, Any]:
        """Generate cancellation message."""
        try:
            prompt = CANCELLATION_RESPONSE_PROMPT
            
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

    async def generate_error_response(self, error: str, context: str = "") -> dict[str, Any]:
        """Generate error message."""
        try:
            prompt = ERROR_RESPONSE_PROMPT.format(
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

    async def get_filtered_entities(self, domains: list[str] = None, areas: list[str] = None, limit_per_domain: int = 15) -> str:
        """Get entities filtered by domains and areas."""
        entity_registry = async_get_entity_registry(self.hass)
        entities_info = []
        
        for entity in entity_registry.entities.values():
            if entity.disabled:
                continue
                
            state = self.hass.states.get(entity.entity_id)
            if state is None:
                continue
            
            # Filter by domain if specified
            if domains and entity.domain not in domains:
                continue
                
            # Filter by area if specified
            if areas and entity.area_id not in areas:
                continue
            
            # Get entity info (compact format)
            entity_info = {
                "entity_id": entity.entity_id,
                "name": entity.name or state.attributes.get("friendly_name", entity.entity_id),
                "domain": entity.domain,
                "area": entity.area_id,
            }
            
            entities_info.append(entity_info)
        
        # Group by domain and format
        domain_groups = {}
        for entity in entities_info:
            domain = entity["domain"]
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(entity)
        
        formatted_entities = []
        for domain, entities in domain_groups.items():
            formatted_entities.append(f"\n{domain.upper()} ENTITIES:")
            for entity in entities[:limit_per_domain]:  # Limit per domain
                area_info = f" ({entity['area']})" if entity['area'] else ""
                formatted_entities.append(
                    f"  - {entity['entity_id']}: {entity['name']}{area_info}"
                )
            if len(entities) > limit_per_domain:
                formatted_entities.append(f"  ... and {len(entities) - limit_per_domain} more {domain} entities")
        
        return "\n".join(formatted_entities) if formatted_entities else "No matching entities found."

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

    async def analyze_clarification_response(self, original_request: str, clarification_question: str, user_response: str) -> dict[str, Any]:
        """Analyze user's response to a clarification question using LLM."""
        try:
            entities_info = await self.get_smart_entities_info()
            areas_info = await self.get_areas_info()
            
            prompt = CLARIFICATION_RESPONSE_ANALYSIS_PROMPT.format(
                entities=entities_info,
                areas=areas_info,
                original_request=original_request,
                clarification_question=clarification_question,
                user_response=user_response
            )
            
            response = await self.provider.generate_response(prompt, CLARIFICATION_RESPONSE_JSON_SCHEMA)
            
            # Clean and parse JSON response
            try:
                clean_response = self._clean_json_response(response)
                analysis_result = json.loads(clean_response)
                _LOGGER.debug("Clarification response analysis: %s", analysis_result)
                return {
                    "success": True,
                    "analysis": analysis_result
                }
            except json.JSONDecodeError as json_err:
                _LOGGER.error("Failed to parse clarification response JSON: %s", json_err)
                _LOGGER.error("Raw response: %s", response)
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {json_err}"
                }
        except Exception as err:
            _LOGGER.error("Failed to analyze clarification response: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def analyze_conversation_flow(self, user_message: str, conversation_history: str, context_info: dict, current_step: str) -> dict[str, Any]:
        """Analyze conversation flow and decide what to do next using LLM."""
        try:
            entities_info = await self.get_smart_entities_info()
            areas_info = await self.get_areas_info()
            
            # Use the simpler analysis prompt for now (we can enhance later)
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                entities=entities_info,
                areas=areas_info,
                user_request=f"Context: {context_info}\nHistory: {conversation_history}\nCurrent message: {user_message}"
            )
            
            response = await self.provider.generate_response(prompt, ANALYSIS_JSON_SCHEMA)
            
            # Clean and parse JSON response
            try:
                clean_response = self._clean_json_response(response)
                analysis_result = json.loads(clean_response)
                
                # Convert simple analysis to conversation flow format
                converted_result = {
                    "conversation_type": "automation" if analysis_result.get("is_automation_request", False) else "general",
                    "language": analysis_result.get("language", "en"),
                    "next_action": "ask_clarification" if analysis_result.get("needs_clarification", False) else "show_preview",
                    "user_intent": {
                        "wants_automation": analysis_result.get("is_automation_request", False),
                        "approval_response": "unclear",
                        "entity_selection": "",
                        "modification_request": ""
                    },
                    "response_needed": {
                        "type": "question" if analysis_result.get("needs_clarification", False) else "info",
                        "content": "",
                        "entities_to_mention": [],
                        "missing_info": analysis_result.get("missing_info", [])
                    },
                    "ready_to_proceed": not analysis_result.get("needs_clarification", False),
                    "automation_details": analysis_result.get("understood", {})
                }
                
                _LOGGER.debug("Conversation flow analysis: %s", converted_result)
                return {
                    "success": True,
                    "analysis": converted_result
                }
            except json.JSONDecodeError as json_err:
                _LOGGER.error("Failed to parse conversation flow JSON: %s", json_err)
                _LOGGER.error("Raw response: %s", response)
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {json_err}"
                }
        except Exception as err:
            _LOGGER.error("Failed to analyze conversation flow: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def analyze_request_with_history(self, user_request: str, conversation_history: str) -> dict[str, Any]:
        """Analyze user request with conversation history for better context understanding."""
        try:
            entities_info = await self.get_smart_entities_info(user_request)
            areas_info = await self.get_areas_info()
            
            # Enhanced prompt that includes conversation history
            prompt = f"""
You classify user requests with conversation context.

📦 Entities: {entities_info}
📍 Areas: {areas_info}
🗣 Current User Request: {user_request}
📋 Conversation History:
{conversation_history}

⚠️ CRITICAL: Use ONLY exact entity IDs from the entities list above.
🌐 ALWAYS respond in the same language as the user's request.

Analyze the current request in context of the conversation history. 
If this is a follow-up question or continuation, understand the full context.
If the user is referring to something mentioned earlier, include that context.

Return JSON:
{{
  "is_automation_request": true/false,
  "language": "he/en",
  "understood": {{
    "action": "turn_on",
    "entity_type": "light", 
    "area": "living_room",
    "time": "evening",
    "conditions": "",
    "context_from_history": "what was understood from previous messages"}},
  "missing_info": [],
  "ambiguous_entities": {{ "light": ["light.living1", "light.living2"] }},
  "needs_clarification": true/false
}}

Only return JSON.
"""
            
            response = await self.provider.generate_response(prompt, ANALYSIS_JSON_SCHEMA)
            
            # Clean and parse JSON response
            try:
                clean_response = self._clean_json_response(response)
                analysis_result = json.loads(clean_response)
                _LOGGER.debug("Analysis with history for '%s': %s", user_request, analysis_result)
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
            _LOGGER.error("Failed to analyze request with history: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def generate_general_response_with_history(self, user_request: str, conversation_history: str) -> dict[str, Any]:
        """Generate response for non-automation requests with conversation context."""
        try:
            entities_info = await self.get_smart_entities_info(user_request)
            areas_info = await self.get_areas_info()
            
            prompt = f"""
Answer the user's question with full conversation context.

🗣 Current Request: {user_request}
📋 Conversation History:
{conversation_history}
📦 Entities: {entities_info}
📍 Areas: {areas_info}

🌐 ALWAYS respond in the same language as the user's request.
Consider the full conversation context when answering.
If the user is asking a follow-up question, understand what they're referring to from the history.
Give a helpful, contextual answer - maximum 3-4 sentences.
Only provide entity/area lists if specifically asked.

Return helpful response only.
"""
            
            response = await self.provider.generate_response(prompt)
            
            _LOGGER.debug("Generated contextual response for: %s", user_request)
            return {
                "success": True,
                "response": response.strip()
            }
        except Exception as err:
            _LOGGER.error("Failed to generate contextual response: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

 