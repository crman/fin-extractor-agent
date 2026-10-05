"""Unit tests for configuration loading."""

import pytest
from fin_extractor.config import AppSettings, AzureOpenAISettings


def test_config_foundry_initialization_with_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://test-foundry.services.ai.azure.com")
    monkeypatch.setenv("FOUNDRY_MODEL", "gpt-4o-mini")

    settings = AppSettings()
    assert settings.foundry_project_endpoint == "https://test-foundry.services.ai.azure.com"
    assert settings.foundry_model == "gpt-4o-mini"
    assert settings.is_foundry_configured is True
    assert settings.is_azure_openai_configured is False


def test_config_azure_openai_initialization_with_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test-resource.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key-12345")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    settings = AzureOpenAISettings()
    assert settings.azure_openai_endpoint == "https://test-resource.openai.azure.com/"
    assert settings.azure_openai_api_key == "test-key-12345"
    assert settings.azure_openai_deployment_name == "gpt-4o"
    assert settings.azure_openai_api_version == "2024-08-01-preview"
    assert settings.log_level == "INFO"
    assert settings.is_azure_openai_configured is True


def test_config_initialization_with_kwargs():
    settings = AppSettings(
        foundry_project_endpoint="https://custom-foundry.services.ai.azure.com",
        foundry_model="gpt-4o",
        log_level="DEBUG",
    )
    assert settings.foundry_project_endpoint == "https://custom-foundry.services.ai.azure.com"
    assert settings.foundry_model == "gpt-4o"
    assert settings.is_foundry_configured is True
    assert settings.log_level == "DEBUG"

