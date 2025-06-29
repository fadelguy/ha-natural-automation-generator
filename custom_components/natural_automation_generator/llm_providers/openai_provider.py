"""OpenAI LLM Provider for Natural Automation Generator."""
from __future__ import annotations

import logging
import re
from typing import Any

import yaml

try:
    import openai
except ImportError:
    openai = None

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
            if openai is None:
                raise ImportError("OpenAI library not installed")
            
            api_key = self._get_config_value(CONF_API_KEY)
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            
            # Initialize client in executor to avoid blocking operations
            import asyncio
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None, 
                lambda: openai.AsyncOpenAI(api_key=api_key)
            )
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
            
            _LOGGER.debug("Raw OpenAI response: %s", content)
            _LOGGER.debug("Extracted YAML: %s", yaml_config)
            
            # Validate YAML
            self._validate_yaml(yaml_config)
            
            _LOGGER.debug("Successfully generated automation YAML")
            return yaml_config
            
        except Exception as err:
            _LOGGER.error("OpenAI automation generation failed: %s", err)
            raise

    async def generate_response(self, prompt: str, json_schema: dict = None) -> str:
        """Generate a text response from the LLM."""
        await self._ensure_client_initialized()
        
        model = self._get_config_value(CONF_MODEL, "gpt-4o")
        max_tokens = self._get_config_value(CONF_MAX_TOKENS, 1500)
        temperature = self._get_config_value(CONF_TEMPERATURE, 0.1)
        
        try:
            _LOGGER.debug("Generating response with OpenAI model: %s", model)
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            # Add JSON schema if provided
            if json_schema:
                request_params["response_format"] = {
                    "type": "json_schema",
                    "json_schema": json_schema
                }
            else:
                request_params["response_format"] = {"type": "text"}
            
            response = await self._client.chat.completions.create(**request_params)
            
            if not response.choices:
                raise ValueError("No response received from OpenAI")
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            
            _LOGGER.debug("Successfully generated response")
            return content.strip()
            
        except Exception as err:
            _LOGGER.error("OpenAI response generation failed: %s", err)
            raise

    def _extract_yaml_from_response(self, response: str) -> str:
        """Extract YAML configuration from LLM response."""
        _LOGGER.debug("Extracting YAML from response: %s", response[:300] + "..." if len(response) > 300 else response)
        
        # Look for YAML code blocks first
        yaml_match = re.search(r'```(?:yaml|yml)?\s*\n(.*?)\n```', response, re.DOTALL)
        if yaml_match:
            extracted = yaml_match.group(1).strip()
            _LOGGER.debug("Found YAML in code block")
            return extracted
        
        # Check if the response looks like compressed YAML (missing line breaks)
        if "alias:" in response and ("trigger:" in response or "triggers:" in response) and ("action:" in response or "actions:" in response):
            # First, check if it's a list format (starts with -)
            cleaned_response = response.strip()
            if cleaned_response.startswith('-'):
                _LOGGER.debug("Detected list format, extracting first automation")
                # Remove the leading dash and treat as single automation
                cleaned_response = cleaned_response[1:].strip()
            
            # Try to fix compressed YAML by adding line breaks
            fixed_yaml = self._fix_compressed_yaml(cleaned_response)
            if fixed_yaml != cleaned_response:
                _LOGGER.debug("Fixed compressed YAML")
                return fixed_yaml
        
        # Look for automation structure without code blocks
        if "alias:" in response and ("trigger:" in response or "triggers:" in response or "action:" in response or "actions:" in response):
            # Find the start of the YAML (first occurrence of 'alias:')
            alias_start = response.find('alias:')
            if alias_start != -1:
                # Extract everything from 'alias:' onwards
                yaml_part = response[alias_start:].strip()
                
                # Try to clean up the YAML by removing non-YAML text after the automation
                lines = yaml_part.split('\n')
                yaml_lines = []
                yaml_started = False
                
                for line in lines:
                    stripped = line.strip()
                    
                    # Skip empty lines but include them in YAML
                    if not stripped:
                        if yaml_started:
                            yaml_lines.append(line)
                        continue
                    
                    # Check if this looks like YAML
                    yaml_indicators = [
                        stripped.startswith('alias:'),
                        stripped.startswith('trigger:'),
                        stripped.startswith('triggers:'),
                        stripped.startswith('action:'),
                        stripped.startswith('actions:'),
                        stripped.startswith('condition:'),
                        stripped.startswith('conditions:'),
                        stripped.startswith('- '),
                        stripped.startswith('platform:'),
                        stripped.startswith('service:'),
                        stripped.startswith('entity_id:'),
                        stripped.startswith('target:'),
                        ':' in stripped and not stripped.startswith('#'),
                        line.startswith('  ') or line.startswith('    ') or line.startswith('\t')
                    ]
                    
                    is_yaml_line = any(yaml_indicators)
                    
                    if is_yaml_line or yaml_started:
                        yaml_lines.append(line)
                        yaml_started = True
                    elif yaml_started and not is_yaml_line:
                        # We've reached the end of YAML content
                        break
                
                if yaml_lines:
                    extracted = '\n'.join(yaml_lines).strip()
                    _LOGGER.debug("Extracted YAML from automation structure")
                    return extracted
        
        # Last resort - return the whole response and let validation handle it
        _LOGGER.debug("Could not extract YAML properly, returning full response")
        return response.strip()

    def _fix_compressed_yaml(self, yaml_text: str) -> str:
        """Fix compressed YAML by adding proper line breaks and indentation."""
        _LOGGER.debug("Attempting to fix compressed YAML: %s", yaml_text)
        
        # Start with clean input
        fixed = yaml_text.strip()
        
        # Split into key sections using regex to preserve order
        # Look for main keys: alias, trigger, action, condition
        sections = {}
        
        # Extract alias
        alias_match = re.search(r'alias:\s*"([^"]+)"', fixed)
        if alias_match:
            sections['alias'] = alias_match.group(1)
            
        # Extract trigger section
        trigger_match = re.search(r'trigger:\s*-\s*platform:\s*(\w+)(?:\s+at:\s*"([^"]+)")?', fixed)
        if trigger_match:
            platform = trigger_match.group(1)
            at_time = trigger_match.group(2)
            sections['trigger'] = {
                'platform': platform,
                'at': at_time
            }
        
        # Extract action section  
        action_match = re.search(r'action:\s*-\s*service:\s*(\S+)(?:\s+target:\s*entity_id:\s*(\S+))?', fixed)
        if action_match:
            service = action_match.group(1)
            entity_id = action_match.group(2)
            sections['action'] = {
                'service': service,
                'entity_id': entity_id
            }
        
        # Rebuild YAML with proper formatting
        result_lines = []
        
        if 'alias' in sections:
            result_lines.append(f'alias: "{sections["alias"]}"')
            
        if 'trigger' in sections:
            result_lines.append('trigger:')
            result_lines.append(f'  - platform: {sections["trigger"]["platform"]}')
            if sections["trigger"]["at"]:
                result_lines.append(f'    at: "{sections["trigger"]["at"]}"')
                
        if 'action' in sections:
            result_lines.append('action:')
            result_lines.append(f'  - service: {sections["action"]["service"]}')
            if sections["action"]["entity_id"]:
                result_lines.append('    target:')
                result_lines.append(f'      entity_id: {sections["action"]["entity_id"]}')
        
        result = '\n'.join(result_lines)
        
        # If we couldn't parse properly, return original with basic line breaks
        if not result_lines or len(result_lines) < 3:
            _LOGGER.debug("Could not parse sections properly, applying basic formatting")
            # Basic pattern replacement as fallback
            fallback = fixed
            fallback = re.sub(r'\s+trigger:\s*-\s*', '\ntrigger:\n  - ', fallback)
            fallback = re.sub(r'\s+action:\s*-\s*', '\naction:\n  - ', fallback)
            fallback = re.sub(r'\s+platform:\s*', '\n    platform: ', fallback)
            fallback = re.sub(r'\s+service:\s*', '\n    service: ', fallback)
            fallback = re.sub(r'\s+at:\s*', '\n    at: ', fallback)
            fallback = re.sub(r'\s+target:\s*entity_id:\s*', '\n    target:\n      entity_id: ', fallback)
            result = fallback
            
        _LOGGER.debug("Fixed YAML result: %s", result)
        return result

    def _validate_yaml(self, yaml_content: str) -> None:
        """Validate that the generated content is valid YAML."""
        try:
            parsed = yaml.safe_load(yaml_content)
            _LOGGER.debug("Parsed YAML type: %s, content: %s", type(parsed), parsed)
            
            if parsed is None:
                raise ValueError("YAML content is empty or None")
            
            if not isinstance(parsed, dict):
                # If it's a list with one automation, extract the first one
                if isinstance(parsed, list) and len(parsed) == 1 and isinstance(parsed[0], dict):
                    _LOGGER.debug("Got list with single automation, extracting first element")
                    parsed = parsed[0]
                elif isinstance(parsed, list) and len(parsed) > 1:
                    _LOGGER.warning("Got multiple automations, taking the first one")
                    parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else None
                    if parsed is None:
                        raise ValueError("List contains invalid automation objects")
                # If it's a string, try to extract YAML from it
                elif isinstance(parsed, str):
                    _LOGGER.debug("Got string instead of dict, trying to re-extract YAML")
                    # Try to find YAML within the string
                    better_yaml = self._extract_yaml_from_response(parsed)
                    if better_yaml != parsed:
                        return self._validate_yaml(better_yaml)
                
                # Check if we now have a dict after processing
                if not isinstance(parsed, dict):
                    raise ValueError(f"YAML must represent a dictionary/object, got {type(parsed)}: {parsed}")
            
            # Check for required automation fields - support both old and new formats
            # Since we convert trigger->triggers and action->actions in conversation.py
            required_fields = ["alias"]
            triggers_ok = "triggers" in parsed or "trigger" in parsed
            actions_ok = "actions" in parsed or "action" in parsed
            
            missing_fields = []
            if not triggers_ok:
                missing_fields.append("triggers/trigger")
            if not actions_ok:
                missing_fields.append("actions/action")
                
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        except yaml.YAMLError as err:
            raise ValueError(f"Invalid YAML format: {err}") from err 