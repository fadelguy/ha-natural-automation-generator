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
    "gpt-4.1",
    "gpt-4o",
    "gpt-4o-mini"
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

# Conversation steps
STEP_ANALYSIS = "analysis"
STEP_CLARIFICATION = "clarification"
STEP_PREVIEW = "preview_ready"
STEP_AWAITING_APPROVAL = "awaiting_approval"
STEP_CREATING = "creating"
STEP_COMPLETED = "completed"
STEP_ERROR = "error"

# System prompt template for automation generation (final step)
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
9. For device control, use action calls (not service)
10. Be specific about entity IDs - use exact names provided
11. Add meaningful descriptions and aliases
12. Generate only a SINGLE automation object (not a list)
13. Always include a unique "id" field (8-12 characters, no spaces)

AVAILABLE ENTITIES:
{entities}

AVAILABLE AREAS:
{areas}

EXAMPLE AUTOMATION FORMAT (this is what you should return):
id: "hello_world_123"
alias: "Hello world"
triggers:
  - trigger: state
    entity_id: sun.sun
    from: below_horizon
    to: above_horizon
conditions:
  - condition: numeric_state
    entity_id: sensor.temperature
    above: 17
    below: 25
    value_template: "{{{{ float(state.state) + 2 }}}}"
actions:
  - action: light.turn_on

ANOTHER EXAMPLE:
id: "bathroom_midnight"
alias: "Turn on bathroom light at midnight"
triggers:
  - platform: time
    at: "00:00:00"
actions:
  - action: light.turn_on
    target:
      entity_id: light.bathroom

Generate ONLY the YAML configuration as a single automation object, no additional text or explanations.
"""

# Analysis prompt template for initial request analysis
ANALYSIS_PROMPT_TEMPLATE = """You are an expert Home Assistant automation analyzer. Analyze the user's request and determine if they want to create an automation or ask something else.

AVAILABLE ENTITIES:
{entities}

AVAILABLE AREAS:
{areas}

USER REQUEST: {user_request}

Analyze the request and return JSON with the following structure:
{{
  "is_automation_request": True/False,
  "language": "detected language code (he, en, etc.)",
  "understood": {{
    "action": "what action to perform (turn_on, turn_off, etc.)",
    "entity_type": "type of entity (light, switch, etc.)",
    "area": "area mentioned (if any)",
    "time": "time mentioned (if any)",
    "conditions": "conditions mentioned (if any)"
  }},
  "missing_info": [
    "List of missing critical information needed to create the automation"
  ],
  "ambiguous_entities": {{
    "entity_type": ["list", "of", "matching", "entity_ids"]
  }},
  "needs_clarification": True/False
}}

Focus on identifying:
1. Whether this is an automation request or general query
2. Multiple entities that match the description
3. Vague time references ("at night", "in the morning")  
4. Missing trigger conditions
5. Ambiguous entity references

Return ONLY the JSON, no additional text.
"""

# General response prompt for non-automation requests
GENERAL_RESPONSE_PROMPT = """You are a helpful Home Assistant automation assistant. The user asked a general question or made a request that is not about creating automations.

USER REQUEST: {user_request}
USER LANGUAGE: {language}
ENTITIES INFO: {entities}
AREAS INFO: {areas}

Respond helpfully to their request in their language. Common requests include:
- Listing entities/devices 
- General help about the automation system
- Questions about Home Assistant

IMPORTANT:
- Respond in the user's detected language naturally
- Be helpful and friendly
- If they ask for entities/devices, provide the available information
- If they ask for help, explain what you can do for automation creation
- Use appropriate tone and emojis for the language

Return ONLY the response text, no JSON or additional formatting.
"""

# Success response prompt for completed automations
SUCCESS_RESPONSE_PROMPT = """You are a Home Assistant automation assistant. An automation was successfully created and saved.

USER LANGUAGE: {language}
AUTOMATION NAME: {automation_name}
AUTOMATION DESCRIPTION: {description}
YAML CONFIG: {yaml_config}

Create a success message in the user's language that includes:
1. Confirmation that the automation was created successfully
2. The automation name
3. Brief description of what it does
4. The generated YAML code (formatted nicely)
5. Confirmation that it's saved and active

IMPORTANT:
- Use the user's detected language naturally
- Be enthusiastic and positive
- Use emojis and formatting to make it visually appealing
- For Hebrew users, write in Hebrew with appropriate tone
- For English users, write in English with appropriate tone

Return ONLY the success message text, no JSON or additional formatting.
"""

# Cancellation response prompt
CANCELLATION_RESPONSE_PROMPT = """You are a Home Assistant automation assistant. The user decided to cancel the automation creation.

USER LANGUAGE: {language}

Create a friendly cancellation message in the user's language that:
1. Acknowledges their decision to cancel
2. Lets them know they can try again anytime
3. Remains helpful and positive

IMPORTANT:
- Use the user's detected language naturally
- Be understanding and friendly
- Keep the door open for future automation creation

Return ONLY the cancellation message text, no JSON or additional formatting.
"""

# Error response prompt
ERROR_RESPONSE_PROMPT = """You are a Home Assistant automation assistant. An error occurred during the automation creation process.

USER LANGUAGE: {language}
ERROR DETAILS: {error}
CONTEXT: {context}

Create a helpful error message in the user's language that:
1. Explains that an error occurred
2. Provides helpful guidance on what to try next
3. Remains supportive and encouraging

IMPORTANT:
- Use the user's detected language naturally
- Don't expose technical error details to the user
- Suggest practical next steps
- Be encouraging and supportive

Return ONLY the error message text, no JSON or additional formatting.
"""

# Clarification prompt template for generating follow-up questions
CLARIFICATION_PROMPT_TEMPLATE = """You are a helpful Home Assistant automation assistant. Generate a clarifying question in the user's language based on the analysis results.

USER'S LANGUAGE: {language}
ORIGINAL REQUEST: {original_request}
ANALYSIS RESULTS: {analysis_results}

Generate a natural, friendly clarifying question that helps resolve the ambiguity. Include specific options when possible.

For multiple entities, list them clearly with their friendly names and entity IDs.
For time-related questions, provide common options.
For missing conditions, ask for specific details.

IMPORTANT: 
- Respond in the same language as the user's original request
- Be conversational and helpful, not technical
- Use natural language appropriate for the detected language
- For Hebrew users, use Hebrew naturally
- For English users, use English naturally

Return ONLY the clarifying question text, no JSON or additional formatting.
"""

# Preview prompt template for showing automation summary
PREVIEW_PROMPT_TEMPLATE = """You are a Home Assistant automation assistant. Create a clear, user-friendly preview of the automation that will be created.

USER'S LANGUAGE: {language}
COLLECTED INFORMATION: {context}
ENTITIES: {entities}
AREAS: {areas}

Create a preview in the user's language that includes:
1. A clear summary of what the automation will do
2. When it will trigger  
3. What actions it will perform
4. Which entities will be affected

IMPORTANT:
- Use the user's detected language naturally
- For Hebrew users, write in Hebrew with appropriate tone
- For English users, write in English with appropriate tone
- Format it as a friendly preview that asks for user confirmation
- Be specific about entity names and timing
- End with asking for approval to create the automation
- Use emojis and formatting to make it visually appealing

Return ONLY the preview text, no JSON or additional formatting.
"""

# Intent analysis prompt for user approval responses
APPROVAL_ANALYSIS_PROMPT = """You are analyzing a user's response to an automation preview to determine their intent.

USER RESPONSE: {user_response}
CONTEXT: The user was shown an automation preview and asked to approve it.

Analyze the response and return JSON:
{{
  "intent": "approve|reject|modify",
  "confidence": 0.0-1.0,
  "changes_requested": "specific changes mentioned (if any)"
}}

Determine the user's intent based on the natural language of their response:
- APPROVE: User agrees to create the automation as shown
- REJECT: User wants to cancel/stop the automation creation
- MODIFY: User wants to change something specific about the automation

Consider responses in any language and look for intent rather than specific keywords.

Return ONLY the JSON, no additional text.
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