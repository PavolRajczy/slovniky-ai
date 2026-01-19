# LLM Provider Abstraction Layer

This abstraction layer allows you to easily switch between different LLM providers (OpenAI, Anthropic, Google) using LangChain, without changing your code.

## Features

- **Unified Interface**: Use the same code with different LLM providers
- **Easy Configuration**: Configure via JSON file or environment variables
- **LangChain Integration**: Built on top of LangChain for maximum compatibility
- **Multiple Providers**: Support for OpenAI, Anthropic, and Google

## Installation

Install the required packages:

```bash
pip install -r requirements.txt
```

For specific providers (optional):
- OpenAI: Already included in `langchain-openai`
- Anthropic: `pip install langchain-anthropic`
- Google: `pip install langchain-google-genai`

## Usage

### Method 1: Using Configuration File

1. Create a JSON configuration file (see `llm_config_example.json`):

```json
{
  "provider": "openai",
  "model_name": "gpt-4o",
  "temperature": 0.0,
  "api_key": null,
  "extra_params": {}
}
```

2. Set the environment variable:
```bash
export LLM_CONFIG_FILE=path/to/your/config.json
```

3. Run your script - it will automatically use the configured LLM.

### Method 2: Using Environment Variables

Set these environment variables:

```bash
export LLM_PROVIDER=openai          # or "anthropic", "google"
export LLM_MODEL_NAME=gpt-4o        # model name for the provider
export LLM_TEMPERATURE=0.0          # optional, defaults to 0.0
export OPENAI_API_KEY=your_key      # provider-specific API key
```

### Method 3: Programmatic Usage

**Simplest approach** (automatically uses config file or env vars):
```python
from llm_provider import get_llm_instance

llm = get_llm_instance()  # Automatically loads from config or env vars
```

### Before (Hardcoded OpenAI)
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0)
```

### After (Using Abstraction)
```python
from llm_provider import LLMFactory, LLMProvider

llm = LLMFactory.create_default_llm(
    provider=LLMProvider.OPENAI,
    model_name="gpt-4o",
    temperature=0.0
)
```

## API Reference

### `LLMProvider` Enum
Enumeration of supported LLM providers:
- `LLMProvider.OPENAI`
- `LLMProvider.ANTHROPIC`
- `LLMProvider.GOOGLE`

### `LLMConfig` Class
Configuration class for LLM instances.

**Parameters:**
- `provider`: `LLMProvider` - The LLM provider to use
- `model_name`: `str` - The model name
- `temperature`: `float` - Temperature (0.0-2.0), default 0.0
- `api_key`: `Optional[str]` - API key (if None, uses environment variable)
- `**kwargs`: Additional provider-specific parameters

### `LLMFactory` Class
Factory for creating LLM instances.

**Methods:**
- `create_llm(config: LLMConfig) -> BaseChatModel`: Create LLM from config
- `create_default_llm(provider, model_name, temperature) -> BaseChatModel`: Create with defaults

### Helper Functions
- `get_llm_instance() -> BaseChatModel`: Get LLM instance (auto-loads from config file or env vars)
- `load_llm_config_from_file(config_path: str) -> LLMConfig`: Load config from JSON file
- `load_llm_config_from_env() -> Optional[LLMConfig]`: Load config from environment variables

## Notes

- API keys can be provided in the config file or as environment variables
- If an API key is not provided, the factory will look for the appropriate environment variable
- Output directories in batch processing scripts automatically use the model name from config
- All LangChain features work seamlessly with the abstraction layer

