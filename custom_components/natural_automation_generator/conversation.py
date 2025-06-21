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
        self._attr_supported_features = conversation.ConversationEntityFeature.CONTROL

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return "*"  # Support all languages

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "Natural Automation Generator",
            "manufacturer": "Natural Automation Generator",
            "model": "Automation Generator",
            "sw_version": "1.2.3",
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
                        _LOGGER.debug("Parsing YAML config: %s", result["yaml_config"][:500])
                        automation_config = yaml.safe_load(result["yaml_config"])
                        
                        if not isinstance(automation_config, dict):
                            raise ValueError("Generated YAML is not a dictionary/object")
                        
                        await self._save_automation(automation_config)
                        
                        # Create a nice response with automation details
                        automation_name = automation_config.get('alias', 'New Automation')
                        response_text = f"✅ **Automation Created Successfully!**\n\n" \
                                       f"**Name:** {automation_name}\n" \
                                       f"**Description:** {result['description']}\n\n" \
                                       f"**Generated YAML:**\n```yaml\n{result['yaml_config']}\n```\n\n" \
                                       f"🎉 The automation has been saved to your `automations.yaml` file and is now active!"
                        
                        # Add to chat log
                        chat_log.async_add_assistant_content_without_tools(
                            conversation.AssistantContent(
                                agent_id=user_input.agent_id,
                                content=response_text,
                            )
                        )
                        
                    except yaml.YAMLError as err:
                        _LOGGER.error("Invalid YAML generated: %s", err)
                        _LOGGER.error("YAML content was: %s", result["yaml_config"])
                        response_text = f"❌ I generated invalid automation YAML. Error: {err}\n\nRAW YAML:\n```\n{result['yaml_config']}\n```\n\nPlease try rephrasing your request."
                        
                        chat_log.async_add_assistant_content_without_tools(
                            conversation.AssistantContent(
                                agent_id=user_input.agent_id,
                                content=response_text,
                            )
                        )
                    except Exception as err:
                        _LOGGER.error("Error processing automation: %s", err)
                        _LOGGER.error("YAML content was: %s", result["yaml_config"])
                        
                        # Try to fix the YAML and parse again
                        try:
                            from .llm_providers.openai_provider import OpenAIProvider
                            provider = OpenAIProvider(self.hass, self._config_entry)
                            fixed_yaml = provider._fix_compressed_yaml(result["yaml_config"])
                            automation_config = yaml.safe_load(fixed_yaml)
                            
                            if isinstance(automation_config, dict):
                                await self._save_automation(automation_config)
                                automation_name = automation_config.get('alias', 'New Automation')
                                response_text = f"✅ **Automation Created Successfully!** (After fixing YAML formatting)\n\n" \
                                               f"**Name:** {automation_name}\n" \
                                               f"**Description:** {result['description']}\n\n" \
                                               f"**Fixed YAML:**\n```yaml\n{fixed_yaml}\n```\n\n" \
                                               f"🎉 The automation has been saved to your `automations.yaml` file and is now active!"
                            else:
                                raise ValueError("Still not a valid automation after fixing")
                                
                        except Exception as fix_err:
                            _LOGGER.error("Failed to fix YAML: %s", fix_err)
                            response_text = f"❌ Error processing automation: {err}\n\nRAW YAML:\n```\n{result['yaml_config']}\n```\n\nPlease try rephrasing your request with more specific details."
                        
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
            import uuid
            import asyncio
            
            # Generate unique ID for the automation
            if 'id' not in automation_config:
                automation_config['id'] = str(uuid.uuid4())[:8]
                
            # Add auto-generated indicator to alias
            if 'alias' in automation_config:
                alias = automation_config['alias']
                if not alias.endswith('(Auto Generated)'):
                    automation_config['alias'] = f"{alias} (Auto Generated)"
            else:
                automation_config['alias'] = "Automation (Auto Generated)"
                
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