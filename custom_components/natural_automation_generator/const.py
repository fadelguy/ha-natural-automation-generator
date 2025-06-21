"""Constants for the Natural Automation Generator integration."""

# Integration domain
DOMAIN = "natural_automation_generator"

# Configuration flow constants
CONF_LLM_PROVIDER = "llm_provider"
CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"

# LLM Providers
PROVIDER_OPENAI = "openai"
PROVIDER_GEMINI = "gemini"

# Default values
DEFAULT_MAX_TOKENS = 1500
DEFAULT_TEMPERATURE = 0.1

# OpenAI Models
OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo"
]

# Gemini Models
GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro"
]

# Service names
SERVICE_CREATE_AUTOMATION = "create_automation"
SERVICE_PREVIEW_AUTOMATION = "preview_automation"
SERVICE_LIST_ENTITIES = "list_entities"

# Service parameters
ATTR_DESCRIPTION = "description"
ATTR_AUTOMATION_CONFIG = "automation_config"
ATTR_PREVIEW_ONLY = "preview_only"
ATTR_AUTOMATION_NAME = "automation_name"
ATTR_YAML_CONFIG = "yaml_config"

# Error messages
ERROR_INVALID_PROVIDER = "Invalid LLM provider specified"
ERROR_API_KEY_REQUIRED = "API key is required"
ERROR_GENERATION_FAILED = "Failed to generate automation"
ERROR_INVALID_YAML = "Generated YAML is invalid"
ERROR_SAVE_FAILED = "Failed to save automation"

# System prompt template
SYSTEM_PROMPT_TEMPLATE = """You are an expert Home Assistant automation generator. Your task is to create valid YAML automation configurations based on natural language descriptions.

IMPORTANT RULES:
1. Always generate valid Home Assistant automation YAML
2. Only use entities that exist in the system
3. Use proper YAML formatting with correct indentation
4. Include all required fields: alias, triggers, actions
5. Use "triggers" (plural) instead of "trigger"
6. Use "actions" (plural) instead of "action" 
7. Use "conditions" (plural) if needed, not "condition"
8. For time-based triggers, use the time platform
9. For device control, use service calls
10. Be specific about entity IDs - use exact names provided
11. Add meaningful descriptions and aliases
12. Generate only a SINGLE automation object (not a list)

AVAILABLE ENTITIES:
{entities}

AVAILABLE AREAS:
{areas}

EXAMPLE AUTOMATION FORMAT:
alias: "Turn on bathroom light at midnight"
triggers:
  - platform: time
    at: "00:00:00"
actions:
  - service: light.turn_on
    target:
      entity_id: light.bathroom
  - delay: "00:10:00"
  - service: light.turn_off
    target:
      entity_id: light.bathroom

Generate ONLY the YAML configuration as a single automation object, no additional text or explanations.
""" 