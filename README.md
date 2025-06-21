# Natural Automation Generator for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/fadelguy/ha-natural-automation-generator)](https://github.com/fadelguy/ha-natural-automation-generator/releases)
[![GitHub issues](https://img.shields.io/github/issues/fadelguy/ha-natural-automation-generator)](https://github.com/fadelguy/ha-natural-automation-generator/issues)

Generate Home Assistant automations through natural language conversations! Chat with your Home Assistant like you would with Assist, and create automations instantly. Currently supports OpenAI ChatGPT (Google Gemini support coming soon).

## Features

- 💬 **Chat Interface**: Natural conversation interface like Home Assistant Assist
- 🤖 **AI-Powered**: Create automations using natural language descriptions
- 🔌 **LLM Provider**: Support for OpenAI ChatGPT (Google Gemini coming soon)
- 🏠 **Entity Discovery**: Automatically discovers all your Home Assistant entities and areas
- ✅ **YAML Validation**: Validates generated automations before saving
- 📝 **Automatic Saving**: Saves automations directly to your `automations.yaml` file
- 🎙️ **Voice Support**: Works with Home Assistant voice assistants
- 🌐 **Multi-language**: Supports English and Hebrew

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
4. Choose OpenAI as your LLM provider
5. Enter your OpenAI API key:
   - **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
6. Complete the setup

## How to Use

### Chat Interface (Recommended)

After installation, the Natural Automation Generator appears as a **Conversation Agent** in Home Assistant:

1. **Go to Settings → Voice Assistants**
2. **Create a new Assistant** or edit an existing one
3. **Choose "Natural Automation Generator"** as the Conversation Agent
4. **Test it**: Click the "Start Conversation" button and chat!

### Example Conversations

💬 **You**: "Create an automation to turn on bathroom light at midnight"
🤖 **Assistant**: "✅ I've created the automation successfully! [Shows YAML] The automation has been saved and is now active."

💬 **You**: "Make an automation for motion detection in hallway"  
🤖 **Assistant**: "✅ I've created the automation successfully! [Shows YAML] The automation has been saved and is now active."

💬 **You**: "List my entities"
🤖 **Assistant**: "📋 **Your Home Assistant entities:** [Shows all your lights, sensors, etc.]"

### Voice Commands

You can also use voice commands if you have a voice assistant set up:

- "Hey Home Assistant, create an automation to turn off lights when I leave"
- "Hey Home Assistant, make an automation for bedtime routine"

### Configuration Options

After setup, you can configure:

- **Model**: Choose which AI model to use
- **Max Tokens**: Maximum response length (100-4000)
- **Temperature**: Response creativity (0.0-1.0, lower = more deterministic)

## Advanced Usage

### Natural Language Examples

Here are some example phrases you can use in your conversations:

### Example Descriptions

Here are some example natural language descriptions you can use:

- **Time-based**: "Turn on the living room lights every weekday at 7 AM"
- **Motion detection**: "Turn on the hallway light when motion is detected at night"
- **Weather-based**: "Close the blinds when it's sunny outside"
- **Device states**: "Send a notification when the washing machine finishes"
- **Complex scenarios**: "If it's after sunset and someone opens the front door, turn on the porch light for 5 minutes"

### Chat Commands

You can use these types of commands in the chat:

- **Create automations**: "Create", "Make", "Generate", "צור", "יצור", "עשה"
- **List entities**: "List entities", "Show devices", "רשימת מכשירים"
- **General help**: Any other message will show help and examples

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

### Google Gemini (Coming Soon)

- Support for Google Gemini will be added in a future update
- Currently disabled due to dependency conflicts with Home Assistant

## Troubleshooting

### Common Issues

1. **"No Natural Automation Generator configured"**

   - Ensure the integration is properly set up in the Integrations page
   - Check that your API key is valid

2. **"Generation failed"**

   - Check your OpenAI API key and quota
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
