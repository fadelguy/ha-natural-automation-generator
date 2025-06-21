"""Config flow for Natural Automation Generator integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_API_KEY,
    CONF_LLM_PROVIDER,
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    GEMINI_MODELS,
    OPENAI_MODELS,
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LLM_PROVIDER, default=PROVIDER_OPENAI): vol.In([PROVIDER_OPENAI]),
        vol.Required(CONF_API_KEY): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    provider = data[CONF_LLM_PROVIDER]
    api_key = data[CONF_API_KEY]
    
    # Test the API connection
    if provider == PROVIDER_OPENAI:
        await _test_openai_connection(api_key)
    else:
        raise CannotConnect("Unsupported provider")
    
    # Return info that you want to store in the config entry.
    return {
        "title": f"Natural Automation Generator ({provider.upper()})",
        "provider": provider,
    }


async def _test_openai_connection(api_key: str) -> None:
    """Test OpenAI API connection."""
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=api_key)
        # Test with a simple request
        await client.models.list()
    except Exception as err:
        _LOGGER.error("Failed to connect to OpenAI: %s", err)
        raise CannotConnect from err


async def _test_gemini_connection(api_key: str) -> None:
    """Test Gemini API connection."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        # Test with a simple request
        models = genai.list_models()
        list(models)  # Force evaluation
    except Exception as err:
        _LOGGER.error("Failed to connect to Gemini: %s", err)
        raise CannotConnect from err


class NaturalAutomationGeneratorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Natural Automation Generator."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Set default model based on provider
            provider = user_input[CONF_LLM_PROVIDER]
            if provider == PROVIDER_OPENAI:
                user_input[CONF_MODEL] = OPENAI_MODELS[0]  # gpt-4o
            # elif provider == PROVIDER_GEMINI:
            #     user_input[CONF_MODEL] = GEMINI_MODELS[0]  # gemini-1.5-flash
            
            # Set default values
            user_input[CONF_MAX_TOKENS] = DEFAULT_MAX_TOKENS
            user_input[CONF_TEMPERATURE] = DEFAULT_TEMPERATURE
            
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> NaturalAutomationGeneratorOptionsFlow:
        """Create the options flow."""
        return NaturalAutomationGeneratorOptionsFlow(config_entry)


class NaturalAutomationGeneratorOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Natural Automation Generator."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        provider = self.config_entry.data[CONF_LLM_PROVIDER]
        available_models = OPENAI_MODELS  # Only OpenAI supported for now
        
        if user_input is not None:
            # If API key was changed, validate it and update config entry
            if CONF_API_KEY in user_input and user_input[CONF_API_KEY] != self.config_entry.data.get(CONF_API_KEY):
                try:
                    await _test_openai_connection(user_input[CONF_API_KEY])
                    # Update the config entry data with new API key
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data={**self.config_entry.data, CONF_API_KEY: user_input[CONF_API_KEY]}
                    )
                except CannotConnect:
                    return self.async_show_form(
                        step_id="init",
                        data_schema=options_schema,
                        errors={"base": "cannot_connect"}
                    )
            
            # Remove API key from options since it's stored in data
            options_data = {k: v for k, v in user_input.items() if k != CONF_API_KEY}
            return self.async_create_entry(title="", data=options_data)

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY,
                    default=self.config_entry.data.get(CONF_API_KEY, "")
                ): str,
                vol.Required(
                    CONF_MODEL,
                    default=self.config_entry.options.get(
                        CONF_MODEL, self.config_entry.data.get(CONF_MODEL)
                    ),
                ): vol.In(available_models),
                vol.Required(
                    CONF_MAX_TOKENS,
                    default=self.config_entry.options.get(
                        CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=100, max=4000)),
                vol.Required(
                    CONF_TEMPERATURE,
                    default=self.config_entry.options.get(
                        CONF_TEMPERATURE, DEFAULT_TEMPERATURE
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth.""" 