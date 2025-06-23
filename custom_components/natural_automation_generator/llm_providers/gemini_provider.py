"""Google Gemini LLM Provider for Natural Automation Generator."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import yaml

from ..const import CONF_API_KEY, CONF_MAX_TOKENS, CONF_MODEL, CONF_TEMPERATURE
from .base import BaseLLMProvider

_LOGGER = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation."""

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "Gemini"

    async def _initialize_client(self) -> None:
        """Initialize the Gemini client."""
        try:
            # Import google.genai in executor to avoid blocking the event loop
            def _import_and_create_client():
                """Import genai and create client in executor."""
                try:
                    _LOGGER.debug("Importing google.genai library...")
                    from google import genai
                    _LOGGER.debug("Successfully imported google.genai")
                    
                    api_key = self._get_config_value(CONF_API_KEY)
                    if not api_key:
                        raise ValueError("Gemini API key not configured")
                    
                    _LOGGER.debug("Creating Gemini client with API key (length: %d)", len(api_key))
                    client = genai.Client(api_key=api_key)
                    _LOGGER.debug("Successfully created Gemini client: %s", type(client))
                    return client
                except ImportError as err:
                    _LOGGER.error("Google GenAI library not installed: %s", err)
                    raise
                except Exception as err:
                    _LOGGER.error("Failed to initialize Gemini client: %s", err)
                    raise
            
            # Run the import and client creation in executor
            self._client = await self.hass.async_add_executor_job(_import_and_create_client)
            
            _LOGGER.debug("Gemini client initialized successfully")
        except Exception as err:
            _LOGGER.error("Failed to initialize Gemini client: %s", err)
            raise

    async def generate_automation(self, system_prompt: str, user_description: str) -> str:
        """Generate automation YAML from natural language description."""
        await self._ensure_client_initialized()
        
        try:
            _LOGGER.debug("Generating automation with Gemini")
            
            # Combine system prompt and user description
            full_prompt = f"{system_prompt}\n\nUser Request: {user_description}"
            
            # Get model configuration
            model_name = self._get_config_value(CONF_MODEL, "gemini-2.5-flash")
            max_tokens = self._get_config_value(CONF_MAX_TOKENS, 1500)
            temperature = self._get_config_value(CONF_TEMPERATURE, 0.1)
            
            # Generate content using new SDK with optimized settings (in executor)
            def _generate_content():
                """Generate content in executor to avoid blocking."""
                try:
                    config = {
                        "max_output_tokens": max_tokens,
                        "temperature": temperature,
                        "top_k": 1,  # Greedy decoding for deterministic automation generation
                        "top_p": 0.1,  # Low nucleus sampling for focused, accurate results
                        "stop_sequences": ["```", "---"]  # Stop at common YAML delimiters
                    }
                    _LOGGER.debug("Calling Gemini API for automation with model: %s, config: %s", model_name, config)
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                        config=config
                    )
                    _LOGGER.debug("Raw Gemini API automation response: %s", response)
                    return response
                except Exception as api_err:
                    _LOGGER.error("Gemini API automation call failed: %s", api_err)
                    raise
            
            response = await self.hass.async_add_executor_job(_generate_content)
            
            _LOGGER.debug("Gemini automation response object: %s", response)
            _LOGGER.debug("Gemini automation response text: %s", getattr(response, 'text', 'No text attribute'))
            
            if not hasattr(response, 'text') or not response.text:
                raise ValueError(f"Empty response from Gemini. Response object: {response}")
            
            # Extract YAML from the response
            yaml_config = self._extract_yaml_from_response(response.text)
            
            # Validate YAML
            self._validate_yaml(yaml_config)
            
            _LOGGER.debug("Successfully generated automation YAML")
            return yaml_config
            
        except Exception as err:
            _LOGGER.error("Gemini automation generation failed: %s", err)
            raise

    def _extract_yaml_from_response(self, response: str) -> str:
        """Extract YAML configuration from LLM response."""
        # Look for YAML code blocks
        yaml_match = re.search(r'```(?:yaml|yml)?\s*\n(.*?)\n```', response, re.DOTALL)
        if yaml_match:
            return yaml_match.group(1).strip()
        
        # Look for automation structure without code blocks
        if "alias:" in response and ("trigger:" in response or "action:" in response):
            # Clean up the response to extract just the YAML part
            lines = response.split('\n')
            yaml_lines = []
            in_yaml = False
            
            for line in lines:
                if line.strip().startswith('alias:') or line.strip().startswith('-'):
                    in_yaml = True
                elif in_yaml and line.strip() == '':
                    continue
                elif in_yaml and not line.startswith(' ') and ':' not in line:
                    break
                
                if in_yaml:
                    yaml_lines.append(line)
            
            if yaml_lines:
                return '\n'.join(yaml_lines)
        
        # If no clear YAML structure found, return the response as-is
        # and let the validation catch any issues
        return response.strip()

    def _validate_yaml(self, yaml_content: str) -> None:
        """Validate that the generated content is valid YAML."""
        try:
            parsed = yaml.safe_load(yaml_content)
            if not isinstance(parsed, dict):
                raise ValueError("YAML must represent a dictionary/object")
            
            # Check for required automation fields
            required_fields = ["alias", "trigger", "action"]
            missing_fields = [field for field in required_fields if field not in parsed]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        except yaml.YAMLError as err:
            raise ValueError(f"Invalid YAML format: {err}") from err

    def _convert_schema_to_gemini_format(self, json_schema: dict) -> dict:
        """Convert JSON schema to Gemini's response schema format."""
        if not json_schema:
            return None
            
        # Extract the actual schema from OpenAI function format if needed
        if "schema" in json_schema:
            schema = json_schema["schema"]
        else:
            schema = json_schema
            
        def convert_type(schema_type: str) -> str:
            """Convert JSON schema types to Gemini types."""
            type_mapping = {
                "string": "STRING",
                "number": "NUMBER", 
                "integer": "INTEGER",
                "boolean": "BOOLEAN",
                "array": "ARRAY",
                "object": "OBJECT"
            }
            return type_mapping.get(schema_type, "STRING")
        
        def convert_properties(properties: dict) -> dict:
            """Recursively convert properties."""
            converted = {}
            for key, prop in properties.items():
                converted_prop = {"type": convert_type(prop.get("type", "string"))}
                
                if "description" in prop:
                    converted_prop["description"] = prop["description"]
                
                if "enum" in prop:
                    converted_prop["enum"] = prop["enum"]
                
                if prop.get("type") == "array" and "items" in prop:
                    converted_prop["items"] = convert_schema_part(prop["items"])
                
                if prop.get("type") == "object":
                    # Handle both properties and additionalProperties
                    if "properties" in prop:
                        converted_prop["properties"] = convert_properties(prop["properties"])
                        if "required" in prop:
                            converted_prop["required"] = prop["required"]
                    elif "additionalProperties" in prop:
                        # For additionalProperties, we'll skip this field entirely
                        # since Gemini doesn't support dynamic object properties well
                        _LOGGER.debug(f"Skipping field '{key}' with additionalProperties for Gemini compatibility")
                        continue
                    else:
                        # Object without properties - skip it
                        _LOGGER.debug(f"Skipping object field '{key}' without defined properties")
                        continue
                
                converted[key] = converted_prop
            
            return converted
        
        def convert_schema_part(schema_part: dict) -> dict:
            """Convert a schema part recursively."""
            converted = {"type": convert_type(schema_part.get("type", "string"))}
            
            if "description" in schema_part:
                converted["description"] = schema_part["description"]
            
            if "enum" in schema_part:
                converted["enum"] = schema_part["enum"]
            
            if schema_part.get("type") == "array" and "items" in schema_part:
                converted["items"] = convert_schema_part(schema_part["items"])
            
            if schema_part.get("type") == "object":
                # Handle both properties and additionalProperties
                if "properties" in schema_part:
                    converted["properties"] = convert_properties(schema_part["properties"])
                    if "required" in schema_part:
                        converted["required"] = schema_part["required"]
                elif "additionalProperties" in schema_part:
                    # For additionalProperties, convert to STRING type instead
                    _LOGGER.debug("Converting object with additionalProperties to STRING type for Gemini")
                    converted["type"] = "STRING"
                    converted["description"] = "JSON string containing dynamic properties"
                else:
                    # Object without properties - convert to STRING
                    _LOGGER.debug("Converting object without properties to STRING type for Gemini")
                    converted["type"] = "STRING"
                    converted["description"] = "JSON string representation"
            
            return converted
        
        return convert_schema_part(schema)

    async def generate_response(self, prompt: str, json_schema: dict = None) -> str:
        """Generate a text response from the LLM."""
        await self._ensure_client_initialized()
        
        try:
            _LOGGER.debug("Generating response with Gemini")
            
            # Get model configuration
            model_name = self._get_config_value(CONF_MODEL, "gemini-2.5-flash")
            max_tokens = self._get_config_value(CONF_MAX_TOKENS, 1500)
            temperature = self._get_config_value(CONF_TEMPERATURE, 0.1)
            
            # Build config
            config = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
                "top_k": 40,  # Default balanced setting for general responses
                "top_p": 0.95  # Default nucleus sampling for diverse but coherent responses
            }
            
            # Add JSON schema if provided
            if json_schema:
                _LOGGER.debug("Using JSON schema for structured output")
                gemini_schema = self._convert_schema_to_gemini_format(json_schema)
                if gemini_schema:
                    config["response_mime_type"] = "application/json"
                    config["response_schema"] = gemini_schema
                    # Adjust parameters for more deterministic JSON output
                    config["top_k"] = 1
                    config["top_p"] = 0.1
            
            # Generate content in executor to avoid blocking
            def _generate_response():
                """Generate response in executor to avoid blocking."""
                try:
                    _LOGGER.debug("Calling Gemini API with model: %s, config: %s", model_name, config)
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    _LOGGER.debug("Raw Gemini API response: %s", response)
                    return response
                except Exception as api_err:
                    _LOGGER.error("Gemini API call failed: %s", api_err)
                    raise
            
            response = await self.hass.async_add_executor_job(_generate_response)
            
            _LOGGER.debug("Gemini response object: %s", response)
            _LOGGER.debug("Gemini response text: %s", getattr(response, 'text', 'No text attribute'))
            
            if not hasattr(response, 'text') or not response.text:
                raise ValueError(f"Empty response from Gemini. Response object: {response}")
            
            _LOGGER.debug("Successfully generated response")
            return response.text.strip()
            
        except Exception as err:
            _LOGGER.error("Gemini response generation failed: %s", err)
            raise 