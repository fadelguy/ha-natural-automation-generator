"""Conversation entity for Natural Automation Generator integration."""
from __future__ import annotations

import logging
import uuid
import yaml
from dataclasses import dataclass, field
from typing import Any, Dict

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    NAME,
    VERSION,
)
from .coordinator import NaturalAutomationGeneratorCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for ongoing conversation."""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stored_automation_yaml: str = ""
    stored_automation_name: str = ""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entity."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([NaturalAutomationConversationEntity(hass, config_entry, coordinator)])


class NaturalAutomationConversationEntity(conversation.ConversationEntity):
    """Natural Automation Generator conversation entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: NaturalAutomationGeneratorCoordinator,
    ) -> None:
        """Initialize the conversation entity."""
        self.hass = hass
        self._config_entry = config_entry
        self._coordinator = coordinator
        self._attr_name = "Natural Automation Generator"
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}"
        self._attr_supported_features = conversation.ConversationEntityFeature.CONTROL
        # Store conversation contexts
        self._conversations: Dict[str, ConversationContext] = {}

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return ["*"]  # Support all languages

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": NAME,
            "manufacturer": "Natural Automation Generator",
            "model": "Automation Generator",
            "sw_version": VERSION,
        }

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Handle incoming user message with unified approach."""
        user_text = user_input.text.strip()
        
        _LOGGER.debug("Handling message: %s", user_text)

        # Get or create conversation context
        context = self._get_conversation_context(user_input.conversation_id)
        
        try:
            # Build conversation history
            conversation_history = self._build_conversation_history(chat_log)
            
            # Single unified LLM call
            result = await self._coordinator.handle_unified_conversation(user_text, conversation_history)
            
            if not result["success"]:
                return self._create_conversation_result(f"Error: {result.get('error', 'Unknown error')}")
            
            response_data = result["result"]
            
            # Handle automation YAML storage/replacement
            if response_data.get("automation_yaml"):
                if response_data.get("is_confirmed"):
                    # User confirmed - save the stored automation
                    if context.stored_automation_yaml:
                        try:
                            automation_config = yaml.safe_load(context.stored_automation_yaml)
                            await self._save_automation(automation_config)
                            
                            # Clear stored automation
                            context.stored_automation_yaml = ""
                            context.stored_automation_name = ""
                            
                        except Exception as err:
                            _LOGGER.error("Failed to save automation: %s", err)
                            return self._create_conversation_result(f"Error saving automation: {err}")
                    else:
                        return self._create_conversation_result("No automation found to save.")
                else:
                    # Store/replace the automation YAML for later confirmation
                    context.stored_automation_yaml = response_data["automation_yaml"]
                    context.stored_automation_name = response_data["automation_name"] or "Automation"
            
            return self._create_conversation_result(response_data["message"])
                
        except Exception as err:
            _LOGGER.error("Error handling message: %s", err)
            return self._create_conversation_result(f"Error: {str(err)}")

    def _get_conversation_context(self, conversation_id: str) -> ConversationContext:
        """Get existing or create new conversation context."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = ConversationContext(conversation_id=conversation_id)
        return self._conversations[conversation_id]

    def _build_conversation_history(self, chat_log: conversation.ChatLog) -> str:
        """Build a formatted conversation history from chat log."""
        history_parts = []
        
        for content in chat_log.content:
            if hasattr(content, 'content') and content.content:
                # Determine if it's user or assistant message
                if hasattr(content, 'agent_id') and content.agent_id:
                    # Assistant message
                    history_parts.append(f"Assistant: {content.content}")
                else:
                    # User message
                    history_parts.append(f"User: {content.content}")
        
        return "\n".join(history_parts) if history_parts else "No previous conversation"

    def _create_conversation_result(self, response: str) -> conversation.ConversationResult:
        """Create a conversation result."""
        intent_response = intent.IntentResponse(language="*")
        intent_response.async_set_speech(response)
        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=None,
        )

    async def _save_automation(self, automation_config: dict[str, Any]) -> None:
        """Save automation to Home Assistant."""
        try:
            # Generate unique ID for the automation
            if 'id' not in automation_config:
                automation_config['id'] = str(uuid.uuid4())[:8]
                
            # Fix the structure to match Home Assistant format
            # Convert trigger -> triggers, action -> actions if needed
            if 'trigger' in automation_config and 'triggers' not in automation_config:
                automation_config['triggers'] = automation_config.pop('trigger')
            if 'action' in automation_config and 'actions' not in automation_config:
                automation_config['actions'] = automation_config.pop('action')
            if 'condition' in automation_config and 'conditions' not in automation_config:
                automation_config['conditions'] = automation_config.pop('condition')
            
            # Get existing automations
            automation_config_path = self.hass.config.path("automations.yaml")
            
            def _read_automations():
                try:
                    with open(automation_config_path, 'r', encoding='utf-8') as file:
                        content = file.read().strip()
                        if not content:
                            return []
                        return yaml.safe_load(content) or []
                except FileNotFoundError:
                    return []
                except Exception as err:
                    _LOGGER.error("Error reading automations.yaml: %s", err)
                    return []
            
            def _write_automations(automations_list):
                with open(automation_config_path, 'w', encoding='utf-8') as file:
                    yaml.dump(automations_list, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            # Run file operations in executor to avoid blocking
            existing_automations = await self.hass.async_add_executor_job(_read_automations)
            
            # Ensure it's a list
            if not isinstance(existing_automations, list):
                existing_automations = []
            
            # Add new automation
            existing_automations.append(automation_config)
            
            # Save back to file
            await self.hass.async_add_executor_job(_write_automations, existing_automations)
            
            # Reload automations
            await self.hass.services.async_call("automation", "reload")
            
            _LOGGER.info("Automation saved with ID %s and reloaded successfully", automation_config['id'])
            
        except Exception as err:
            _LOGGER.error("Failed to save automation: %s", err)
            raise 

 