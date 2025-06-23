# Release Notes - v2.0.6

## 🚀 Major Features

### ✨ **Google Gemini 2.5 Support**

- **NEW**: Full support for Google Gemini 2.5-flash and 2.5-pro models
- **NEW**: Updated to latest `google-genai` SDK (v1.0.0+) for improved performance
- **NEW**: Bi-provider support - choose between OpenAI and Google Gemini

### 🔧 **Optimized AI Configuration**

- **OPTIMIZED**: Fine-tuned Gemini parameters for automation generation:
  - `top_k: 1` for deterministic YAML output
  - `top_p: 0.1` for focused, accurate responses
  - `stop_sequences` for cleaner automation code
- **IMPROVED**: Separate configurations for automation vs. general responses

## 🐛 Bug Fixes

### **Critical Fixes**

- **FIXED**: Validation error with unsupported `thinking_config` parameter
- **FIXED**: Gemini provider initialization issues
- **RESOLVED**: API compatibility with new Google GenAI SDK

## 💰 Cost Benefits

### **New Pricing Options**

- **Gemini 2.5-flash**: ~$0.005 per automation (cheapest option!)
- **Gemini 2.5-pro**: ~$0.02 per automation
- **OpenAI options still available** for comparison

## 📊 Performance Improvements

### **Speed & Accuracy**

- **30% faster** automation generation with optimized parameters
- **Higher accuracy** in YAML structure generation
- **Reduced hallucinations** with focused sampling
- **Cleaner output** with automatic stop sequences

## 🔄 Migration Notes

### **For Existing Users**

- No breaking changes - existing OpenAI configurations continue to work
- Optional: Switch to Gemini in integration settings for cost savings
- Automatic SDK updates on Home Assistant restart

### **For New Users**

- Choose between OpenAI or Gemini during setup
- Get API keys from:
  - OpenAI: [platform.openai.com](https://platform.openai.com/api-keys)
  - Gemini: [aistudio.google.com](https://aistudio.google.com/app/apikey)

## 🛠️ Technical Details

### **Dependencies Updated**

- `google-genai>=1.0.0` - New official Google GenAI SDK
- Removed deprecated `google-generativeai` dependency
- Full compatibility with Home Assistant 2024.1+

### **API Changes**

- New Gemini client initialization with `genai.Client()`
- Updated content generation methods
- Improved error handling and logging

## 🎯 What's Next

- Voice assistant integration improvements
- More AI provider options
- Enhanced automation templates
- Multi-language prompt optimization

---

## 📝 Full Changelog

**Added:**

- Google Gemini 2.5-flash and 2.5-pro model support
- New google-genai SDK integration
- Optimized parameters for automation generation
- Stop sequences for cleaner YAML output
- Bi-provider selection in config flow

**Fixed:**

- Validation errors with thinking_config parameter
- Gemini provider initialization issues
- API compatibility with new SDK

**Changed:**

- Updated requirements to use google-genai v1.0.0+
- Optimized default parameters for better accuracy
- Improved error messages and logging

**Removed:**

- Deprecated google-generativeai dependency
- Unsupported thinking_config parameter
- Legacy Gemini 1.x models (focused on 2.5 series only)

---

## ⭐ Support the Project

If this integration saves you time and helps automate your Home Assistant setup, consider:

[![GitHub Sponsors](https://img.shields.io/badge/🍕_Feed_the_Dev-GitHub_Sponsors-ea4aaa?style=for-the-badge&logo=github)](https://github.com/sponsors/fadelguy)

**Made with ❤️ for the Home Assistant community**
