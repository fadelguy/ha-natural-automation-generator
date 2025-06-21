"""OpenAI LLM Provider for Natural Automation Generator."""
from __future__ import annotations

import logging
import re
from typing import Any

import yaml

from ..const import CONF_API_KEY, CONF_MAX_TOKENS, CONF_MODEL, CONF_TEMPERATURE
from .base import BaseLLMProvider

_LOGGER = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "OpenAI"

    async def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        try:
            import openai
            
            api_key = self._get_config_value(CONF_API_KEY)
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            
            self._client = openai.AsyncOpenAI(api_key=api_key)
            _LOGGER.debug("OpenAI client initialized")
        except ImportError as err:
            _LOGGER.error("OpenAI library not installed: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Failed to initialize OpenAI client: %s", err)
            raise

    async def generate_automation(self, system_prompt: str, user_description: str) -> str:
        """Generate automation YAML from natural language description."""
        await self._ensure_client_initialized()
        
        model = self._get_config_value(CONF_MODEL, "gpt-4o")
        max_tokens = self._get_config_value(CONF_MAX_TOKENS, 1500)
        temperature = self._get_config_value(CONF_TEMPERATURE, 0.1)
        
        try:
            _LOGGER.debug("Generating automation with OpenAI model: %s", model)
            
            response = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_description}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "text"}
            )
            
            if not response.choices:
                raise ValueError("No response received from OpenAI")
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            
            # Extract YAML from the response
            yaml_config = self._extract_yaml_from_response(content)
            
            # Validate YAML
            self._validate_yaml(yaml_config)
            
            _LOGGER.debug("Successfully generated automation YAML")
            return yaml_config
            
        except Exception as err:
            _LOGGER.error("OpenAI automation generation failed: %s", err)
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