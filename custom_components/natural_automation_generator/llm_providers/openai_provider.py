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
        if "alias:" in response and "trigger:" in response and "action:" in response:
            # Try to fix compressed YAML by adding line breaks
            fixed_yaml = self._fix_compressed_yaml(response)
            if fixed_yaml != response:
                _LOGGER.debug("Fixed compressed YAML")
                return fixed_yaml
        
        # Look for automation structure without code blocks
        if "alias:" in response and ("trigger:" in response or "action:" in response):
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
                        stripped.startswith('action:'),
                        stripped.startswith('condition:'),
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
        
        # Common patterns that should be on new lines
        patterns = [
            (r'(\w+:)\s*([a-zA-Z])', r'\1\n  \2'),  # key: value -> key:\n  value
            (r'\s+trigger:\s*-', '\ntrigger:\n  -'),  # trigger: - -> trigger:\n  -
            (r'\s+action:\s*-', '\naction:\n  -'),   # action: - -> action:\n  -
            (r'\s+condition:\s*-', '\ncondition:\n  -'),  # condition: - -> condition:\n  -
            (r'\s+platform:\s*(\w+)', r'\n    platform: \1'),  # platform: word -> \n    platform: word
            (r'\s+service:\s*(\S+)', r'\n    service: \1'),   # service: word -> \n    service: word
            (r'\s+entity_id:\s*(\S+)', r'\n      entity_id: \1'),  # entity_id: word -> \n      entity_id: word
            (r'\s+at:\s*"([^"]+)"', r'\n    at: "\1"'),      # at: "time" -> \n    at: "time"
            (r'\s+target:\s*entity_id:', '\n    target:\n      entity_id:'),  # target: entity_id: -> target:\n      entity_id:
        ]
        
        fixed = yaml_text.strip()
        
        # Apply patterns
        for pattern, replacement in patterns:
            fixed = re.sub(pattern, replacement, fixed)
        
        # Clean up extra spaces and ensure proper structure
        lines = fixed.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # Determine proper indentation
            if stripped.startswith('alias:') or stripped.startswith('trigger:') or stripped.startswith('action:') or stripped.startswith('condition:'):
                cleaned_lines.append(stripped)
            elif stripped.startswith('- platform:') or stripped.startswith('- service:'):
                cleaned_lines.append('  ' + stripped)
            elif stripped.startswith('platform:') or stripped.startswith('service:') or stripped.startswith('target:') or stripped.startswith('at:'):
                cleaned_lines.append('    ' + stripped)
            elif stripped.startswith('entity_id:'):
                cleaned_lines.append('      ' + stripped)
            else:
                # Keep original indentation if it looks right
                if line.startswith('  ') or line.startswith('    ') or line.startswith('      '):
                    cleaned_lines.append(line)
                else:
                    cleaned_lines.append('  ' + stripped)
        
        result = '\n'.join(cleaned_lines)
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
            
            # Check for required automation fields
            required_fields = ["alias", "trigger", "action"]
            missing_fields = [field for field in required_fields if field not in parsed]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        except yaml.YAMLError as err:
            raise ValueError(f"Invalid YAML format: {err}") from err 