"""Application configuration settings for Azure AI Foundry and Azure OpenAI."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Unified application settings supporting Azure AI Foundry and Azure OpenAI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # --- Azure AI Foundry Configuration ---
    foundry_project_endpoint: Optional[str] = Field(
        None,
        alias="FOUNDRY_PROJECT_ENDPOINT",
        description="Azure AI Foundry project endpoint (e.g. https://<project>.services.ai.azure.com)",
    )
    foundry_model: str = Field(
        "gpt-4o",
        alias="FOUNDRY_MODEL",
        description="Model deployment name in Azure AI Foundry (e.g. gpt-4o, gpt-4o-mini)",
    )

    # --- Azure OpenAI Direct Configuration ---
    azure_openai_endpoint: Optional[str] = Field(
        None,
        alias="AZURE_OPENAI_ENDPOINT",
        description="Azure OpenAI endpoint URL (e.g. https://<resource>.openai.azure.com/)",
    )
    azure_openai_api_key: Optional[str] = Field(
        None,
        alias="AZURE_OPENAI_API_KEY",
        description="Azure OpenAI API key",
    )
    azure_openai_deployment_name: str = Field(
        "gpt-4o",
        alias="AZURE_OPENAI_DEPLOYMENT_NAME",
        description="Name of the deployed model in Azure OpenAI",
    )
    azure_openai_api_version: str = Field(
        "2024-08-01-preview",
        alias="AZURE_OPENAI_API_VERSION",
        description="Target Azure OpenAI API version",
    )

    # --- General Application Settings ---
    log_level: str = Field(
        "INFO",
        alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    @property
    def is_foundry_configured(self) -> bool:
        """Returns True if Azure AI Foundry project endpoint is configured."""
        return bool(self.foundry_project_endpoint)

    @property
    def is_azure_openai_configured(self) -> bool:
        """Returns True if Azure OpenAI direct endpoint is configured."""
        return bool(self.azure_openai_endpoint)


# Alias for backward compatibility
AzureOpenAISettings = AppSettings


def get_settings() -> AppSettings:
    """Helper to instantiate and return application settings."""
    return AppSettings()