"""
Model names and API origin for the agents.

The values are resolved in llm.provider so batch processing and the backend
share one configuration. This module keeps the names the rest of the backend
already imports.
"""
from llm.provider import (
    BASE_URL_ENV_VAR,
    MINI_MODEL_ENV_VAR,
    MODEL_ENV_VAR,
    get_base_url,
    get_mini_model,
    get_model,
)

__all__ = [
    "BASE_URL_ENV_VAR",
    "MINI_MODEL_ENV_VAR",
    "MODEL_ENV_VAR",
    "get_base_url",
    "get_mini_model",
    "get_model",
]
