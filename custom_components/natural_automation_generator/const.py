"""Constants for the Natural Automation Generator integration."""

# Domain and basic info
DOMAIN = "natural_automation_generator"
NAME = "Natural Automation Generator"
VERSION = "2.2.3"

# Configuration and services
DEFAULT_NAME = NAME
SERVICE_GENERATE_AUTOMATION = "generate_automation"

# Conversation steps
STEP_INITIAL = "initial"
STEP_ANALYZING = "analyzing"
STEP_ANALYSIS = "analysis"
STEP_CLARIFYING = "clarifying"
STEP_CLARIFICATION = "clarification"
STEP_COLLECTING_INFO = "collecting_info"
STEP_PREVIEW = "preview"
STEP_AWAITING_APPROVAL = "awaiting_approval"
STEP_CREATING_AUTOMATION = "creating_automation"
STEP_CREATING = "creating"
STEP_COMPLETED = "completed"
STEP_ERROR = "error"

# Automation filename
AUTOMATIONS_FILE = "automations.yaml"

# Default LLM settings
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL_OPENAI = "gpt-4"
DEFAULT_MODEL_GEMINI = "gemini-2.5-flash"
DEFAULT_MAX_TOKENS = 1500
DEFAULT_TEMPERATURE = 0.7

# Configuration flow constants
CONF_LLM_PROVIDER = "llm_provider"
CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"

# LLM Providers
PROVIDER_OPENAI = "openai"
PROVIDER_GEMINI = "gemini"

# Available models
OPENAI_MODELS = ["gpt-4.1", "gpt-4o", "gpt-4o-mini"]
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# Services
SERVICE_CREATE_AUTOMATION = "create_automation"
SERVICE_PREVIEW_AUTOMATION = "preview_automation"
SERVICE_LIST_ENTITIES = "list_entities"

# Service attributes
ATTR_DESCRIPTION = "description"
ATTR_AUTOMATION_CONFIG = "automation_config"
ATTR_PREVIEW_ONLY = "preview_only"
ATTR_AUTOMATION_NAME = "automation_name"
ATTR_YAML_CONFIG = "yaml_config"

# Errors
ERROR_INVALID_PROVIDER = "Invalid LLM provider specified"
ERROR_API_KEY_REQUIRED = "API key is required"
ERROR_GENERATION_FAILED = "Failed to generate automation"
ERROR_INVALID_YAML = "Generated YAML is invalid"
ERROR_SAVE_FAILED = "Failed to save automation"

# Prompt templates
SYSTEM_PROMPT_TEMPLATE = """
You generate valid YAML automations for Home Assistant.

🛠 Task:
Create a single automation from natural language.

📏 Rules:
- ⚠️ CRITICAL: Use ONLY the exact entity IDs listed below in the ENTITIES section
- ⚠️ NEVER invent or create entity IDs that are not in the list
- ⚠️ If you need a light, use ONLY entities starting with "light." from the list
- ⚠️ If you need a switch, use ONLY entities starting with "switch." from the list
- Output a valid YAML object (no list)
- Include: id, alias, triggers, actions
- Use plural keys: triggers, actions, conditions
- Format correctly with indentation
- Use exact entity IDs from the list below
- id: 8–12 lowercase characters, no spaces

📦 AVAILABLE ENTITIES (USE ONLY THESE):
{entities}

📍 AVAILABLE AREAS (USE ONLY THESE):
{areas}

✅ Example:
id: "hello_world"
alias: "Hello world"
triggers:
  - platform: time
    at: "00:00:00"
actions:
  - service: light.turn_on
    target:
      entity_id: light.bathroom

⚠️ REMINDER: Only use entity IDs that appear in the AVAILABLE ENTITIES list above!

Return YAML only.
"""

ANALYSIS_PROMPT_TEMPLATE = """
You classify user requests.

📦 Entities: {entities}
📍 Areas: {areas}
🗣 User: {user_request}

⚠️ CRITICAL: Use ONLY exact entity IDs from the entities list above.

Classify if this is an automation request (explicit intent only).

Return JSON:
{{
  "is_automation_request": true/false,
  "language": "he/en",
  "understood": {{
    "action": "turn_on",
    "entity_type": "light",
    "area": "living_room",
    "time": "evening",
    "conditions": ""}},
  "missing_info": [],
  "ambiguous_entities": {{ "light": ["light.living1", "light.living2"] }},
  "needs_clarification": true/false
}}

Only return JSON.
"""

GENERAL_RESPONSE_PROMPT = """
Answer briefly and to the point.

🗣 Request: {user_request}
📦 Entities: {entities}
📍 Areas: {areas}

🌐 ALWAYS respond in the same language as the user's request.
Give a short, helpful answer - maximum 2-3 sentences.
Only provide entity/area lists if specifically asked.
Don't explain everything - just answer what was asked.

Return brief response only.
"""

SUCCESS_RESPONSE_PROMPT = """
Automation created successfully.

📝 Name: {automation_name}
📄 Description: {description}
🧾 YAML:
{yaml_config}

🌐 ALWAYS respond in the same language as the user's original request.
Respond positively with:
1. Confirmation
2. Name & description
3. YAML shown nicely
4. State it's saved and active

Return message only.
"""

CANCELLATION_RESPONSE_PROMPT = """
User cancelled automation.

🌐 ALWAYS respond in the same language as the user's request.
Acknowledge the cancellation, offer to restart anytime. Friendly tone.

Return message only.
"""

ERROR_RESPONSE_PROMPT = """
Error occurred in automation creation.

⚠️ Error: {error}
📝 Context: {context}

🌐 ALWAYS respond in the same language as the user's request.
Explain there's an error without technical details. Offer helpful next steps.

Return message only.
"""

CLARIFICATION_PROMPT_TEMPLATE = """
Ask user a clarifying question based on analysis.

🗣 Request: {original_request}
📊 Analysis: {analysis_results}

🌐 ALWAYS respond in the same language as the user's request.
Use friendly formatting with emojis.
Examples:
- Multiple entities ➜ list with names & IDs
- Time ➜ ⏰ Morning / Noon / Evening / Night
- Trigger ➜ 🎯 Options like motion/time/sun

Return question only.
"""

PREVIEW_PROMPT_TEMPLATE = """
Create a preview of the planned automation.

📋 Info: {context}
📦 Entities: {entities}
📍 Areas: {areas}

🌐 ALWAYS respond in the same language as the user's original request.
Summarize clearly:
- What it does
- When it runs
- Affected entities

Use friendly tone and emojis. Ask for approval.

Return message only.
"""

APPROVAL_ANALYSIS_PROMPT = """
Analyze user response to a preview.

🗨️ Response: {user_response}

Return intent JSON:
{{
  "intent": "approve|reject|modify",
  "confidence": 0–1,
  "changes_requested": "text if any"
}}

Return JSON only.
"""

ENTITY_ANALYSIS_PROMPT = """
Analyze what entities are relevant.

📦 Entities: {entities_summary}
🗣 Request: {user_request}

Return JSON:
{{
  "relevant_domains": ["light"],
  "relevant_areas": ["living_room"],
  "needs_detailed_list": true,
  "reasoning": "brief reason"
}}

JSON only.
"""

CLARIFICATION_RESPONSE_ANALYSIS_PROMPT = """
Analyze user's response to a clarification question.

📦 Available Entities: {entities}
📍 Available Areas: {areas}
🗣 Original Request: {original_request}
❓ Clarification Question: {clarification_question}
💬 User Response: {user_response}

🎯 Task: Determine what the user selected/specified in their response.

⚠️ CRITICAL: Use ONLY exact entity IDs from the entities list above.

Return JSON:
{{
  "understood_selection": {{
    "entity_id": "exact_entity_id_if_selected",
    "action": "turn_on|turn_off|open|close",
    "area": "exact_area_id", 
    "time": "specific_time_if_mentioned",
    "description": "what_user_said"
  }},
  "needs_more_clarification": true/false,
  "ready_for_automation": true/false,
  "next_missing_info": ["entity", "time", "conditions"]
}}

Only return JSON.
"""

# JSON Schemas for OpenAI structured responses
ANALYSIS_JSON_SCHEMA = {
    "name": "analysis_response",
    "description": "Analysis of user automation request",
    "schema": {
        "type": "object",
        "properties": {
            "is_automation_request": {
                "type": "boolean",
                "description": "Whether this is an automation request"
            },
            "language": {
                "type": "string",
                "description": "Detected language code (e.g., 'he', 'en')"
            },
            "understood": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "entity_type": {"type": "string"},
                    "area": {"type": "string"},
                    "time": {"type": "string"},
                    "conditions": {"type": "string"}
                }
            },
            "missing_info": {
                "type": "array",
                "items": {"type": "string"}
            },
            "ambiguous_entities": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "needs_clarification": {
                "type": "boolean"
            }
        },
        "required": ["is_automation_request", "language", "needs_clarification"],
        "additionalProperties": False
    }
}

INTENT_ANALYSIS_JSON_SCHEMA = {
    "name": "intent_analysis",
    "description": "Analysis of user's intent from their response to automation preview",
    "schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["approve", "reject", "modify"],
                "description": "User's intent"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Confidence level (0-1)"
            },
            "changes_requested": {
                "type": "string",
                "description": "Specific changes mentioned if intent is modify"
            }
        },
        "required": ["intent", "confidence"],
        "additionalProperties": False
    }
} 
# JSON Schema for entity analysis
ENTITY_ANALYSIS_JSON_SCHEMA = {
    "name": "entity_analysis",
    "description": "Analysis of what entities are needed for the user request",
    "schema": {
        "type": "object",
        "properties": {
            "relevant_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of entity domains needed (light, sensor, etc.)"
            },
            "relevant_areas": {
                "type": "array", 
                "items": {"type": "string"},
                "description": "List of area IDs needed"
            },
            "needs_detailed_list": {
                "type": "boolean",
                "description": "Whether detailed entity list is needed"
            },
            "reasoning": {
                "type": "string",
                "description": "Explanation of the analysis"
            }
        },
        "required": ["relevant_domains", "relevant_areas", "needs_detailed_list", "reasoning"],
        "additionalProperties": False
    }
} 
CLARIFICATION_RESPONSE_JSON_SCHEMA = {
    "name": "clarification_response_analysis",
    "description": "Analysis of user's response to clarification question",
    "schema": {
        "type": "object",
        "properties": {
            "understood_selection": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                    "action": {"type": "string"},
                    "area": {"type": "string"},
                    "time": {"type": "string"},
                    "description": {"type": "string"}
                }
            },
            "needs_more_clarification": {
                "type": "boolean",
                "description": "Whether more clarification is needed"
            },
            "ready_for_automation": {
                "type": "boolean",
                "description": "Whether we have enough info to create automation"
            },
            "next_missing_info": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What information is still missing"
            }
        },
        "required": ["understood_selection", "needs_more_clarification", "ready_for_automation"],
        "additionalProperties": False
    }
} 

CONVERSATION_MANAGEMENT_PROMPT = """
You are managing a conversation for Home Assistant automation creation.

📦 Available Entities: {entities}
📍 Available Areas: {areas}
🗣 User Message: {user_message}
📜 Conversation History: {conversation_history}
🎯 Context: {context}

🧠 Your Task: Analyze the current state and decide what to do next.

⚠️ CRITICAL: Use ONLY exact entity IDs from the entities list above.

Analyze the conversation and return JSON:
{{
  "conversation_type": "automation|general|help",
  "language": "he|en",
  "next_action": "ask_clarification|show_preview|create_automation|provide_info|handle_approval",
  "user_intent": {{
    "wants_automation": true/false,
    "approval_response": "approve|reject|modify|unclear",
    "entity_selection": "exact_entity_id_if_mentioned",
    "modification_request": "what_user_wants_to_change"
  }},
  "response_needed": {{
    "type": "question|preview|success|info|error",
    "content": "what_to_say_to_user",
    "entities_to_mention": ["entity1", "entity2"],
    "missing_info": ["entity", "time", "conditions"]
  }},
  "ready_to_proceed": true/false,
  "automation_details": {{
    "action": "turn_on|turn_off|open|close", 
    "entity_id": "exact_entity_id",
    "area": "exact_area_id",
    "time": "specific_time",
    "conditions": "any_conditions"
  }}
}}

Only return JSON.
"""

CONVERSATION_MANAGEMENT_JSON_SCHEMA = {
    "name": "conversation_management",
    "description": "Complete conversation management analysis",
    "schema": {
        "type": "object",
        "properties": {
            "conversation_type": {
                "type": "string",
                "enum": ["automation", "general", "help"],
                "description": "Type of conversation"
            },
            "language": {
                "type": "string",
                "enum": ["he", "en"],
                "description": "Detected language"
            },
            "next_action": {
                "type": "string", 
                "enum": ["ask_clarification", "show_preview", "create_automation", "provide_info", "handle_approval"],
                "description": "What to do next"
            },
            "user_intent": {
                "type": "object",
                "properties": {
                    "wants_automation": {"type": "boolean"},
                    "approval_response": {"type": "string", "enum": ["approve", "reject", "modify", "unclear"]},
                    "entity_selection": {"type": "string"},
                    "modification_request": {"type": "string"}
                }
            },
            "response_needed": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["question", "preview", "success", "info", "error"]},
                    "content": {"type": "string"},
                    "entities_to_mention": {"type": "array", "items": {"type": "string"}},
                    "missing_info": {"type": "array", "items": {"type": "string"}}
                }
            },
            "ready_to_proceed": {"type": "boolean"},
            "automation_details": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "area": {"type": "string"},
                    "time": {"type": "string"},
                    "conditions": {"type": "string"}
                }
            }
        },
        "required": ["conversation_type", "language", "next_action", "user_intent", "response_needed", "ready_to_proceed"],
        "additionalProperties": False
    }
} 