# Release Notes

## Version 2.0.7 (2025-01-21)

### 🚀 Improvements

- **Enhanced JSON Schema Support for Gemini**: Added full support for JSON schema structured output in Gemini provider
- **Improved Response Parsing**: Added robust JSON response cleaning to handle responses wrapped in markdown code blocks
- **Better Error Handling**: Enhanced error handling for JSON parsing failures with detailed logging

### 🔧 Technical Changes

- Added `_convert_schema_to_gemini_format()` method to convert OpenAI-style schemas to Gemini format
- Added `_clean_json_response()` method to handle markdown-wrapped JSON responses
- Optimized Gemini parameters for deterministic JSON output (top_k=1, top_p=0.1)
- Enhanced structured output reliability across both OpenAI and Gemini providers

### 📋 Schema Support

- Full support for `ANALYSIS_JSON_SCHEMA` for automation request analysis
- Full support for `INTENT_ANALYSIS_JSON_SCHEMA` for user intent analysis
- Automatic schema conversion between OpenAI and Gemini formats
- Consistent JSON output across both providers

---

## Version 2.0.6 (2025-01-21)

### 🚀 New Features

- **Gemini 2.5 Integration**: Added support for Google's latest Gemini 2.5 models
- **Dual Provider Support**: Full bi-provider support - choose between OpenAI and Gemini
- **Model Selection**: Support for gemini-2.5-flash and gemini-2.5-pro models
- **Cost Optimization**: Gemini 2.5-flash offers significant cost savings (~$0.005 per automation)

### 🔧 Technical Improvements

- **New Google GenAI SDK**: Migrated to google-genai>=1.0.0 for improved reliability
- **Optimized Parameters**: Fine-tuned generation parameters for better automation quality
- **Enhanced Error Handling**: Better error messages and debugging information
- **Improved Logging**: More detailed logging for troubleshooting

### 📋 Configuration

- Updated configuration flow to include Gemini provider selection
- Maintained backward compatibility with existing OpenAI configurations
- Added model selection UI for both providers

### 🐛 Bug Fixes

- Fixed YAML parsing edge cases
- Improved automation validation
- Enhanced response processing reliability

### 📊 Performance & Cost

- **Gemini 2.5-flash**: ~$0.005 per automation (vs. $0.03-0.06 for OpenAI)
- **Gemini 2.5-pro**: ~$0.025 per automation (premium quality)
- **OpenAI GPT-4**: ~$0.03-0.06 per automation (established reliability)

---

## Version 2.0.5 (2025-01-21)

### 🚀 New Features

- **Gemini Integration**: Added initial support for Google Gemini models
- **Dual Provider Architecture**: Support for both OpenAI and Gemini providers
- **Enhanced Configuration**: Provider selection in configuration flow

### 🔧 Technical Changes

- Added GeminiProvider class with google-generativeai integration
- Implemented provider selection logic in coordinator
- Added Gemini-specific model configurations

### 📋 Models Supported

- **OpenAI**: gpt-4.1, gpt-4o, gpt-4o-mini
- **Gemini**: gemini-1.5-flash, gemini-1.5-pro

---

## Version 2.0.4 (Previous)

### 🚀 Features

- **Natural Language Processing**: Advanced conversation handling with multi-step clarification
- **Smart Entity Detection**: Automatic detection and disambiguation of Home Assistant entities
- **Hebrew & English Support**: Bilingual support with natural language processing
- **Preview System**: Preview automations before creation with user approval flow
- **Validation System**: Comprehensive YAML validation and error handling

### 🔧 Technical Features

- **OpenAI Integration**: GPT-4 powered automation generation
- **Conversation Management**: Multi-step conversation flow with context preservation
- **Entity Registry Integration**: Real-time entity and area discovery
- **YAML Generation**: Structured automation YAML with proper formatting
- **Error Recovery**: Robust error handling and user feedback

### 📋 Supported Use Cases

- Time-based automations (sunrise, sunset, specific times)
- Motion and sensor-based triggers
- Device control (lights, switches, climate, etc.)
- Multi-condition automations
- Area-based automations

---

## Migration Guide

### From Version 2.0.6 to 2.0.7

No breaking changes. Existing configurations will continue to work. New installations will benefit from improved JSON schema support automatically.

### From Version 2.0.5 to 2.0.6

1. The integration will automatically update to use the new Google GenAI SDK
2. Existing Gemini configurations may need to be reconfigured due to model changes
3. New model options (gemini-2.5-flash, gemini-2.5-pro) will be available

### From Version 2.0.4 to 2.0.5+

1. Existing OpenAI configurations will continue to work unchanged
2. New Gemini provider option will be available in configuration
3. You can switch between providers without losing functionality

---

## Support

For issues, questions, or feature requests, please visit our [GitHub repository](https://github.com/fadelguy/ha-natural-automation-generator).
