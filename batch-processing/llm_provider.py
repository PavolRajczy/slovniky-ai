"""Compatibility shim. The factory lives in the agentic backend."""
import sys
from pathlib import Path

_BACKEND_SRC = Path(__file__).resolve().parents[1] / "semantic-modeling-assistant-agentic-backend" / "src"
if str(_BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(_BACKEND_SRC))

from llm.provider import (  # noqa: E402
    LLMConfig,
    LLMFactory,
    LLMProvider,
    get_llm_instance,
    get_model_output_dir_name,
    load_llm_config_from_env,
    load_llm_config_from_file,
    resolve_llm_config,
)

__all__ = [
    "LLMConfig",
    "LLMFactory",
    "LLMProvider",
    "get_llm_instance",
    "get_model_output_dir_name",
    "load_llm_config_from_env",
    "load_llm_config_from_file",
    "resolve_llm_config",
]
