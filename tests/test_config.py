"""Unit tests for configuration loading."""

import pytest

from fin_extractor.config import AppSettings


def test_config_foundry_initialization_with_env(monkeypatch: pytest.MonkeyPatch):
    """Verifies that Azure AI Foundry settings are loaded from environment variables."""
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://test-foundry.services.ai.azure.com")
    monkeypatch.setenv("FOUNDRY_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "InstrumentationKey=dummy-key;")
    monkeypatch.setenv("ENABLE_GENAI_TRACING", "false")
    monkeypatch.setenv("CAPTURE_MESSAGE_CONTENT", "false")

    settings = AppSettings()
    assert settings.foundry_project_endpoint == "https://test-foundry.services.ai.azure.com"
    assert settings.foundry_model == "gpt-4o-mini"
    assert settings.log_level == "DEBUG"
    assert settings.is_foundry_configured is True
    assert settings.applicationinsights_connection_string == "InstrumentationKey=dummy-key;"
    assert settings.is_tracing_configured is True
    assert settings.enable_genai_tracing is False
    assert settings.capture_message_content is False


def test_config_defaults():
    """Verifies default values when no environment variables are set."""
    settings = AppSettings(
        foundry_project_endpoint=None,
        applicationinsights_connection_string=None,
        _env_file=None,
    )
    assert settings.foundry_project_endpoint is None
    assert settings.foundry_model == "gpt-4o"
    assert settings.log_level == "INFO"
    assert settings.is_foundry_configured is False
    assert settings.applicationinsights_connection_string is None
    assert settings.is_tracing_configured is False
    assert settings.enable_genai_tracing is True
    assert settings.capture_message_content is True


def test_config_initialization_with_kwargs():
    """Verifies instantiation using Python constructor keyword arguments."""
    settings = AppSettings(
        foundry_project_endpoint="https://custom-foundry.services.ai.azure.com",
        foundry_model="gpt-4o",
        log_level="WARNING",
        applicationinsights_connection_string="InstrumentationKey=custom-key;",
    )
    assert settings.foundry_project_endpoint == "https://custom-foundry.services.ai.azure.com"
    assert settings.foundry_model == "gpt-4o"
    assert settings.is_foundry_configured is True
    assert settings.log_level == "WARNING"
    assert settings.applicationinsights_connection_string == "InstrumentationKey=custom-key;"
    assert settings.is_tracing_configured is True
