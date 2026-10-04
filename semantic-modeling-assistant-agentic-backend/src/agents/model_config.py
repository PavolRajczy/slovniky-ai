"""
Central resolution of the OpenAI client settings used by the agents.

Models and the API origin are read from the environment so they can be changed
without editing code, including from Docker Compose:

    OPENAI_MODEL       main reasoning model  (task planner, iteration suggester)
    OPENAI_MODEL_MINI  cheaper reasoning model (modeler, domain area analyzer)
    OPENAI_BASE_URL    OpenAI-compatible API origin, for example
                       https://llm.ai.e-infra.cz/v1/

Both models default to the gpt-5 family. Agents call these through the Responses API
with `reasoning` and `verbosity`, so a replacement must be a reasoning model as well.
When OPENAI_BASE_URL is empty, the official https://api.openai.com/v1 origin is used.
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


DEFAULT_MODEL = "gpt-5"
DEFAULT_MINI_MODEL = "gpt-5-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"

MODEL_ENV_VAR = "OPENAI_MODEL"
MINI_MODEL_ENV_VAR = "OPENAI_MODEL_MINI"
BASE_URL_ENV_VAR = "OPENAI_BASE_URL"


def get_model() -> str:
    """Main reasoning model, used where planning quality matters most."""
    return _read_env(MODEL_ENV_VAR, DEFAULT_MODEL)


def get_mini_model() -> str:
    """Cheaper reasoning model, used for the higher-volume agent calls."""
    return _read_env(MINI_MODEL_ENV_VAR, DEFAULT_MINI_MODEL)


def get_base_url() -> str:
    """OpenAI-compatible API origin the clients call."""
    return _read_env(BASE_URL_ENV_VAR, DEFAULT_BASE_URL).rstrip("/")


def create_openai_client(api_key: str) -> OpenAI:
    """Build an OpenAI client for the configured API origin."""
    return OpenAI(api_key=api_key, base_url=get_base_url())


def _read_env(name: str, default: str) -> str:
    """Read a model name from the environment, ignoring blank values."""
    value = os.getenv(name)
    if value is None:
        return default

    stripped = value.strip()
    return stripped if stripped else default
