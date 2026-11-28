"""Unit tests for resolving agent model names from the environment."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agents import model_config


def _clear_model_env(monkeypatch):
    monkeypatch.delenv(model_config.MODEL_ENV_VAR, raising=False)
    monkeypatch.delenv(model_config.MINI_MODEL_ENV_VAR, raising=False)
    monkeypatch.delenv("LLM_MODEL_NAME", raising=False)


def test_defaults_to_the_einfra_alias_when_unset(monkeypatch):
    _clear_model_env(monkeypatch)

    assert model_config.get_model() == "mini"
    assert model_config.get_mini_model() == "mini"


def test_environment_overrides_the_defaults(monkeypatch):
    monkeypatch.setenv(model_config.MODEL_ENV_VAR, "kimi")
    monkeypatch.setenv(model_config.MINI_MODEL_ENV_VAR, "deepseek")

    assert model_config.get_model() == "kimi"
    assert model_config.get_mini_model() == "deepseek"


def test_the_two_tiers_are_independent(monkeypatch):
    _clear_model_env(monkeypatch)
    monkeypatch.setenv(model_config.MODEL_ENV_VAR, "kimi")

    assert model_config.get_model() == "kimi"
    assert model_config.get_mini_model() == "mini"


def test_batch_model_name_is_the_fallback(monkeypatch):
    _clear_model_env(monkeypatch)
    monkeypatch.setenv("LLM_MODEL_NAME", "glm")

    assert model_config.get_model() == "glm"
    assert model_config.get_mini_model() == "glm"


def test_surrounding_whitespace_is_ignored(monkeypatch):
    monkeypatch.setenv(model_config.MODEL_ENV_VAR, "  kimi \n")

    assert model_config.get_model() == "kimi"


def test_blank_value_falls_back_to_the_default(monkeypatch):
    """An empty line in .env must not turn into an empty model name."""
    _clear_model_env(monkeypatch)
    monkeypatch.setenv(model_config.MODEL_ENV_VAR, "   ")
    monkeypatch.setenv(model_config.MINI_MODEL_ENV_VAR, "")

    assert model_config.get_model() == "mini"
    assert model_config.get_mini_model() == "mini"
