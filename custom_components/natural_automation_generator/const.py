"""Constants for the Natural Automation Generator integration."""

# Basic integration info
DOMAIN = "natural_automation_generator"
NAME = "Natural Automation Generator"
VERSION = "2.1.4"

# Configuration and services
DEFAULT_NAME = "Natural Automation Generator"
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

# Gemini specific defaults (much higher token limit)
GEMINI_DEFAULT_MAX_TOKENS = 4000

# OpenAI Models
OPENAI_MODELS = [
    "gpt-4.1",
    "gpt-4o",
    "gpt-4o-mini"
]

# Gemini Models (New 2.5 series only)
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro"
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

⚠️ IMPORTANT: The entities listed above are the ONLY entities that exist in this system.
DO NOT suggest or reference entities that are not in the list above.
If the user mentions "living room light" - check the EXACT entity IDs available (like light.living_room_big, light.living_room_small).
NEVER assume entity names like "light.living_room_main" or "light.living_room_accent" - use only what's listed!

USER REQUEST: {user_request}

CRITICAL: Only classify as automation request if the user explicitly wants to CREATE AN AUTOMATION or AUTOMATE something.

AUTOMATION REQUESTS include:
- "Turn on the lights when I come home"
- "Close the blinds at sunset"
- "תדליק את האור במטבח" (Turn on kitchen light)
- "Create automation to..."
- "I want to automate..."
- Requests with triggers (when/if) and actions (then/do)

NOT AUTOMATION REQUESTS include:
- General questions: "How can I help?", "What can you do?"
- Status requests: "What lights are on?", "Show me devices"
- Help requests: "Help me", "I need assistance"
- General greetings or conversation starters

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
1. Whether this is an automation request or general query (BE STRICT!)
2. Multiple entities that match the description - USE ONLY ENTITY IDs FROM THE LIST ABOVE
3. Vague time references ("at night", "in the morning")  
4. Missing trigger conditions
5. Ambiguous entity references - but suggest only entities that actually exist

Return ONLY the JSON, no additional text.
"""

# General response prompt for non-automation requests
GENERAL_RESPONSE_PROMPT = """You are a helpful Home Assistant automation assistant. The user asked a general question or made a request that is not about creating automations.

USER REQUEST: {user_request}
USER LANGUAGE: {language}
ENTITIES INFO: {entities}
AREAS INFO: {areas}

Analyze the user's request and respond appropriately:

FOR ENTITY/DEVICE LISTING REQUESTS:
If the user is asking to see their devices/entities/sensors/lights/etc, provide a comprehensive list using the ENTITIES INFO provided. Format it nicely with:
- Overview of the system
- Detailed entity information organized by type
- Helpful tips on how to use these entities for automations

FOR GENERAL HELP QUESTIONS ("How can I assist?", "What can you do?"):
- Explain that you can help create Home Assistant automations
- Give examples: "I can help you create automations like turning on lights when you arrive home, closing blinds at sunset, etc."
- Invite them to describe what they want to automate

FOR CAPABILITY QUESTIONS:
- Explain your automation creation capabilities
- Give concrete examples of automations you can create
- Ask what they would like to automate

IMPORTANT:
- Respond in the user's detected language naturally
- Be helpful and friendly 
- Use appropriate tone and emojis for the language
- For Hebrew: Write in Hebrew naturally
- For English: Write in English naturally
- When showing entities, make it visually appealing with emojis and formatting
- Always include helpful tips on how to use the information for automations

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

⚠️ CRITICAL: Use ONLY the exact entity IDs from the system. DO NOT invent entity names!

USER'S LANGUAGE: {language}
ORIGINAL REQUEST: {original_request}
ANALYSIS RESULTS: {analysis_results}

Generate a natural, friendly clarifying question that helps resolve the ambiguity. Format it beautifully and user-friendly:

FOR MULTIPLE ENTITIES - Use this format:
[Question asking which device they want] 💡

🔹 **[Friendly Name 1]** (`[entity_id]`)
🔹 **[Friendly Name 2]** (`[entity_id]`)
🔹 **[Friendly Name 3]** (`[entity_id]`)

FOR TIME-RELATED QUESTIONS - Use this format:
[Question asking when they want the action] ⏰

🕐 **[Morning option]** (6:00-10:00)
🕐 **[Noon option]** (12:00-16:00)  
🕐 **[Evening option]** (18:00-22:00)
🕐 **[Night option]** (22:00-6:00)

FOR CONDITIONS/TRIGGERS - Use this format:
[Question asking what should trigger the automation] 🎯

🔸 **[Motion sensor option]**
🔸 **[Door opening option]**
🔸 **[Time-based option]**
🔸 **[Sun state option]**

IMPORTANT: 
- Respond in the same language as the user's original request
- Use emojis and formatting to make it visually appealing
- Be conversational and helpful, not technical
- For Hebrew users, use Hebrew naturally with RTL formatting
- For English users, use English naturally
- Make entity IDs smaller/secondary with backticks
- Use bold for friendly names

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

# Entity analysis prompt for smart filtering (ultra-compact to avoid MAX_TOKENS)
ENTITY_ANALYSIS_PROMPT = """Analyze request and return JSON:

ENTITIES: {entities_summary}
REQUEST: {user_request}

Return:
{{
  "relevant_domains": ["light"],
  "relevant_areas": ["living_room"], 
  "needs_detailed_list": true,
  "reasoning": "brief explanation"
}}

Examples:
- "lights in living room" → {{"relevant_domains":["light"],"relevant_areas":["living_room"],"needs_detailed_list":true,"reasoning":"need lights"}}
- "what can you do" → {{"relevant_domains":[],"relevant_areas":[],"needs_detailed_list":false,"reasoning":"general help"}}

JSON only:"""

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