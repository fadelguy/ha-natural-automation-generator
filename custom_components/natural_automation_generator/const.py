"""Constants for the Natural Automation Generator integration."""

# Basic integration info
DOMAIN = "natural_automation_generator"
NAME = "Natural Automation Generator"
VERSION = "2.1.4"

# Configuration and services
DEFAULT_NAME = NAME
SERVICE_GENERATE_AUTOMATION = "generate_automation"

# Conversation flow steps
STEP_ANALYSIS = "analysis"
STEP_CLARIFICATION = "clarification"
STEP_PREVIEW = "preview"
STEP_AWAITING_APPROVAL = "awaiting_approval"
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
- Use only existing entities and areas
- Output a valid YAML object (no list)
- Include: id, alias, triggers, actions
- Use plural keys: triggers, actions, conditions
- Format correctly with indentation
- Use exact entity IDs
- id: 8–12 lowercase characters, no spaces

📦 Entities:
{entities}
📍 Areas:
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

Return YAML only.
"""

ANALYSIS_PROMPT_TEMPLATE = """
You classify user requests.

📦 Entities: {entities}
📍 Areas: {areas}
🗣 User: {user_request}

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
User asked a general question.

🗣 Request: {user_request}
🌐 Language: {language}
📦 Entities: {entities}
📍 Areas: {areas}

Respond helpfully in the user's language:
- Explain automation features
- List devices (if requested)
- Use emojis and formatting

Return response text only.
"""

SUCCESS_RESPONSE_PROMPT = """
Automation created successfully.

🌐 Language: {language}
📝 Name: {automation_name}
📄 Description: {description}
🧾 YAML:
{yaml_config}

Respond positively in user's language with:
1. Confirmation
2. Name & description
3. YAML shown nicely
4. State it's saved and active

Return message only.
"""

CANCELLATION_RESPONSE_PROMPT = """
User cancelled automation.

🌐 Language: {language}

Acknowledge the cancellation, offer to restart anytime. Friendly tone.

Return message only.
"""

ERROR_RESPONSE_PROMPT = """
Error occurred in automation creation.

🌐 Language: {language}
⚠️ Context: {context}

Explain there's an error without technical details. Offer helpful next steps.

Return message only.
"""

CLARIFICATION_PROMPT_TEMPLATE = """
Ask user a clarifying question based on analysis.

🌐 Language: {language}
🗣 Request: {original_request}
📊 Analysis: {analysis_results}

Use friendly formatting with emojis.
Examples:
- Multiple entities ➜ list with names & IDs
- Time ➜ ⏰ Morning / Noon / Evening / Night
- Trigger ➜ 🎯 Options like motion/time/sun

Return question only.
"""

PREVIEW_PROMPT_TEMPLATE = """
Create a preview of the planned automation.

🌐 Language: {language}
📋 Info: {context}
📦 Entities: {entities}
📍 Areas: {areas}

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
