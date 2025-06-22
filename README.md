# Natural Automation Generator for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/fadelguy/ha-natural-automation-generator)](https://github.com/fadelguy/ha-natural-automation-generator/releases)

## 🍕 Feed the Developer (He's Hungry!)

> **Plot twist:** This integration works so well, I forgot to eat while coding it! 😅  
> If this saves you from manually writing YAML automations (and your sanity), consider buying me a virtual pizza!

<div align="center">

[![GitHub Sponsors](https://img.shields.io/badge/🍕_Feed_the_Dev-GitHub_Sponsors-ea4aaa?style=for-the-badge&logo=github)](https://github.com/sponsors/fadelguy)

_No pressure though - the integration is free forever! But pizza keeps the code flowing..._ 🍕➡️💻➡️✨

</div>

---

**Transform your words into Home Assistant automations!** 🗣️✨  
Just tell it what you want, and it creates the automation for you.

## ✨ What It Does

- 🗣️ **Chat naturally**: "Turn on lights when I get home"
- 🤖 **AI creates automation**: Uses OpenAI GPT models
- 📝 **Saves automatically**: Straight to your `automations.yaml`
- 🌐 **Multi-language**: English & Hebrew supported
- 🎙️ **Voice ready**: Works with Home Assistant voice assistants

## 🚀 Installation

### Via HACS (Recommended)

1. **HACS** → **Integrations** → **⋮** → **Custom repositories**
2. Add: `https://github.com/fadelguy/ha-natural-automation-generator`
3. Find **"Natural Automation Generator"** and install
4. **Restart Home Assistant**

### Setup

1. **Settings** → **Integrations** → **Add Integration**
2. Search **"Natural Automation Generator"**
3. Enter your **OpenAI API key** ([Get one here](https://platform.openai.com/api-keys))
4. Done! 🎉

## 🎯 How to Use

### Quick Setup

1. **Settings** → **Voice Assistants** → **Add Assistant**
2. **Conversation Agent**: Select **"Natural Automation Generator"**
3. **Test** it out!

### Just Talk to It! 🗣️

**Examples:**

- "Turn on bathroom light at midnight"
- "Motion sensor hallway lights"
- "Close blinds when sunny"
- "תדליק אור בסלון בשבע בבוקר" (Hebrew)

**Result:**

```
✅ Automation Created Successfully!

Name: Turn on bathroom light at midnight (Auto Generated)
🎉 Saved to automations.yaml and active!
```

## 💰 Costs

**Need OpenAI API key** ([Get one here](https://platform.openai.com/))

- **GPT-4o-mini**: ~$0.01 per automation (recommended)
- **GPT-4o**: ~$0.05 per automation
- **GPT-4.1**: ~$0.08 per automation

## 🛠️ Issues?

1. **Not working?** → Restart Home Assistant
2. **API errors?** → Check your OpenAI key has credit
3. **Entity not found?** → Ask "list my entities" first

---

**That's it!** 🎉 Now just talk to Home Assistant and watch the magic happen!

---

🐛 [Issues](https://github.com/fadelguy/ha-natural-automation-generator/issues) • 💬 [Community](https://community.home-assistant.io/) • **Made with ❤️ for Home Assistant**
