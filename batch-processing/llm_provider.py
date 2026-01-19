"""
LLM Provider Abstraction Layer using LangChain.

This module provides a unified interface for working with different LLM providers
(OpenAI, Anthropic, etc.) through LangChain, allowing easy switching between providers.
"""

import os
import json
from enum import Enum
from typing import Optional, Dict, Any
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

# Optional imports - install only if you need these providers
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMConfig:
    """Configuration for LLM instances."""
    
    def __init__(
        self,
        provider: LLMProvider,
        model_name: str,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Initialize LLM configuration.
        
        Args:
            provider: The LLM provider to use
            model_name: The model name (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
            temperature: Temperature setting (0.0-2.0)
            api_key: API key for the provider (if None, will use environment variable)
            **kwargs: Additional provider-specific parameters
        """
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.api_key = api_key
        self.extra_params = kwargs
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LLMConfig":
        """Create LLMConfig from a dictionary."""
        provider = LLMProvider(config_dict.get("provider", "openai").lower())
        return cls(
            provider=provider,
            model_name=config_dict.get("model_name", "gpt-4o"),
            temperature=config_dict.get("temperature", 0.0),
            api_key=config_dict.get("api_key"),
            **config_dict.get("extra_params", {})
        )


class LLMFactory:
    """Factory for creating LLM instances from different providers."""
    
    @staticmethod
    def create_llm(config: LLMConfig) -> BaseChatModel:
        """
        Create an LLM instance based on the provided configuration.
        
        Args:
            config: LLM configuration
            
        Returns:
            LangChain BaseChatModel instance
            
        Raises:
            ValueError: If provider is not supported or required API key is missing
        """
        # Get API key
        api_key = config.api_key
        if not api_key:
            api_key = LLMFactory._get_api_key_for_provider(config.provider)
        
        if not api_key:
            raise ValueError(
                f"API key not provided for {config.provider.value}. "
                f"Set it in config or as environment variable {LLMFactory._get_env_var_name(config.provider)}"
            )
        
        # Create LLM based on provider
        if config.provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=config.model_name,
                temperature=config.temperature,
                api_key=api_key,
                **config.extra_params
            )
        elif config.provider == LLMProvider.ANTHROPIC:
            if ChatAnthropic is None:
                raise ImportError(
                    "langchain-anthropic is not installed. "
                    "Install it with: pip install langchain-anthropic"
                )
            return ChatAnthropic(
                model=config.model_name,
                temperature=config.temperature,
                api_key=api_key,
                **config.extra_params
            )
        elif config.provider == LLMProvider.GOOGLE:
            if ChatGoogleGenerativeAI is None:
                raise ImportError(
                    "langchain-google-genai is not installed. "
                    "Install it with: pip install langchain-google-genai"
                )
            return ChatGoogleGenerativeAI(
                model=config.model_name,
                temperature=config.temperature,
                google_api_key=api_key,
                **config.extra_params
            )
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    @staticmethod
    def _get_api_key_for_provider(provider: LLMProvider) -> Optional[str]:
        """Get API key from environment variable for the given provider."""
        env_var = LLMFactory._get_env_var_name(provider)
        return os.getenv(env_var)
    
    @staticmethod
    def _get_env_var_name(provider: LLMProvider) -> str:
        """Get the environment variable name for the provider's API key."""
        mapping = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.GOOGLE: "GOOGLE_API_KEY"
        }
        return mapping[provider]
    
    @staticmethod
    def create_default_llm(
        provider: Optional[LLMProvider] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0
    ) -> BaseChatModel:
        """
        Create a default LLM instance.
        
        Args:
            provider: Provider to use (defaults to OpenAI if not specified)
            model_name: Model name (defaults to provider-specific default)
            temperature: Temperature setting
            
        Returns:
            LangChain BaseChatModel instance
        """
        if provider is None:
            provider = LLMProvider.OPENAI
        
        if model_name is None:
            model_name = LLMFactory._get_default_model(provider)
        
        config = LLMConfig(
            provider=provider,
            model_name=model_name,
            temperature=temperature
        )
        return LLMFactory.create_llm(config)
    
    @staticmethod
    def _get_default_model(provider: LLMProvider) -> str:
        """Get default model name for the provider."""
        defaults = {
            LLMProvider.OPENAI: "gpt-4o",
            LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
            LLMProvider.GOOGLE: "gemini-pro"
        }
        return defaults[provider]


def load_llm_config_from_file(config_path: str) -> LLMConfig:
    """
    Load LLM configuration from a JSON file.
    
    Args:
        config_path: Path to the JSON configuration file
        
    Returns:
        LLMConfig instance
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = json.load(f)
    
    return LLMConfig.from_dict(config_dict)


def load_llm_config_from_env() -> Optional[LLMConfig]:
    """
    Load LLM configuration from environment variables.
    
    Environment variables:
        LLM_PROVIDER: Provider name (openai, anthropic, google)
        LLM_MODEL_NAME: Model name (e.g., gpt-4o)
        LLM_TEMPERATURE: Temperature (default: 0.0)
        
    Returns:
        LLMConfig instance or None if not configured
    """
    provider_str = os.getenv("LLM_PROVIDER")
    if not provider_str:
        return None
    
    try:
        provider = LLMProvider(provider_str.lower())
    except ValueError:
        return None
    
    model_name = os.getenv("LLM_MODEL_NAME")
    if not model_name:
        model_name = LLMFactory._get_default_model(provider)
    
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    
    return LLMConfig(
        provider=provider,
        model_name=model_name,
        temperature=temperature
    )


def get_llm_instance() -> BaseChatModel:
    """
    Get an LLM instance using the configured provider.
    
    Tries to load configuration from:
    1. Config file (if LLM_CONFIG_FILE env var is set)
    2. Environment variables
    3. Defaults to OpenAI gpt-4o
    
    Returns:
        LangChain BaseChatModel instance
    """
    llm_config = None
    config_file = os.getenv("LLM_CONFIG_FILE")
    if config_file and os.path.exists(config_file):
        llm_config = load_llm_config_from_file(config_file)
    else:
        llm_config = load_llm_config_from_env()
    
    if llm_config is None:
        # Default to OpenAI gpt-4o
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4o",
            temperature=0.0
        )
    
    return LLMFactory.create_llm(llm_config)

