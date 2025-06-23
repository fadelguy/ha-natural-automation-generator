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
    NAME,
    VERSION,
    STEP_ANALYSIS,
    STEP_AWAITING_APPROVAL,
    STEP_CLARIFICATION,
    STEP_COMPLETED,
    STEP_CREATING,
    STEP_ERROR,
    STEP_PREVIEW,
    STEP_ANALYZING,
    STEP_CLARIFYING,
    STEP_COLLECTING_INFO,
    STEP_INITIAL,
    STEP_CREATING_AUTOMATION,
)
from .coordinator import NaturalAutomationCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for ongoing conversation."""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_request: str = ""
    language: str = "en"
    step: str = STEP_INITIAL
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
        coordinator: NaturalAutomationCoordinator,
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
        """Handle incoming user message."""
        user_text = user_input.text.strip()
        agent_id = user_input.agent_id or "unknown"
        
        # Update progress: Starting analysis
        await _update_progress_entity(self.hass, agent_id, "🔍 Analyzing request...")
        
        _LOGGER.debug("Handling message: %s", user_text)

        # Get or create conversation context
        context = self._get_conversation_context(user_input.conversation_id)
        
        try:
            if context.step == STEP_INITIAL:
                # Update progress: Analyzing with AI
                await _update_progress_entity(self.hass, agent_id, "🧠 Processing with AI...")
                return await self._handle_initial_request(context, user_text, chat_log, agent_id)
            
            elif context.step == STEP_CLARIFYING:
                # Update progress: Processing clarification
                await _update_progress_entity(self.hass, agent_id, "💭 Processing clarification...")
                return await self._handle_clarification_response(context, user_text, chat_log, agent_id)
            
            elif context.step == STEP_AWAITING_APPROVAL:
                # Update progress: Processing approval
                await _update_progress_entity(self.hass, agent_id, "✅ Processing approval...")
                return await self._handle_approval_response(context, user_text, chat_log, agent_id)
            
            else:
                # Update progress: Error handling
                await _update_progress_entity(self.hass, agent_id, "❌ Error occurred")
                return await self._handle_error(context, "Unknown conversation state", chat_log, agent_id)
                
        except Exception as err:
            _LOGGER.error("Error handling message: %s", err)
            await _update_progress_entity(self.hass, agent_id, "❌ Error occurred")
            return await self._handle_error(context, str(err), chat_log, agent_id)

    def _get_conversation_context(self, conversation_id: str) -> ConversationContext:
        """Get existing or create new conversation context."""
        if conversation_id not in self._conversations:
            # Create new context
            context = ConversationContext(
                conversation_id=conversation_id,
                step=STEP_INITIAL
            )
            self._conversations[conversation_id] = context
        
        return self._conversations[conversation_id]

    async def _handle_initial_request(
        self, 
        context: ConversationContext, 
        user_text: str, 
        chat_log: conversation.ChatLog, 
        agent_id: str
    ) -> conversation.ConversationResult:
        """Handle the initial automation request."""
        context.original_request = user_text
        
        # Update progress: Analyzing request
        await _update_progress_entity(self.hass, agent_id, "🔍 Analyzing automation request...")
        
        # Analyze the request
        analysis_result = await self._coordinator.analyze_request(user_text, chat_log, agent_id)
        
        if not analysis_result["success"]:
            context.step = STEP_ERROR
            await _update_progress_entity(self.hass, agent_id, "❌ Analysis failed")
            return await self._generate_error_response(analysis_result.get("error", "Analysis failed"))
        
        analysis = analysis_result["analysis"]
        context.language = analysis.get("language", "en")
        
        if analysis.get("is_automation_request", False):
            if analysis.get("needs_clarification", False):
                # Update progress: Preparing question
                await _update_progress_entity(self.hass, agent_id, "❓ Preparing clarification question...")
                return await self._generate_clarification(context, analysis, chat_log, agent_id)
            else:
                # Update progress: Preparing preview
                await _update_progress_entity(self.hass, agent_id, "👀 Preparing automation preview...")
                context.collected_info = analysis
                return await self._generate_preview(context, chat_log, agent_id)
        else:
            # Update progress: Generating response
            await _update_progress_entity(self.hass, agent_id, "💬 Generating response...")
            return await self._generate_general_response(user_text, chat_log, agent_id)

    async def _generate_clarification(
        self, 
        context: ConversationContext, 
        analysis: dict[str, Any], 
        chat_log: conversation.ChatLog, 
        agent_id: str
    ) -> conversation.ConversationResult:
        """Generate a clarifying question."""
        context.step = STEP_CLARIFYING
        context.collected_info = analysis
        
        # Update progress: Generating clarification question
        await _update_progress_entity(self.hass, agent_id, "❓ Generating clarification question...")
        
        clarification_result = await self._coordinator.generate_clarification(
            context.original_request, analysis
        )
        
        if clarification_result["success"]:
            await _update_progress_entity(self.hass, agent_id, "❓ Question ready")
            return self._create_conversation_result(clarification_result["question"])
        else:
            context.step = STEP_ERROR
            await _update_progress_entity(self.hass, agent_id, "❌ Failed to generate question")
            return await self._generate_error_response(clarification_result.get("error", "Failed to generate clarification"))

    async def _generate_preview(
        self, 
        context: ConversationContext, 
        chat_log: conversation.ChatLog, 
        agent_id: str
    ) -> conversation.ConversationResult:
        """Generate automation preview and ask for approval."""
        _LOGGER.debug("Generating preview for context: %s", context.collected_info)
        
        # Update progress: Generating preview
        await _update_progress_entity(self.hass, agent_id, "👀 Generating automation preview...")
        
        preview_result = await self._coordinator.generate_preview(context.collected_info)
        
        if preview_result["success"]:
            context.step = STEP_AWAITING_APPROVAL
            await _update_progress_entity(self.hass, agent_id, "👀 Preview ready - awaiting approval")
            return self._create_conversation_result(preview_result["preview"])
        else:
            context.step = STEP_ERROR
            await _update_progress_entity(self.hass, agent_id, "❌ Failed to generate preview")
            return await self._generate_error_response(preview_result.get("error", "Unknown error"))

    async def _handle_approval_response(
        self, 
        context: ConversationContext, 
        user_text: str, 
        chat_log: conversation.ChatLog, 
        agent_id: str
    ) -> conversation.ConversationResult:
        """Handle user's approval/rejection/modification request."""
        
        # Update progress: Processing approval
        await _update_progress_entity(self.hass, agent_id, "✅ Processing approval response...")
        
        # Use LLM to analyze the approval response
        approval_analysis = await self._coordinator.analyze_approval_response(
            context.original_request, 
            context.collected_info, 
            user_text
        )
        
        if not approval_analysis["success"]:
            await _update_progress_entity(self.hass, agent_id, "❌ Failed to process approval")
            return await self._generate_error_response("Failed to process your response")
        
        analysis = approval_analysis["analysis"]
        action = analysis.get("action", "unknown")
        
        if action == "approve":
            # Update progress: Creating automation
            await _update_progress_entity(self.hass, agent_id, "🛠 Creating automation...")
            return await self._create_automation(context, chat_log, agent_id)
        elif action == "reject":
            # Update progress: Request cancelled
            await _update_progress_entity(self.hass, agent_id, "🚫 Request cancelled")
            context.step = STEP_INITIAL
            return self._create_conversation_result(analysis.get("response", "Automation creation cancelled. How else can I help?"))
        elif action == "modify":
            # Update progress: Processing modifications
            await _update_progress_entity(self.hass, agent_id, "🔄 Processing modifications...")
            # Update context with modifications and regenerate preview
            if "modifications" in analysis:
                context.collected_info.update(analysis["modifications"])
            return await self._generate_preview(context, chat_log, agent_id)
        else:
            await _update_progress_entity(self.hass, agent_id, "❓ Clarification needed")
            return self._create_conversation_result(analysis.get("response", "I didn't understand your response. Please say 'yes' to approve, 'no' to cancel, or describe what you'd like to change."))

    async def _create_automation(
        self, 
        context: ConversationContext, 
        chat_log: conversation.ChatLog, 
        agent_id: str
    ) -> conversation.ConversationResult:
        """Create the automation based on collected information."""
        context.step = STEP_CREATING_AUTOMATION
        
        # Update progress: Generating automation code
        await _update_progress_entity(self.hass, agent_id, "📝 Generating automation code...")
        
        creation_result = await self._coordinator.create_automation(context.collected_info, chat_log, agent_id)
        
        if creation_result["success"]:
            # Update progress: Automation created successfully
            await _update_progress_entity(self.hass, agent_id, "✅ Automation created successfully!")
            context.step = STEP_INITIAL  # Reset for next request
            return self._create_conversation_result(creation_result["message"])
        else:
            context.step = STEP_ERROR
            await _update_progress_entity(self.hass, agent_id, "❌ Failed to create automation")
            return await self._generate_error_response(creation_result.get("error", "Failed to create automation"))

    async def _generate_general_response(
        self, 
        user_request: str, 
        chat_log: conversation.ChatLog, 
        agent_id: str
    ) -> conversation.ConversationResult:
        """Generate response for non-automation requests."""
        
        # Update progress: Generating response
        await _update_progress_entity(self.hass, agent_id, "💬 Generating response...")
        
        response_result = await self._coordinator.generate_general_response(user_request)
        
        if response_result["success"]:
            await _update_progress_entity(self.hass, agent_id, "💬 Response ready")
            return self._create_conversation_result(response_result["response"])
        else:
            await _update_progress_entity(self.hass, agent_id, "❌ Failed to generate response")
            return await self._generate_error_response(response_result.get("error", "Failed to generate response"))

    async def _handle_clarification_response(
        self, 
        context: ConversationContext, 
        user_text: str, 
        chat_log: conversation.ChatLog, 
        agent_id: str
    ) -> conversation.ConversationResult:
        """Handle user's response to clarification question."""
        
        # Update progress: Analyzing clarification response
        await _update_progress_entity(self.hass, agent_id, "💭 Analyzing clarification response...")
        
        # Use LLM to analyze the clarification response
        analysis_result = await self._coordinator.analyze_clarification_response(
            context.original_request,
            context.collected_info,
            user_text
        )
        
        if not analysis_result["success"]:
            await _update_progress_entity(self.hass, agent_id, "❌ Failed to analyze response")
            return await self._generate_error_response("Failed to process your clarification")
        
        analysis = analysis_result["analysis"]
        
        if analysis.get("ready_for_automation", False):
            # Update progress: Preparing preview
            await _update_progress_entity(self.hass, agent_id, "👀 Preparing automation preview...")
            # Update context with the resolved information
            context.collected_info.update(analysis.get("updated_info", {}))
            return await self._generate_preview(context, chat_log, agent_id)
        elif analysis.get("needs_more_clarification", False):
            # Update progress: Preparing follow-up question
            await _update_progress_entity(self.hass, agent_id, "❓ Preparing follow-up question...")
            # Generate another clarification question
            return await self._generate_clarification(context, context.collected_info, chat_log, agent_id)
        else:
            # Update progress: Processing response
            await _update_progress_entity(self.hass, agent_id, "💭 Processing response...")
            # Return the LLM's response to continue the conversation
            response = analysis.get("response", "I need more information to proceed.")
            return self._create_conversation_result(response)

    async def _generate_error_response(self, error: str) -> conversation.ConversationResult:
        """Generate error response."""
        return self._create_conversation_result(f"Error: {error}")

    async def _handle_error(self, context: ConversationContext, error: str, chat_log, agent_id: str) -> conversation.ConversationResult:
        """Handle error in conversation."""
        context.step = STEP_ERROR
        return await self._generate_error_response(error)

    def _create_conversation_result(self, response: str) -> conversation.ConversationResult:
        """Create a conversation result."""
        return conversation.ConversationResult(
            response=conversation.ConversationResponse(
                response_type=intent.IntentResponseType.ACTION_DONE,
                language="*",  # Support all languages
                intent=None,
                speech={"plain": {"speech": response, "extra_data": None}},
                card=None,
                error_code=None,
            ),
            conversation_id=None,
        )

    async def _generate_cancellation_response(self) -> str:
        """Generate cancellation response using LLM."""
        cancel_result = await self._coordinator.generate_cancellation_response()
        
        if cancel_result["success"]:
            return cancel_result["response"]
        else:
            # Fallback cancellation message - let LLM decide language based on conversation
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

    async def _add_progress_message(self, chat_log: conversation.ChatLog, agent_id: str, message: str) -> None:
        """Add a progress message to the chat."""
        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(
                agent_id=agent_id,
                content=message,
            )
        )

# Progress message helper function
async def _update_progress_entity(hass: HomeAssistant, agent_id: str, message: str) -> None:
    """Update progress entity for dashboard display."""
    try:
        # Create or update input_text entity for progress display
        entity_id = f"input_text.natural_automation_progress_{agent_id}"
        await hass.services.async_call(
            "input_text",
            "set_value",
            {
                "entity_id": entity_id,
                "value": message
            },
            blocking=False
        )
    except Exception as err:
        _LOGGER.debug("Could not update progress entity: %s", err) 