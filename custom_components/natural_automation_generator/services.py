"""Services for Natural Automation Generator integration."""
from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol
import yaml
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_AUTOMATION_CONFIG,
    ATTR_AUTOMATION_NAME,
    ATTR_DESCRIPTION,
    ATTR_PREVIEW_ONLY,
    ATTR_YAML_CONFIG,
    DOMAIN,
    SERVICE_CREATE_AUTOMATION,
    SERVICE_LIST_ENTITIES,
    SERVICE_PREVIEW_AUTOMATION,
)
from .coordinator import NaturalAutomationGeneratorCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
CREATE_AUTOMATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DESCRIPTION): cv.string,
        vol.Optional(ATTR_AUTOMATION_NAME): cv.string,
        vol.Optional(ATTR_PREVIEW_ONLY, default=False): cv.boolean,
    }
)

PREVIEW_AUTOMATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DESCRIPTION): cv.string,
    }
)

LIST_ENTITIES_SCHEMA = vol.Schema({})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the Natural Automation Generator integration."""
    
    async def handle_create_automation(call: ServiceCall) -> None:
        """Handle the create automation service call."""
        description = call.data[ATTR_DESCRIPTION]
        automation_name = call.data.get(ATTR_AUTOMATION_NAME)
        preview_only = call.data.get(ATTR_PREVIEW_ONLY, False)
        
        _LOGGER.debug("Creating automation: %s (preview: %s)", description, preview_only)
        
        # Get the first coordinator (assuming single config entry for now)
        coordinators = []
        for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
            if isinstance(coordinator, NaturalAutomationGeneratorCoordinator):
                coordinators.append(coordinator)
        
        if not coordinators:
            raise HomeAssistantError("No Natural Automation Generator configured")
        
        coordinator = coordinators[0]  # Use the first available coordinator
        
        try:
            # Generate the automation
            result = await coordinator.generate_automation(description)
            
            if not result["success"]:
                raise HomeAssistantError(f"Generation failed: {result.get('error', 'Unknown error')}")
            
            yaml_config = result["yaml_config"]
            
            # Parse the YAML to get the configuration dict
            try:
                automation_config = yaml.safe_load(yaml_config)
            except yaml.YAMLError as err:
                raise HomeAssistantError(f"Invalid YAML generated: {err}") from err
            
            # Set automation name if provided
            if automation_name:
                automation_config["alias"] = automation_name
            
            # If not preview only, save the automation
            if not preview_only:
                await _save_automation_to_file(hass, automation_config, automation_name)
                _LOGGER.info("Automation saved successfully: %s", automation_config.get("alias", "Unnamed"))
            
            # Return the result
            hass.bus.async_fire(
                f"{DOMAIN}_automation_generated",
                {
                    ATTR_DESCRIPTION: description,
                    ATTR_AUTOMATION_CONFIG: automation_config,
                    ATTR_YAML_CONFIG: yaml_config,
                    ATTR_PREVIEW_ONLY: preview_only,
                }
            )
            
        except Exception as err:
            _LOGGER.error("Failed to create automation: %s", err)
            raise HomeAssistantError(f"Failed to create automation: {err}") from err

    async def handle_preview_automation(call: ServiceCall) -> None:
        """Handle the preview automation service call."""
        description = call.data[ATTR_DESCRIPTION]
        
        _LOGGER.debug("Previewing automation: %s", description)
        
        # Get the first coordinator
        coordinators = []
        for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
            if isinstance(coordinator, NaturalAutomationGeneratorCoordinator):
                coordinators.append(coordinator)
        
        if not coordinators:
            raise HomeAssistantError("No Natural Automation Generator configured")
        
        coordinator = coordinators[0]
        
        try:
            # Generate the automation
            result = await coordinator.generate_automation(description)
            
            if not result["success"]:
                raise HomeAssistantError(f"Generation failed: {result.get('error', 'Unknown error')}")
            
            yaml_config = result["yaml_config"]
            automation_config = yaml.safe_load(yaml_config)
            
            # Fire event with preview
            hass.bus.async_fire(
                f"{DOMAIN}_automation_previewed",
                {
                    ATTR_DESCRIPTION: description,
                    ATTR_AUTOMATION_CONFIG: automation_config,
                    ATTR_YAML_CONFIG: yaml_config,
                }
            )
            
        except Exception as err:
            _LOGGER.error("Failed to preview automation: %s", err)
            raise HomeAssistantError(f"Failed to preview automation: {err}") from err

    async def handle_list_entities(call: ServiceCall) -> None:
        """Handle the list entities service call."""
        _LOGGER.debug("Listing entities")
        
        # Get the first coordinator
        coordinators = []
        for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
            if isinstance(coordinator, NaturalAutomationGeneratorCoordinator):
                coordinators.append(coordinator)
        
        if coordinators:
            coordinator = coordinators[0]
            try:
                entities_info = await coordinator.get_entities_info()
                areas_info = await coordinator.get_areas_info()
                
                # Fire event with entities list
                hass.bus.async_fire(
                    f"{DOMAIN}_entities_listed",
                    {
                        "entities": entities_info,
                        "areas": areas_info,
                    }
                )
                
            except Exception as err:
                _LOGGER.error("Failed to list entities: %s", err)
                raise HomeAssistantError(f"Failed to list entities: {err}") from err

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_AUTOMATION,
        handle_create_automation,
        schema=CREATE_AUTOMATION_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_PREVIEW_AUTOMATION,
        handle_preview_automation,
        schema=PREVIEW_AUTOMATION_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_ENTITIES,
        handle_list_entities,
        schema=LIST_ENTITIES_SCHEMA,
    )
    
    _LOGGER.info("Natural Automation Generator services registered")


async def _save_automation_to_file(
    hass: HomeAssistant, 
    automation_config: dict[str, Any],
    automation_name: str | None = None
) -> None:
    """Save automation configuration to the automations.yaml file."""
    config_dir = hass.config.config_dir
    automations_file = os.path.join(config_dir, "automations.yaml")
    
    # Load existing automations
    existing_automations = []
    if os.path.exists(automations_file):
        try:
            with open(automations_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing_automations = yaml.safe_load(content) or []
        except Exception as err:
            _LOGGER.warning("Failed to load existing automations: %s", err)
    
    # Ensure existing_automations is a list
    if not isinstance(existing_automations, list):
        existing_automations = []
    
    # Generate unique ID for the automation
    import time
    automation_id = f"natural_gen_{int(time.time())}"
    automation_config["id"] = automation_id
    
    # Add the new automation
    existing_automations.append(automation_config)
    
    # Save to file
    try:
        with open(automations_file, "w", encoding="utf-8") as f:
            yaml.dump(existing_automations, f, default_flow_style=False, allow_unicode=True)
        
        # Reload automations in Home Assistant
        await hass.services.async_call("automation", "reload")
        
        _LOGGER.info("Automation saved to %s with ID: %s", automations_file, automation_id)
        
    except Exception as err:
        _LOGGER.error("Failed to save automation to file: %s", err)
        raise HomeAssistantError(f"Failed to save automation: {err}") from err 