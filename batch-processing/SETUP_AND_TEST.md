# Setup and Testing Guide

## Current Status

The LLM abstraction layer has been created and integrated into all batch-processing scripts. However, **dependencies need to be installed** before it can be used.

## Installation Steps

### 1. Install Dependencies

Run this command in the `batch-processing` directory:

```bash
pip install -r requirements.txt
```

Or install just the required LangChain packages:

```bash
pip install langchain langchain-core langchain-openai
```

For additional providers (optional):
```bash
pip install langchain-anthropic    # For Anthropic Claude
pip install langchain-google-genai  # For Google Gemini
```


### 2. Test the Abstraction Layer

Run the comprehensive test:

```bash
python test_llm_abstraction.py
```

This will test:
- ✓ All imports
- ✓ LLMProvider enum
- ✓ LLMConfig creation
- ✓ LLMFactory functionality
- ✓ get_llm_instance() convenience function

**Note**: The test may show API key warnings if `OPENAI_API_KEY` is not set, but that's expected. The abstraction layer itself will work.

## What Was Changed

All batch-processing scripts have been updated to use the abstraction:

- `classExtraction.py` - Now uses `get_llm_instance()`
- `classCategorization.py` - Now uses `get_llm_instance()`
- `classMerging.py` - Now uses `get_llm_instance()`
- `relationshipExtraction.py` - Now uses `get_llm_instance()`
- `attributeExtraction.py` - Now uses `get_llm_instance()`

## Configuration

You can now switch LLM providers without changing code:

### Option 1: Environment Variables
```bash
export LLM_PROVIDER=openai
export LLM_MODEL_NAME=gpt-4o
export OPENAI_API_KEY=your-key
```

### Option 2: Configuration File
```bash
export LLM_CONFIG_FILE=llm_config_example.json
```

See `LLM_ABSTRACTION_README.md` for full documentation.

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'langchain_core'"
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Issue: "API key not provided"
**Solution**: Set the appropriate API key environment variable:
- `OPENAI_API_KEY` for OpenAI
- `ANTHROPIC_API_KEY` for Anthropic
- `GOOGLE_API_KEY` for Google

### Issue: "ImportError: langchain-anthropic is not installed"
**Solution**: This is only needed if using Anthropic. Either:
- Install it: `pip install langchain-anthropic`
- Or use a different provider (OpenAI is the default)

