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


def test_config_prompt_shield_settings(monkeypatch: pytest.MonkeyPatch):
    """Verifies that Prompt Shield settings and endpoint auto-derivation work as expected."""
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://fin-hub.services.ai.azure.com/api/projects/proj-1")
    monkeypatch.setenv("ENABLE_PROMPT_SHIELD", "true")

    settings = AppSettings()
    assert settings.enable_prompt_shield is True
    assert settings.resolved_content_safety_endpoint == "https://fin-hub.services.ai.azure.com"
    assert settings.is_prompt_shield_configured is True
    assert settings.content_safety_api_version == "2024-09-01"

    # When explicit CONTENT_SAFETY_ENDPOINT and API version are set
    monkeypatch.setenv("CONTENT_SAFETY_ENDPOINT", "https://custom-safety.cognitiveservices.azure.com")
    monkeypatch.setenv("CONTENT_SAFETY_API_VERSION", "2024-09-15-preview")
    settings2 = AppSettings()
    assert settings2.resolved_content_safety_endpoint == "https://custom-safety.cognitiveservices.azure.com"
    assert settings2.is_prompt_shield_configured is True
    assert settings2.content_safety_api_version == "2024-09-15-preview"
