# Natural Automation Generator

Generate Home Assistant automations using natural language descriptions with AI/LLM providers.

## Features

- 🤖 AI-powered automation generation from natural language
- 🔌 Supports OpenAI ChatGPT and Google Gemini
- 🏠 Automatic entity and area discovery
- ✅ YAML validation and preview mode
- 📝 Direct integration with Home Assistant automations

## Quick Start

1. Install via HACS
2. Add integration in Home Assistant
3. Configure with your OpenAI or Gemini API key
4. Use the service to create automations:

```yaml
service: natural_automation_generator.create_automation
data:
  description: "Turn on bathroom light at midnight for 10 minutes"
```

Perfect for users who want to create complex automations without learning YAML syntax!
