"""Google Gemini LLM Provider for Natural Automation Generator."""
from __future__ import annotations

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
            import google.generativeai as genai
            
            api_key = self._get_config_value(CONF_API_KEY)
            if not api_key:
                raise ValueError("Gemini API key not configured")
            
            genai.configure(api_key=api_key)
            
            model_name = self._get_config_value(CONF_MODEL, "gemini-1.5-flash")
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=self._get_config_value(CONF_MAX_TOKENS, 1500),
                temperature=self._get_config_value(CONF_TEMPERATURE, 0.1),
                response_mime_type="text/plain"
            )
            
            self._client = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            
            _LOGGER.debug("Gemini client initialized with model: %s", model_name)
        except ImportError as err:
            _LOGGER.error("Google Generative AI library not installed: %s", err)
            raise
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
            
            # Generate content
            response = await self._client.generate_content_async(full_prompt)
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
            
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