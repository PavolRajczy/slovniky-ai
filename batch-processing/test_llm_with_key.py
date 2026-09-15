"""
Test script to verify LLM abstraction works with API key from .env file.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root (parent directory)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded .env file from {env_path}")
else:
    print(f"[WARNING] .env file not found at {env_path}")

# Now import and test LLM
from llm_provider import LLMFactory, LLMProvider, LLMConfig, get_llm_instance

def test_llm_factory():
    """Test LLMFactory with API key."""
    print("\n[TEST] Testing LLMFactory.create_default_llm()...")
    try:
        llm = LLMFactory.create_default_llm(model_name="gpt-4o-mini")
        print(f"[SUCCESS] Created LLM instance: {type(llm).__name__}")
        
        # Test with a simple call
        print("[TEST] Making test API call...")
        response = llm.invoke("Say 'Hello, LLM works!' if you can read this.")
        print(f"[SUCCESS] LLM response: {response.content}")
        return True
    except Exception as e:
        print(f"[ERROR] LLMFactory test failed: {e}")
        return False

def test_get_llm_instance():
    """Test get_llm_instance convenience function."""
    print("\n[TEST] Testing get_llm_instance()...")
    try:
        llm = get_llm_instance()
        print(f"[SUCCESS] Created LLM instance: {type(llm).__name__}")
        
        # Test with a simple call
        print("[TEST] Making test API call...")
        response = llm.invoke("Say 'Hello, convenience function works!' if you can read this.")
        print(f"[SUCCESS] LLM response: {response.content}")
        return True
    except Exception as e:
        print(f"[ERROR] get_llm_instance test failed: {e}")
        return False

def test_custom_config():
    """Test with custom LLMConfig."""
    print("\n[TEST] Testing with custom LLMConfig...")
    try:
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4o-mini",
            temperature=0.0
        )
        llm = LLMFactory.create_llm(config)
        print(f"[SUCCESS] Created LLM with custom config: {type(llm).__name__}")
        
        # Test with a simple call
        print("[TEST] Making test API call...")
        response = llm.invoke("Say 'Hello, custom config works!' if you can read this.")
        print(f"[SUCCESS] LLM response: {response.content}")
        return True
    except Exception as e:
        print(f"[ERROR] Custom config test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing LLM Abstraction Layer with API Key")
    print("=" * 60)
    
    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found in environment")
        print("Make sure .env file exists in project root with OPENAI_API_KEY set")
        return 1
    
    print(f"[OK] Found OPENAI_API_KEY (length: {len(api_key)})")
    os.environ["LLM_MODEL_NAME"] = "gpt-4o-mini"
    
    results = []
    results.append(("LLMFactory.create_default_llm()", test_llm_factory()))
    results.append(("get_llm_instance()", test_get_llm_instance()))
    results.append(("Custom LLMConfig", test_custom_config()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n[SUCCESS] All tests passed! LLM abstraction layer is working correctly.")
        return 0
    else:
        print("\n[ERROR] Some tests failed.")
        return 1

if __name__ == "__main__":
    exit(main())
