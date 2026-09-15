"""Unit tests for resolving agent model names from the environment."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agents import model_config


def test_defaults_to_the_gpt5_family_when_unset(monkeypatch):
    monkeypatch.delenv(model_config.MODEL_ENV_VAR, raising=False)
    monkeypatch.delenv(model_config.MINI_MODEL_ENV_VAR, raising=False)

    assert model_config.get_model() == "gpt-5"
    assert model_config.get_mini_model() == "gpt-5-mini"


def test_environment_overrides_the_defaults(monkeypatch):
    monkeypatch.setenv(model_config.MODEL_ENV_VAR, "gpt-5-mini")
    monkeypatch.setenv(model_config.MINI_MODEL_ENV_VAR, "o4-mini")

    assert model_config.get_model() == "gpt-5-mini"
    assert model_config.get_mini_model() == "o4-mini"


def test_the_two_tiers_are_independent(monkeypatch):
    monkeypatch.setenv(model_config.MODEL_ENV_VAR, "gpt-5-mini")
    monkeypatch.delenv(model_config.MINI_MODEL_ENV_VAR, raising=False)

    assert model_config.get_model() == "gpt-5-mini"
    assert model_config.get_mini_model() == "gpt-5-mini"


def test_surrounding_whitespace_is_ignored(monkeypatch):
    monkeypatch.setenv(model_config.MODEL_ENV_VAR, "  gpt-5-mini \n")

    assert model_config.get_model() == "gpt-5-mini"


def test_blank_value_falls_back_to_the_default(monkeypatch):
    """An empty line in .env must not turn into an empty model name."""
    monkeypatch.setenv(model_config.MODEL_ENV_VAR, "   ")
    monkeypatch.setenv(model_config.MINI_MODEL_ENV_VAR, "")

    assert model_config.get_model() == "gpt-5"
    assert model_config.get_mini_model() == "gpt-5-mini"
