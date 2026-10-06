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

    # --- Observability & Tracing (Application Insights) ---
    applicationinsights_connection_string: str | None = Field(
        None,
        alias="APPLICATIONINSIGHTS_CONNECTION_STRING",
        description="Azure Application Insights connection string for OpenTelemetry tracing.",
    )
    enable_genai_tracing: bool = Field(
        True,
        alias="ENABLE_GENAI_TRACING",
        description="Enable OpenTelemetry tracing for GenAI and Azure AI Foundry.",
    )
    capture_message_content: bool = Field(
        True,
        alias="CAPTURE_MESSAGE_CONTENT",
        description="Capture full LLM input prompts and completion contents in traces.",
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
    def is_tracing_configured(self) -> bool:
        """Returns True if Application Insights connection string is configured."""
        return bool(self.applicationinsights_connection_string)


def get_settings() -> AppSettings:
    """Helper to instantiate and return application settings."""
    return AppSettings()