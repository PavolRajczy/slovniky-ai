"""
Simple test script to verify the LLM abstraction layer works.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root (parent directory)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"[INFO] Loaded .env file from {env_path}\n")
else:
    print(f"[WARNING] .env file not found at {env_path}\n")

from llm_provider import (
    LLMProvider, 
    LLMConfig, 
    LLMFactory, 
    get_llm_instance,
    load_llm_config_from_env,
    resolve_llm_config,
)

def test_imports():
    """Test that all imports work."""
    print("[OK] All imports successful")

def test_llm_config():
    """Test LLMConfig creation."""
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o-mini",
        temperature=0.0
    )
    assert config.provider == LLMProvider.OPENAI
    assert config.model_name == "gpt-4o-mini"
    assert config.temperature == 0.0
    print("[OK] LLMConfig creation works")

def test_factory_defaults():
    """Test factory with defaults."""
    try:
        llm = LLMFactory.create_default_llm(model_name="gpt-4o-mini")
        print("[OK] LLMFactory.create_default_llm() works")
        print(f"  Model type: {type(llm).__name__}")
        # Test with a simple call to verify it actually works
        response = llm.invoke("Say 'OK' if you can read this.")
        print(f"  Test response: {response.content}")
    except ValueError as e:
        if "API key" in str(e):
            print("[WARNING] LLMFactory works but API key not set (expected)")
        else:
            raise

def test_get_llm_instance():
    """Test the convenience function."""
    previous_model_name = os.environ.pop("LLM_MODEL_NAME", None)
    try:
        os.environ["LLM_MODEL_NAME"] = "gpt-4o-mini"
        llm = get_llm_instance()
        config = resolve_llm_config()
        assert config.model_name == "gpt-4o-mini"
        print("[OK] get_llm_instance() works")
        print(f"  Model type: {type(llm).__name__}")
        print(f"  Resolved model: {config.model_name}")
        # Test with a simple call to verify it actually works
        response = llm.invoke("Say 'OK' if you can read this.")
        print(f"  Test response: {response.content}")
    except ValueError as e:
        if "API key" in str(e):
            print("[WARNING] get_llm_instance() works but API key not set (expected)")
        else:
            raise
    finally:
        if previous_model_name is None:
            os.environ.pop("LLM_MODEL_NAME", None)
        else:
            os.environ["LLM_MODEL_NAME"] = previous_model_name

def test_resolve_llm_config_defaults():
    """Test default config resolution."""
    previous_model_name = os.environ.pop("LLM_MODEL_NAME", None)
    previous_provider = os.environ.pop("LLM_PROVIDER", None)
    try:
        config = resolve_llm_config()
        assert config.provider == LLMProvider.OPENAI
        assert config.model_name == "gpt-4o-mini"
        print("[OK] resolve_llm_config() defaults to gpt-4o-mini")
    finally:
        if previous_model_name is None:
            os.environ.pop("LLM_MODEL_NAME", None)
        else:
            os.environ["LLM_MODEL_NAME"] = previous_model_name
        if previous_provider is None:
            os.environ.pop("LLM_PROVIDER", None)
        else:
            os.environ["LLM_PROVIDER"] = previous_provider

def test_env_config():
    """Test loading config from environment."""
    # Test with no env vars (should return None)
    config = load_llm_config_from_env()
    if config is None:
        print("[OK] load_llm_config_from_env() returns None when no env vars set (expected)")
    else:
        print(f"[OK] load_llm_config_from_env() loaded config: {config.provider.value}")

def test_provider_enum():
    """Test LLMProvider enum."""
    assert LLMProvider.OPENAI.value == "openai"
    assert LLMProvider.ANTHROPIC.value == "anthropic"
    assert LLMProvider.GOOGLE.value == "google"
    print("[OK] LLMProvider enum works")

def main():
    """Run all tests."""
    print("Testing LLM Abstraction Layer\n")
    print("=" * 50)
    
    try:
        test_imports()
        test_provider_enum()
        test_llm_config()
        test_factory_defaults()
        test_resolve_llm_config_defaults()
        test_get_llm_instance()
        test_env_config()
        
        print("\n" + "=" * 50)
        print("[OK] All tests passed!")
        print("\nNote: API key warnings are expected if OPENAI_API_KEY is not set.")
        print("To test with actual LLM, set OPENAI_API_KEY environment variable.")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

