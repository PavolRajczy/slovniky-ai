"""
Central resolution of the OpenAI model names used by the agents.

Models are read from the environment so they can be changed without editing code,
which matters because access to a given model differs per OpenAI project:

    OPENAI_MODEL       main reasoning model  (task planner, iteration suggester)
    OPENAI_MODEL_MINI  cheaper reasoning model (modeler, domain area analyzer)

Both default to the gpt-5 family. Agents call these through the Responses API with
`reasoning` and `verbosity`, so a replacement must be a reasoning model as well.
"""
import os

from dotenv import load_dotenv

load_dotenv()


DEFAULT_MODEL = "gpt-5"
DEFAULT_MINI_MODEL = "gpt-5-mini"

MODEL_ENV_VAR = "OPENAI_MODEL"
MINI_MODEL_ENV_VAR = "OPENAI_MODEL_MINI"


def get_model() -> str:
    """Main reasoning model, used where planning quality matters most."""
    return _read_env(MODEL_ENV_VAR, DEFAULT_MODEL)


def get_mini_model() -> str:
    """Cheaper reasoning model, used for the higher-volume agent calls."""
    return _read_env(MINI_MODEL_ENV_VAR, DEFAULT_MINI_MODEL)


def _read_env(name: str, default: str) -> str:
    """Read a model name from the environment, ignoring blank values."""
    value = os.getenv(name)
    if value is None:
        return default

    stripped = value.strip()
    return stripped if stripped else default
