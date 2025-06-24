"""Constants for the Natural Automation Generator integration."""

# Domain and basic info
DOMAIN = "natural_automation_generator"
NAME = "Natural Automation Generator"
VERSION = "2.3.0"

# Configuration and services
DEFAULT_NAME = NAME
SERVICE_GENERATE_AUTOMATION = "generate_automation"

# Automation filename
AUTOMATIONS_FILE = "automations.yaml"

# Default LLM settings
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL_OPENAI = "gpt-4"
DEFAULT_MODEL_GEMINI = "gemini-2.5-flash"
DEFAULT_MAX_TOKENS = 2000
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

# Unified Conversation Prompt
UNIFIED_CONVERSATION_PROMPT = """# Home Assistant Automation Assistant

You are an expert Home Assistant automation assistant that helps users create, modify, and manage automations through natural conversation.

## Your Role
- **Analyze** user requests in context of the full conversation
- **Create** valid Home Assistant YAML automations
- **Guide** users through the automation creation process
- **Respond** in the user's language (Hebrew/English/etc.)

## Available Resources

### 🏠 Available Entities
```
{entities}
```

### 📍 Available Areas  
```
{areas}
```

### 💬 Conversation History
```
{conversation_history}
```

### 🗣️ Current User Message
```
{user_message}
```

## Critical Rules
- ⚠️ **ONLY use exact entity IDs** from the entities list above
- ⚠️ **Never invent** entity IDs that don't exist
- 🌐 **Always respond** in the same language as the user's request
- 📝 **Generate valid YAML** following Home Assistant format
- 🏷️ **Always add "(Auto Generated)" suffix** to automation alias/name

## YAML Automation Example
```yaml
id: kitchen_light_evening
alias: "Kitchen Light at Evening (Auto Generated)"
description: "Turn on kitchen light at 6 PM daily"
triggers:
  - platform: time
    at: "18:00:00"
conditions: []
actions:
  - service: light.turn_on
    target:
      entity_id: light.kitchen_main
mode: single
```

## Response Instructions
Analyze the conversation and respond appropriately:
- **For automation requests**: Create/update YAML automation
- **For user approvals**: Confirm automation should be saved  
- **For questions/chat**: Provide helpful responses
- **For modifications**: Update existing automation based on feedback
"""

# Unified JSON Schema
UNIFIED_CONVERSATION_JSON_SCHEMA = {
    "name": "conversation_response",
    "description": "Unified response for all conversation types",
    "schema": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Your response to the user"
            },
            "is_confirmed": {
                "type": "boolean", 
                "description": "True if user confirmed to save automation"
            },
            "automation_yaml": {
                "type": ["string", "null"],
                "description": "Complete YAML automation following Home Assistant format",
                "pattern": "^(id:|alias:|description:|triggers:|conditions:|actions:|mode:).*",
                "example": "id: example_auto\nalias: \"Example Automation (Auto Generated)\"\ndescription: \"Example description\"\ntriggers:\n  - platform: time\n    at: \"18:00:00\"\nconditions: []\nactions:\n  - service: light.turn_on\n    target:\n      entity_id: light.example\nmode: single"
            },
            "automation_name": {
                "type": ["string", "null"],
                "description": "Human-readable name of the automation, must end with '(Auto Generated)'",
                "pattern": ".*\\(Auto Generated\\)$",
                "example": "Kitchen Light at Evening (Auto Generated)"
            }
        },
        "required": ["message", "is_confirmed", "automation_yaml", "automation_name"],
        "additionalProperties": False
    }
} 