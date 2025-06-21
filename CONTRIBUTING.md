# Contributing to Natural Automation Generator

Thank you for your interest in contributing to the Natural Automation Generator for Home Assistant! This document provides guidelines for contributing to the project.

## Code of Conduct

This project follows the [Home Assistant Code of Conduct](https://www.home-assistant.io/code_of_conduct/). By participating, you are expected to uphold this code.

## Development Setup

### Prerequisites

- Python 3.11 or later
- Home Assistant development environment
- API keys for testing (OpenAI and/or Google Gemini)

### Setting up the Development Environment

1. Fork and clone the repository:

```bash
git clone https://github.com/fadelguy/ha-natural-automation-generator.git
cd ha-natural-automation-generator
```

2. Install development dependencies:

```bash
pip install -r requirements.txt
```

3. Set up pre-commit hooks:

```bash
pre-commit install
```

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting
- Use isort for import sorting
- Use type hints for all functions and methods
- Write docstrings for all public functions and classes

### Testing

- Write unit tests for all new functionality
- Use pytest for testing
- Maintain or improve test coverage
- Test with both OpenAI and Gemini providers

### Documentation

- Update README.md for new features
- Add docstrings to all new functions and classes
- Update example automations if needed
- Keep comments clear and concise

## How to Contribute

### Reporting Issues

When reporting issues, please include:

1. **Home Assistant version** and **integration version**
2. **LLM provider** being used (OpenAI/Gemini)
3. **Steps to reproduce** the issue
4. **Expected behavior** vs **actual behavior**
5. **Log output** (with sensitive information removed)
6. **Configuration** (anonymized)

### Suggesting Features

Feature suggestions are welcome! Please:

1. Check if the feature has already been requested
2. Explain the use case and benefits
3. Consider if it fits the project's scope
4. Be willing to help implement it

### Pull Requests

1. **Create an issue first** for significant changes
2. **Fork the repository** and create a feature branch
3. **Make your changes** following the development guidelines
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Ensure all tests pass** and code follows style guidelines
7. **Submit a pull request** with a clear description

#### Pull Request Checklist

- [ ] Code follows the project's style guidelines
- [ ] All tests pass
- [ ] New functionality includes tests
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No sensitive information (API keys, etc.) is included

## Project Structure

```
ha-natural-automation-generator/
├── custom_components/
│   └── natural_automation_generator/
│       ├── __init__.py              # Integration setup
│       ├── config_flow.py           # Configuration flow
│       ├── const.py                 # Constants
│       ├── coordinator.py           # Main coordinator
│       ├── services.py              # Service handlers
│       ├── manifest.json            # Integration manifest
│       └── llm_providers/           # LLM provider implementations
│           ├── __init__.py
│           ├── base.py              # Base provider class
│           ├── openai_provider.py   # OpenAI implementation
│           └── gemini_provider.py   # Gemini implementation
├── hacs.json                        # HACS configuration
├── README.md                        # Main documentation
├── LICENSE                          # License file
├── requirements.txt                 # Dependencies
└── example_automations.yaml         # Example outputs
```

## Development Tips

### Adding New LLM Providers

1. Create a new provider class inheriting from `BaseLLMProvider`
2. Implement all abstract methods
3. Add the provider to the configuration flow
4. Update constants and documentation
5. Add tests for the new provider

### Improving the System Prompt

The system prompt is crucial for good results. When modifying:

1. Test with various entity types and scenarios
2. Keep the prompt concise but informative
3. Include clear examples
4. Validate that generated YAML is always valid

### Testing with Real APIs

When testing with real API keys:

1. Use test/development API keys
2. Be mindful of API costs
3. Never commit API keys to the repository
4. Use environment variables for testing

## Common Development Tasks

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black custom_components/
isort custom_components/
```

### Type Checking

```bash
mypy custom_components/natural_automation_generator/
```

### Testing in Home Assistant

1. Copy the integration to your HA `custom_components` directory
2. Restart Home Assistant
3. Add the integration through the UI
4. Test with your entities and scenarios

## Release Process

1. Update version in `manifest.json`
2. Update CHANGELOG.md
3. Create a release PR
4. Tag the release after merging
5. Update HACS information if needed

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For general questions and discussions
- **Home Assistant Community**: For Home Assistant specific questions

## Recognition

Contributors will be recognized in the README.md file and release notes. We appreciate all contributions, whether they're code, documentation, testing, or feature suggestions!

---

Thank you for contributing to making Home Assistant automation creation more accessible to everyone! 🚀
