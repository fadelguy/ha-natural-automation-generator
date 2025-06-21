# Natural Automation Generator for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/fadelguy/ha-natural-automation-generator)](https://github.com/fadelguy/ha-natural-automation-generator/releases)
[![GitHub issues](https://img.shields.io/github/issues/fadelguy/ha-natural-automation-generator)](https://github.com/fadelguy/ha-natural-automation-generator/issues)

[![GitHub Sponsors](https://img.shields.io/badge/sponsor-GitHub_Sponsors-ea4aaa?style=flat&logo=github)](https://github.com/sponsors/fadelguy)

Generate Home Assistant automations through natural language conversations! Chat with your Home Assistant using the built-in Voice Assistants like Assist, and create automations instantly using OpenAI's powerful AI models.

## ✨ Features

- 💬 **Chat Interface**: Natural conversation interface integrated with Home Assistant Voice Assistants
- 🤖 **AI-Powered**: Uses OpenAI GPT models (GPT-4o, GPT-4o-mini, etc.) for automation generation
- 🏠 **Entity Discovery**: Automatically discovers all your Home Assistant entities and areas
- ✅ **YAML Validation**: Validates and fixes generated automations before saving
- 📝 **Automatic Saving**: Saves automations directly to your `automations.yaml` file with unique IDs
- 🎙️ **Voice Support**: Works with Home Assistant voice assistants and mobile app
- 🌐 **Multi-language**: Supports English and Hebrew conversations
- 🔄 **Auto-Generated Tags**: All automations are clearly marked as "(Auto Generated)"
- 📊 **Dashboard Integration**: Visible in Settings → Integrations with status monitoring
- ⚙️ **Configurable**: Update API keys, models, and parameters through the UI

## 🚀 Installation

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

## ⚙️ Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **Add Integration**
3. Search for "Natural Automation Generator"
4. Enter your OpenAI API key (get it from [OpenAI Platform](https://platform.openai.com/api-keys))
5. Complete the setup

### Configuration Options

After setup, you can reconfigure the integration by clicking **Configure** in the integrations dashboard:

- **API Key**: Update your OpenAI API key
- **Model**: Choose your preferred GPT model:
  - `gpt-4o` (recommended - most capable)
  - `gpt-4o-mini` (faster and cheaper)
  - `gpt-4-turbo` (previous generation)
  - `gpt-3.5-turbo` (basic but economical)
- **Max Tokens**: Maximum response length (100-4000 tokens)
- **Temperature**: Response creativity (0.0-1.0, lower = more deterministic)

## 🎯 How to Use

### Setting Up Voice Assistant

1. **Go to Settings → Voice Assistants**
2. **Create a new Assistant** or edit an existing one:
   - Name: "Automation Assistant" (or any name you prefer)
   - Conversation Agent: **Select "Natural Automation Generator"**
   - Language: Choose your preferred language
3. **Save the configuration**

### Chat Interface

You can now chat with your automation assistant in several ways:

#### Via Voice Assistants Page

1. Go to **Settings → Voice Assistants**
2. Click on your assistant
3. Click **"Test"** to start a conversation
4. Type or speak your automation requests

#### Via Mobile App

- Say: _"Hey Home Assistant, create an automation to turn on bathroom light at midnight"_
- Or open the assistant and type your request

#### Via Voice Assistant Devices

- Use any connected voice assistant device with your configured assistant

### Example Conversations

💬 **You**: "Create an automation to turn on bathroom light at midnight"  
🤖 **Assistant**:

```
✅ Automation Created Successfully!

Name: Turn on bathroom light at midnight (Auto Generated)
Description: Create an automation to turn on bathroom light at midnight

Generated YAML:
id: "abc12345"
alias: "Turn on bathroom light at midnight (Auto Generated)"
triggers:
  - platform: time
    at: "00:00:00"
actions:
  - action: light.turn_on
    target:
      entity_id: light.bathroom

🎉 The automation has been saved to your automations.yaml file and is now active!
```

💬 **You**: "Make an automation for motion detection in hallway"  
🤖 **Assistant**: "✅ Automation created successfully! [Details and YAML shown]"

💬 **You**: "List my entities"  
🤖 **Assistant**: "📋 Your Home Assistant entities: [Complete list of all devices]"

### Voice Commands Examples

- "Create an automation to turn off lights when I leave"
- "Make an automation for bedtime routine"
- "Generate automation to close blinds when sunny"
- "צור אוטומציה להדליק אור בחדר שינה בשבע בבוקר" (Hebrew)

## 📋 Advanced Usage

### Natural Language Examples

The AI understands complex automation descriptions:

- **Time-based**: "Turn on the living room lights every weekday at 7 AM"
- **Motion detection**: "Turn on the hallway light when motion is detected, but only at night"
- **Weather-based**: "Close the blinds when it's sunny and temperature is above 25°C"
- **Device states**: "Send a notification when the washing machine finishes its cycle"
- **Complex scenarios**: "If it's after sunset and someone opens the front door, turn on the porch light for 5 minutes then turn it off"
- **Multi-step**: "When I press the bedtime switch, turn off all lights, lock the doors, and set the thermostat to 18°C"

### Supported Chat Commands

- **Create automations**: "Create", "Make", "Generate", "Build", "צור", "יצור", "עשה", "בנה"
- **List entities**: "List entities", "Show devices", "What entities do I have?", "רשימת מכשירים"
- **Help**: Any other message will show help and examples

### Generated Automation Format

All automations generated by this integration:

✅ **Include unique IDs** for editor compatibility  
✅ **Use modern YAML format** (`triggers`/`actions` instead of `trigger`/`action`)  
✅ **Are clearly marked** with "(Auto Generated)" in the name  
✅ **Are automatically saved** to `automations.yaml`  
✅ **Are immediately active** after creation

Example generated automation:

```yaml
- id: "living_room_8am"
  alias: "Turn on living room lights at 8 AM (Auto Generated)"
  triggers:
    - platform: time
      at: "08:00:00"
  conditions:
    - condition: time
      weekday:
        - mon
        - tue
        - wed
        - thu
        - fri
  actions:
    - action: light.turn_on
      target:
        entity_id: light.living_room_main
```

## 💰 API Keys and Costs

### OpenAI Setup

1. **Sign up** at [OpenAI Platform](https://platform.openai.com/)
2. **Add payment method** (required for API access)
3. **Generate API key** in the API Keys section
4. **Set usage limits** to control costs (recommended)

### Cost Estimates

- **GPT-4o**: ~$0.02-0.08 per automation
- **GPT-4o-mini**: ~$0.005-0.02 per automation
- **GPT-3.5-turbo**: ~$0.001-0.005 per automation

Costs depend on automation complexity and entity count.

## 🛠️ Troubleshooting

### Common Issues

1. **Integration not visible in dashboard**

   - Restart Home Assistant after installation
   - Check that the integration shows "Ready (OpenAI)" status

2. **"Missing required fields" error**

   - The AI generated invalid YAML format
   - Try rephrasing your request more specifically
   - Use exact entity names from your system

3. **"Generation failed" error**

   - Check your OpenAI API key is valid and has credit
   - Verify your internet connection
   - Try a simpler automation description first

4. **Entity not found**

   - Ask to "list entities" to see available devices
   - Use exact entity names (e.g., `light.living_room_main`)
   - Make sure the device is properly set up in Home Assistant

5. **Cannot update API key**
   - Go to Settings → Integrations
   - Click "Configure" on Natural Automation Generator
   - Update your API key and save

### Debug Logging

Enable detailed logging by adding this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.natural_automation_generator: debug
```

### Integration Status

Check the integration status in **Settings → Integrations**:

- **Status sensor** shows "Ready (OpenAI)" when working
- **Provider information** and connection status
- **Configuration options** for updates

## 🔧 Technical Details

### Supported Platforms

- **Conversation**: Chat interface integration
- **Sensor**: Status monitoring and dashboard visibility

### Dependencies

- **OpenAI Python SDK** (≥1.3.0)
- **PyYAML** (≥6.0)
- **Home Assistant** (≥2024.1.0)

### File Structure

```
custom_components/natural_automation_generator/
├── __init__.py              # Integration setup
├── config_flow.py           # Configuration UI
├── conversation.py          # Chat interface
├── coordinator.py           # Entity discovery & automation generation
├── sensor.py               # Status sensor
├── const.py                # Constants and prompts
├── manifest.json           # Integration metadata
└── llm_providers/
    ├── base.py             # Abstract LLM provider
    └── openai_provider.py  # OpenAI implementation
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Home Assistant
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This integration uses AI/LLM services which may:

- Generate incorrect or unsafe automations
- Have associated costs with API usage
- Send your automation descriptions to OpenAI's servers
- Occasionally produce invalid YAML that needs manual fixing

**Always review generated automations before relying on them in production.**

## 🆘 Support

- 🐛 [Report Issues](https://github.com/fadelguy/ha-natural-automation-generator/issues)
- 💬 [Community Forum](https://community.home-assistant.io/)
- 📖 [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- 📧 [OpenAI Support](https://help.openai.com/) for API-related issues

## ☕ Support This Project

If this integration has made your Home Assistant automation journey easier, consider supporting its development:

<div align="center">

[![GitHub Sponsors](https://img.shields.io/badge/sponsor-GitHub_Sponsors-ea4aaa?style=for-the-badge&logo=github)](https://github.com/sponsors/fadelguy)

</div>

**Why support this project?**

- 🚀 **Continued Development**: New features, bug fixes, and improvements
- 🤖 **Additional AI Providers**: Support for Google Gemini, Claude, and other LLM providers
- 📚 **Enhanced Documentation**: Better guides, examples, and tutorials
- 🎯 **Priority Support**: Faster responses to issues and feature requests
- ☁️ **API Costs**: Helping cover development and testing API costs

Every contribution, no matter how small, helps keep this project alive and growing! 🙏

### 🎯 How You Can Help

Support this project through [GitHub Sponsors](https://github.com/sponsors/fadelguy) - any contribution helps keep the project alive and growing!

_Every contribution, no matter the size, makes a real difference in continued development and improvements._

## 🚀 Roadmap

### Planned Features

- [ ] Support for additional LLM providers (Google Gemini, Claude, etc.)
- [ ] Automation templates and examples library
- [ ] Advanced automation validation and testing
- [ ] Integration with Home Assistant automation editor
- [ ] Batch automation creation
- [ ] Natural language automation explanation/documentation

### Recent Updates (v1.2.6)

- ✅ Integrated with Voice Assistants interface
- ✅ Added dashboard visibility and status monitoring
- ✅ Improved YAML validation and error handling
- ✅ Added auto-generated automation tagging
- ✅ Enhanced configuration options and API key management
- ✅ Fixed automation ID generation for editor compatibility

---

**Made with ❤️ for the Home Assistant community**
