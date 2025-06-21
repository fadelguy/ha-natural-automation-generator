"""Conversation entity for Natural Automation Generator integration."""
from __future__ import annotations

import logging
from typing import Any, Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import yaml

from .const import DOMAIN
from .coordinator import NaturalAutomationGeneratorCoordinator

_LOGGER = logging.getLogger(__name__)


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
        self._attr_supported_languages = ["en", "he", "*"]
        self._attr_supported_features = conversation.ConversationEntityFeature.CONTROL

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "Natural Automation Generator",
            "manufacturer": "Natural Automation Generator",
            "model": "Automation Generator",
            "sw_version": "1.1.0",
        }

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Handle the conversation message."""
        _LOGGER.debug("Processing conversation input: %s", user_input.text)
        
        # Check if this is a request to create an automation
        automation_keywords = [
            # English keywords
            "create", "make", "generate", "automation", "automate", "build", "new",
            # Hebrew keywords  
            "יצור", "צור", "עשה", "בנה", "תייצר", "חדש", "אוטומציה"
        ]
        is_automation_request = any(keyword in user_input.text.lower() for keyword in automation_keywords)
        
        try:
            if is_automation_request:
                # Generate automation
                result = await self._coordinator.generate_automation(user_input.text)
                
                if result["success"]:
                    # Parse YAML and save automation
                    try:
                        automation_config = yaml.safe_load(result["yaml_config"])
                        await self._save_automation(automation_config)
                        
                        response_text = f"✅ I've created the automation successfully!\n\n**Generated automation:**\n```yaml\n{result['yaml_config']}\n```\n\nThe automation has been saved and is now active."
                        
                        # Add to chat log
                        chat_log.async_add_assistant_content_without_tools(
                            conversation.AssistantContent(
                                agent_id=user_input.agent_id,
                                content=response_text,
                            )
                        )
                        
                    except yaml.YAMLError as err:
                        _LOGGER.error("Invalid YAML generated: %s", err)
                        response_text = f"❌ I generated invalid automation YAML. Error: {err}\n\nPlease try rephrasing your request."
                        
                        chat_log.async_add_assistant_content_without_tools(
                            conversation.AssistantContent(
                                agent_id=user_input.agent_id,
                                content=response_text,
                            )
                        )
                else:
                    response_text = f"❌ Failed to generate automation: {result.get('error', 'Unknown error')}\n\nPlease try again with a clearer description."
                    
                    chat_log.async_add_assistant_content_without_tools(
                        conversation.AssistantContent(
                            agent_id=user_input.agent_id,
                            content=response_text,
                        )
                    )
            else:
                # Handle general questions about entities or system
                entities_info = await self._coordinator.get_entities_info()
                areas_info = await self._coordinator.get_areas_info()
                
                # Check for entity listing requests in multiple languages
                entity_list_keywords = ["entities", "list", "devices", "רשימה", "מכשירים", "רשימת"]
                if any(keyword in user_input.text.lower() for keyword in entity_list_keywords):
                    # Detect language for response
                    is_hebrew = any(hebrew_char in user_input.text for hebrew_char in "אבגדהוזחטיכלמנסעפצקרשת")
                    if is_hebrew:
                        response_text = f"📋 **המכשירים שלך ב-Home Assistant:**\n\n{entities_info}\n\n{areas_info}"
                    else:
                        response_text = f"📋 **Your Home Assistant entities:**\n\n{entities_info}\n\n{areas_info}"
                else:
                    # General conversation response
                    response_text = f"🤖 Hi! I'm your Natural Automation Generator.\n\n" \
                                  f"I can help you create Home Assistant automations using natural language.\n\n" \
                                  f"**Examples:**\n" \
                                  f"• 'Create an automation to turn on bathroom light at midnight'\n" \
                                  f"• 'Make an automation for motion detection in hallway'\n" \
                                  f"• 'Generate automation to close blinds when sunny'\n\n" \
                                  f"You can also ask me to 'list entities' to see all your devices.\n\n" \
                                  f"What automation would you like me to create? 😊"
                
                chat_log.async_add_assistant_content_without_tools(
                    conversation.AssistantContent(
                        agent_id=user_input.agent_id,
                        content=response_text,
                    )
                )
            
            # Create intent response
            response = intent.IntentResponse(language=user_input.language)
            response.async_set_speech(response_text)
            
            return conversation.ConversationResult(
                conversation_id=user_input.conversation_id,
                response=response,
                continue_conversation=False,
            )
            
        except Exception as err:
            _LOGGER.error("Error processing conversation: %s", err)
            error_text = f"❌ Sorry, I encountered an error: {err}\n\nPlease try again."
            
            chat_log.async_add_assistant_content_without_tools(
                conversation.AssistantContent(
                    agent_id=user_input.agent_id,
                    content=error_text,
                )
            )
            
            response = intent.IntentResponse(language=user_input.language)
            response.async_set_speech(error_text)
            
            return conversation.ConversationResult(
                conversation_id=user_input.conversation_id,
                response=response,
                continue_conversation=False,
            )

    async def _save_automation(self, automation_config: dict[str, Any]) -> None:
        """Save automation to Home Assistant."""
        try:
            # Get existing automations
            automation_config_path = self.hass.config.path("automations.yaml")
            
            try:
                with open(automation_config_path, 'r', encoding='utf-8') as file:
                    existing_automations = yaml.safe_load(file) or []
            except FileNotFoundError:
                existing_automations = []
            
            # Add new automation
            existing_automations.append(automation_config)
            
            # Save back to file
            with open(automation_config_path, 'w', encoding='utf-8') as file:
                yaml.dump(existing_automations, file, default_flow_style=False, allow_unicode=True)
            
            # Reload automations
            await self.hass.services.async_call("automation", "reload")
            
            _LOGGER.info("Automation saved and reloaded successfully")
            
        except Exception as err:
            _LOGGER.error("Failed to save automation: %s", err)
            raise 