"""Application configuration settings for Azure AI Foundry."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings for Azure AI Foundry."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # --- Azure AI Foundry Configuration ---
    foundry_project_endpoint: str | None = Field(
        None,
        alias="FOUNDRY_PROJECT_ENDPOINT",
        description="Azure AI Foundry project endpoint (e.g. https://<project>.services.ai.azure.com)",
    )
    foundry_model: str = Field(
        "gpt-4o",
        alias="FOUNDRY_MODEL",
        description="Model deployment name in Azure AI Foundry (e.g. gpt-4o, gpt-4o-mini)",
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


def get_settings() -> AppSettings:
    """Helper to instantiate and return application settings."""
    return AppSettings()