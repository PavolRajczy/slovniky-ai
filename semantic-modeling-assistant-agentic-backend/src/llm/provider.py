"""
LangChain access to an OpenAI-compatible chat API.

The agentic backend and the batch-processing scripts share this factory.
e-INFRA CZ is that kind of API: one origin, many model names. Pick a model
with OPENAI_MODEL, OPENAI_MODEL_MINI, or LLM_MODEL_NAME. An empty value
falls back to the maintained alias ``mini``.

    OPENAI_BASE_URL              API origin, for example https://llm.ai.e-infra.cz/v1/
    OPENAI_MODEL                 task planner and iteration suggester
    OPENAI_MODEL_MINI            modeler, domain-area analyzer, and summarizer
    LLM_MODEL_NAME               single model for batch scripts; also the fallback
    OPENAI_EMBEDDING_MODEL       defaults to qwen3-embedding-4b
    OPENAI_EMBEDDING_DIMENSION   defaults to 2560
"""
import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

load_dotenv()


DEFAULT_CHAT_MODEL = "mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_EMBEDDING_MODEL = "qwen3-embedding-4b"
DEFAULT_EMBEDDING_DIMENSION = 2560

MODEL_ENV_VAR = "OPENAI_MODEL"
MINI_MODEL_ENV_VAR = "OPENAI_MODEL_MINI"
BATCH_MODEL_ENV_VAR = "LLM_MODEL_NAME"
BASE_URL_ENV_VAR = "OPENAI_BASE_URL"
EMBEDDING_MODEL_ENV_VAR = "OPENAI_EMBEDDING_MODEL"
EMBEDDING_DIMENSION_ENV_VAR = "OPENAI_EMBEDDING_DIMENSION"


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
            provider: The LLM provider to use.
            model_name: The model name served by that provider.
            temperature: Temperature setting (0.0-2.0).
            api_key: API key for the provider (if None, read from the environment).
            **kwargs: Additional provider-specific parameters.
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
            model_name=config_dict.get("model_name", DEFAULT_CHAT_MODEL),
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
            config: LLM configuration.

        Returns:
            LangChain BaseChatModel instance.

        Raises:
            ValueError: If the provider is not supported or the API key is missing.
        """
        api_key = config.api_key or LLMFactory._get_api_key_for_provider(config.provider)
        if not api_key:
            raise ValueError(
                f"API key not provided for {config.provider.value}. "
                f"Set it in config or as environment variable {LLMFactory._get_env_var_name(config.provider)}"
            )

        if config.provider == LLMProvider.OPENAI:
            params = {
                "model": config.model_name,
                "temperature": config.temperature,
                "api_key": api_key,
                "base_url": get_base_url(),
            }
            params.update(config.extra_params)
            return ChatOpenAI(**params)
        if config.provider == LLMProvider.ANTHROPIC:
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
        if config.provider == LLMProvider.GOOGLE:
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
        raise ValueError(f"Unsupported provider: {config.provider}")

    @staticmethod
    def _get_api_key_for_provider(provider: LLMProvider) -> Optional[str]:
        """Get the API key from the environment variable for the given provider."""
        return os.getenv(LLMFactory._get_env_var_name(provider))

    @staticmethod
    def _get_env_var_name(provider: LLMProvider) -> str:
        """Get the environment variable name for the provider's API key."""
        mapping = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.GOOGLE: "GOOGLE_API_KEY",
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
            provider: Provider to use (defaults to OpenAI if not specified).
            model_name: Model name (defaults to the provider default).
            temperature: Temperature setting.

        Returns:
            LangChain BaseChatModel instance.
        """
        if provider is None:
            provider = LLMProvider.OPENAI
        if model_name is None:
            model_name = LLMFactory._get_default_model(provider)
        return LLMFactory.create_llm(LLMConfig(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
        ))

    @staticmethod
    def _get_default_model(provider: LLMProvider) -> str:
        """Get the default model name for the provider."""
        defaults = {
            LLMProvider.OPENAI: DEFAULT_CHAT_MODEL,
            LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
            LLMProvider.GOOGLE: "gemini-pro",
        }
        return defaults[provider]


def get_model() -> str:
    """Chat model for the task planner and the iteration suggester."""
    return _read_env(MODEL_ENV_VAR, _read_env(BATCH_MODEL_ENV_VAR, DEFAULT_CHAT_MODEL))


def get_mini_model() -> str:
    """Chat model for the modeler, the domain-area analyzer, and the summarizer."""
    return _read_env(MINI_MODEL_ENV_VAR, _read_env(BATCH_MODEL_ENV_VAR, DEFAULT_CHAT_MODEL))


def get_base_url() -> str:
    """OpenAI-compatible API origin the clients call."""
    return _read_env(BASE_URL_ENV_VAR, DEFAULT_BASE_URL).rstrip("/")


def get_embedding_model() -> str:
    """Embedding model served by the same API origin."""
    return _read_env(EMBEDDING_MODEL_ENV_VAR, DEFAULT_EMBEDDING_MODEL)


def get_embedding_dimension() -> int:
    """Vector size of the configured embedding model."""
    raw = _read_env(EMBEDDING_DIMENSION_ENV_VAR, str(DEFAULT_EMBEDDING_DIMENSION))
    return int(raw)


def create_chat_model(model_name: str, temperature: float = 0.0) -> BaseChatModel:
    """Build a chat model for one e-INFRA (or other OpenAI-compatible) model name."""
    return LLMFactory.create_llm(LLMConfig(
        provider=LLMProvider.OPENAI,
        model_name=model_name,
        temperature=temperature,
    ))


def parse_structured(messages: List[dict], schema: Type[BaseModel], model_name: str) -> BaseModel:
    """
    Ask the chat model for one structured object.

    Uses tool calling, which the e-INFRA generative models advertise, and does
    not send Responses API reasoning or verbosity parameters.
    """
    structured = create_chat_model(model_name).with_structured_output(
        schema,
        method="function_calling",
    )
    return structured.invoke(messages)


def invoke_chat(
    messages: List[dict],
    model_name: str,
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
) -> str:
    """Return the text of one chat completion."""
    chat = create_chat_model(model_name, temperature=temperature)
    if max_tokens is not None:
        chat = chat.bind(max_tokens=max_tokens)
    response = chat.invoke(messages)
    content = response.content
    if isinstance(content, str):
        return content.strip()
    parts: List[str] = []
    for part in content:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, dict):
            parts.append(str(part.get("text", "")))
    return "".join(parts).strip()


def create_embeddings(model_name: Optional[str] = None) -> OpenAIEmbeddings:
    """Build an embeddings client for the configured API origin.

    The vector size is not sent to the API. qwen3-embedding-4b already returns
    2560-dimensional vectors and rejects a dimensions parameter.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key must be provided as OPENAI_API_KEY environment variable"
        )
    return OpenAIEmbeddings(
        model=model_name or get_embedding_model(),
        api_key=api_key,
        base_url=get_base_url(),
    )


def load_llm_config_from_file(config_path: str) -> LLMConfig:
    """
    Load LLM configuration from a JSON file.

    Args:
        config_path: Path to the JSON configuration file.

    Returns:
        LLMConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as config_file:
        config_dict = json.load(config_file)

    return LLMConfig.from_dict(config_dict)


def load_llm_config_from_env() -> Optional[LLMConfig]:
    """
    Load LLM configuration from environment variables.

    Environment variables:
        LLM_PROVIDER: Provider name (openai, anthropic, google).
        LLM_MODEL_NAME: Model name.
        LLM_TEMPERATURE: Temperature (default: 0.0).

    Returns:
        LLMConfig instance, or None when neither provider nor model is set.
    """
    provider_str = os.getenv("LLM_PROVIDER")
    model_name = os.getenv(BATCH_MODEL_ENV_VAR)

    if not provider_str and not model_name:
        return None

    if provider_str:
        try:
            provider = LLMProvider(provider_str.lower())
        except ValueError:
            return None
    else:
        provider = LLMProvider.OPENAI

    if not model_name or not model_name.strip():
        model_name = get_model() if provider == LLMProvider.OPENAI else LLMFactory._get_default_model(provider)
    else:
        model_name = model_name.strip()

    temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    return LLMConfig(
        provider=provider,
        model_name=model_name,
        temperature=temperature,
    )


def resolve_llm_config() -> LLMConfig:
    """
    Resolve LLM configuration from a config file, environment variables, or defaults.

    Order:
    1. Config file, when LLM_CONFIG_FILE is set and the file exists.
    2. LLM_PROVIDER and/or LLM_MODEL_NAME.
    3. OPENAI_MODEL, then the alias mini.
    """
    config_file = os.getenv("LLM_CONFIG_FILE")
    if config_file and os.path.exists(config_file):
        return load_llm_config_from_file(config_file)

    llm_config = load_llm_config_from_env()
    if llm_config is not None:
        return llm_config

    return LLMConfig(
        provider=LLMProvider.OPENAI,
        model_name=get_model(),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
    )


def get_model_output_dir_name(config: LLMConfig) -> str:
    """Return a filesystem-safe directory name for the given model."""
    return config.model_name.replace("/", "-").replace(":", "-")


def get_llm_instance() -> BaseChatModel:
    """
    Get an LLM instance using the configured provider.

    Batch scripts use this single model. The agentic backend uses
    create_chat_model with the two role-specific names instead.
    """
    return LLMFactory.create_llm(resolve_llm_config())


def _read_env(name: str, default: str) -> str:
    """Read a setting from the environment, ignoring blank values."""
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped if stripped else default
