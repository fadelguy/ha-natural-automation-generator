"""Conversation entity for Natural Automation Generator integration."""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import yaml

from .const import (
    DOMAIN,
    STEP_ANALYSIS,
    STEP_AWAITING_APPROVAL,
    STEP_CLARIFICATION,
    STEP_COMPLETED,
    STEP_CREATING,
    STEP_ERROR,
    STEP_PREVIEW,
)
from .coordinator import NaturalAutomationGeneratorCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for ongoing conversation."""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_request: str = ""
    language: str = "en"
    step: str = STEP_ANALYSIS
    collected_info: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    needs_clarification: bool = False
    last_question: str = ""
    attempt_count: int = 0


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
            "sw_version": "1.2.7",
        }

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Handle the conversation message."""
        _LOGGER.debug("Processing conversation input: %s", user_input.text)
        
        try:
            # Get or create conversation context
            conversation_id = user_input.conversation_id or str(uuid.uuid4())
            context = self._get_or_create_context(conversation_id, user_input.text)
            
            response_text = ""
            
            # Handle different conversation steps
            if context.step == STEP_ANALYSIS:
                response_text = await self._handle_initial_request(context, user_input.text)
            elif context.step == STEP_CLARIFICATION:
                response_text = await self._handle_clarification_response(context, user_input.text)
            elif context.step == STEP_AWAITING_APPROVAL:
                response_text = await self._handle_approval_response(context, user_input.text)
            else:
                # Handle non-automation requests (entity listing, help, etc.)
                response_text = await self._handle_general_request(user_input.text, "en")
            
            # Add to chat log
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
                conversation_id=conversation_id,
                response=response,
                continue_conversation=True,
            )
            
        except Exception as err:
            _LOGGER.error("Error in conversation handling: %s", err)
            error_text = f"❌ Sorry, I encountered an error: {err}"
            
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

    def _get_or_create_context(self, conversation_id: str, user_text: str) -> ConversationContext:
        """Get existing or create new conversation context."""
        if conversation_id not in self._conversations:
            # Create new context for potential automation request
            context = ConversationContext(
                conversation_id=conversation_id,
                original_request=user_text,
                step=STEP_ANALYSIS
            )
            self._conversations[conversation_id] = context
        
        return self._conversations[conversation_id]

    async def _handle_initial_request(self, context: ConversationContext, user_text: str) -> str:
        """Handle the initial automation request and analyze it."""
        _LOGGER.debug("Handling initial request: %s", user_text)
        
        # Analyze the request
        analysis_result = await self._coordinator.analyze_request(user_text)
        
        if not analysis_result["success"]:
            context.step = STEP_ERROR
            return await self._generate_error_response("en", analysis_result.get("error", "Unknown error"))
        
        analysis = analysis_result["analysis"]
        context.analysis_results = analysis
        context.language = analysis.get("language", "en")
        
        # Check if this is actually an automation request
        if not analysis.get("is_automation_request", False):
            # Handle as general request
            context.step = "general"
            return await self._handle_general_request(user_text, context.language)
        
        if analysis.get("needs_clarification", False):
            # Need clarification
            context.step = STEP_CLARIFICATION
            clarification_result = await self._coordinator.generate_clarification(user_text, analysis)
            
            if clarification_result["success"]:
                context.last_question = clarification_result["question"]
                return clarification_result["question"]
            else:
                context.step = STEP_ERROR
                return await self._generate_error_response(context.language, clarification_result.get("error", "Unknown error"))
        else:
            # No clarification needed, show preview
            context.step = STEP_PREVIEW
            context.collected_info = analysis.get("understood", {})
            return await self._generate_preview(context)

    async def _handle_clarification_response(self, context: ConversationContext, user_text: str) -> str:
        """Handle user's response to clarification question."""
        _LOGGER.debug("Handling clarification response: %s", user_text)
        
        # Update collected info based on response
        # This is a simplified version - in reality, you'd want more sophisticated parsing
        context.collected_info.update({
            "user_clarification": user_text,
            "clarification_step": context.attempt_count
        })
        
        context.attempt_count += 1
        
        # Check if we need more clarification or can proceed to preview
        if context.attempt_count < 3:  # Limit clarification rounds
            # Try to analyze again with the additional info
            combined_request = f"{context.original_request}. {user_text}"
            analysis_result = await self._coordinator.analyze_request(combined_request)
            
            if analysis_result["success"]:
                analysis = analysis_result["analysis"]
                if analysis.get("needs_clarification", False):
                    # Still need clarification
                    clarification_result = await self._coordinator.generate_clarification(combined_request, analysis)
                    if clarification_result["success"]:
                        context.last_question = clarification_result["question"]
                        return clarification_result["question"]
        
        # Move to preview
        context.step = STEP_PREVIEW
        return await self._generate_preview(context)

    async def _generate_preview(self, context: ConversationContext) -> str:
        """Generate automation preview and ask for approval."""
        _LOGGER.debug("Generating preview for context: %s", context.collected_info)
        
        preview_result = await self._coordinator.generate_preview(context.collected_info, context.language)
        
        if preview_result["success"]:
            context.step = STEP_AWAITING_APPROVAL
            return preview_result["preview"]
        else:
            context.step = STEP_ERROR
            return await self._generate_error_response(context.language, preview_result.get("error", "Unknown error"))

    async def _handle_approval_response(self, context: ConversationContext, user_text: str) -> str:
        """Handle user's approval/rejection/modification response."""
        _LOGGER.debug("Handling approval response: %s", user_text)
        
        # Analyze user intent
        intent_result = await self._coordinator.analyze_user_intent(user_text, context.collected_info)
        
        if not intent_result["success"]:
            return await self._generate_error_response(context.language, "Could not understand response")
        
        intent = intent_result["intent"]
        intent_type = intent.get("intent", "").lower()
        
        if intent_type == "approve":
            # Create the automation
            context.step = STEP_CREATING
            return await self._create_automation(context)
        elif intent_type == "reject":
            # Cancel automation creation
            context.step = STEP_COMPLETED
            self._conversations.pop(context.conversation_id, None)
            return await self._generate_cancellation_response(context.language)
        elif intent_type == "modify":
            # Handle modifications
            changes = intent.get("changes_requested", "")
            context.collected_info["requested_changes"] = changes
            context.step = STEP_CLARIFICATION
            
            # Generate clarification request for modifications
            modification_context = f"User wants to modify: {changes}. Original request: {context.original_request}"
            clarification_result = await self._coordinator.generate_clarification(modification_context, context.analysis_results)
            
            if clarification_result["success"]:
                return clarification_result["question"]
            else:
                return await self._generate_error_response(context.language, "Could not generate modification question")
        else:
            # Unclear response - ask for clarification
            return await self._generate_error_response(context.language, "Unclear approval response")

    async def _create_automation(self, context: ConversationContext) -> str:
        """Create the automation and save it."""
        _LOGGER.debug("Creating automation from context: %s", context.collected_info)
        
        # Generate automation
        result = await self._coordinator.generate_automation(context.collected_info)
        
        if result["success"]:
            try:
                # Parse and save automation
                automation_config = yaml.safe_load(result["yaml_config"])
                
                if not isinstance(automation_config, dict):
                    raise ValueError("Generated YAML is not a dictionary/object")
                
                await self._save_automation(automation_config)
                
                # Success response
                automation_name = automation_config.get('alias', 'New Automation')
                context.step = STEP_COMPLETED
                self._conversations.pop(context.conversation_id, None)
                
                success_result = await self._coordinator.generate_success_response(
                    context.language, automation_name, result['description'], result['yaml_config']
                )
                
                if success_result["success"]:
                    return success_result["response"]
                else:
                    return await self._generate_error_response(context.language, "Could not generate success message")
                
            except Exception as err:
                _LOGGER.error("Error creating automation: %s", err)
                context.step = STEP_ERROR
                return await self._generate_error_response(context.language, f"Error creating automation: {err}")
        else:
            context.step = STEP_ERROR
            return await self._generate_error_response(context.language, result.get('error', 'Unknown error'))

    async def _handle_general_request(self, user_text: str, language: str = "en") -> str:
        """Handle non-automation requests like entity listing, help, etc."""
        general_result = await self._coordinator.generate_general_response(user_text, language)
        
        if general_result["success"]:
            return general_result["response"]
        else:
            return await self._generate_error_response(language, general_result.get("error", "Unknown error"))

    async def _generate_error_response(self, language: str, error: str) -> str:
        """Generate error response using LLM."""
        error_result = await self._coordinator.generate_error_response(language, error)
        
        if error_result["success"]:
            return error_result["response"]
        else:
            # Fallback error message
            if language == "he":
                return f"❌ מצטער, יש לי בעיה: {error}"
            else:
                return f"❌ Sorry, I encountered an error: {error}"

    async def _generate_cancellation_response(self, language: str) -> str:
        """Generate cancellation response using LLM."""
        cancel_result = await self._coordinator.generate_cancellation_response(language)
        
        if cancel_result["success"]:
            return cancel_result["response"]
        else:
            # Fallback cancellation message
            if language == "he":
                return "בסדר, ביטלתי את יצירת האוטומציה."
            else:
                return "Okay, I've cancelled the automation creation."

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