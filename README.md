# Natural Automation Generator for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/fadelguy/ha-natural-automation-generator)](https://github.com/fadelguy/ha-natural-automation-generator/releases)
[![GitHub issues](https://img.shields.io/github/issues/fadelguy/ha-natural-automation-generator)](https://github.com/fadelguy/ha-natural-automation-generator/issues)

Generate Home Assistant automations using natural language with AI/LLM providers like OpenAI ChatGPT and Google Gemini.

## Features

- 🤖 **AI-Powered**: Create automations using natural language descriptions
- 🔌 **Multiple LLM Providers**: Support for OpenAI ChatGPT and Google Gemini
- 🏠 **Entity Discovery**: Automatically discovers all your Home Assistant entities and areas
- ✅ **YAML Validation**: Validates generated automations before saving
- 🔍 **Preview Mode**: Preview automations before creating them
- 🛠️ **Easy Configuration**: Simple setup through Home Assistant UI
- 📝 **Automatic Saving**: Saves automations directly to your `automations.yaml` file

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant interface
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/fadelguy/ha-natural-automation-generator`
6. Select "Integration" as the category
7. Click "Add"
8. Find "Natural Automation Generator" in the integration list and install it
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/fadelguy/ha-natural-automation-generator/releases)
2. Extract the files and copy the `custom_components/natural_automation_generator` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Configuration** → **Integrations**
2. Click **Add Integration**
3. Search for "Natural Automation Generator"
4. Choose your LLM provider (OpenAI or Google Gemini)
5. Enter your API key:
   - **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
   - **Google Gemini**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
6. Complete the setup

### Configuration Options

After setup, you can configure:

- **Model**: Choose which AI model to use
- **Max Tokens**: Maximum response length (100-4000)
- **Temperature**: Response creativity (0.0-1.0, lower = more deterministic)

## Usage

### Service Calls

The integration provides three services:

#### `natural_automation_generator.create_automation`

Create and save an automation from a natural language description.

```yaml
service: natural_automation_generator.create_automation
data:
  description: "Turn on the bathroom light every day at midnight for 10 minutes"
  automation_name: "Bathroom Night Light" # Optional
  preview_only: false # Optional, default: false
```

#### `natural_automation_generator.preview_automation`

Preview an automation without saving it.

```yaml
service: natural_automation_generator.preview_automation
data:
  description: "Turn off all lights when I leave home"
```

#### `natural_automation_generator.list_entities`

List all available entities and areas for reference.

```yaml
service: natural_automation_generator.list_entities
```

### Example Descriptions

Here are some example natural language descriptions you can use:

- **Time-based**: "Turn on the living room lights every weekday at 7 AM"
- **Motion detection**: "Turn on the hallway light when motion is detected at night"
- **Weather-based**: "Close the blinds when it's sunny outside"
- **Device states**: "Send a notification when the washing machine finishes"
- **Complex scenarios**: "If it's after sunset and someone opens the front door, turn on the porch light for 5 minutes"

### Events

The integration fires events for automation results:

- `natural_automation_generator_automation_generated`: Fired when an automation is created
- `natural_automation_generator_automation_previewed`: Fired when an automation is previewed
- `natural_automation_generator_entities_listed`: Fired when entities are listed

### Automation Examples

#### Example 1: Simple Time-Based Automation

**Input**: "Turn on kitchen lights at 6 AM every weekday"

**Generated YAML**:

```yaml
alias: "Turn on kitchen lights at 6 AM every weekday"
trigger:
  - platform: time
    at: "06:00:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: light.turn_on
    target:
      entity_id: light.kitchen
```

#### Example 2: Motion-Based Automation

**Input**: "Turn on bathroom light when motion detected, but only at night"

**Generated YAML**:

```yaml
alias: "Turn on bathroom light when motion detected at night"
trigger:
  - platform: state
    entity_id: binary_sensor.bathroom_motion
    from: "off"
    to: "on"
condition:
  - condition: sun
    after: sunset
  - condition: sun
    before: sunrise
action:
  - service: light.turn_on
    target:
      entity_id: light.bathroom
```

## API Keys and Costs

### OpenAI

- Sign up at [OpenAI Platform](https://platform.openai.com/)
- Pricing varies by model (GPT-4o is recommended)
- Typical cost: $0.01-0.05 per automation generation

### Google Gemini

- Sign up at [Google AI Studio](https://makersuite.google.com/)
- Generous free tier available
- Gemini 1.5 Flash is recommended for cost-effectiveness

## Troubleshooting

### Common Issues

1. **"No Natural Automation Generator configured"**

   - Ensure the integration is properly set up in the Integrations page
   - Check that your API key is valid

2. **"Generation failed"**

   - Check your API key and quota
   - Ensure your description is clear and specific
   - Try a simpler description first

3. **Invalid YAML Generated**

   - The AI occasionally generates invalid YAML
   - Try rephrasing your request
   - Use more specific entity names

4. **Entity not found**
   - Use the `list_entities` service to see available entities
   - Make sure entity names in your description match actual entities

### Debug Logging

Enable debug logging by adding this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.natural_automation_generator: debug
```

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration uses AI/LLM services which may:

- Generate incorrect or unsafe automations
- Have associated costs with API usage
- Send your automation descriptions to third-party services

Always review generated automations before using them in production.

## Support

- 🐛 [Report Issues](https://github.com/fadelguy/ha-natural-automation-generator/issues)
- 💬 [Community Forum](https://community.home-assistant.io/)
- 📖 [Home Assistant Documentation](https://www.home-assistant.io/docs/)

---

**Made with ❤️ for the Home Assistant community**
