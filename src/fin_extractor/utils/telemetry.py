"""OpenTelemetry and Azure AI Foundry tracing integration.

Provides centralized configuration for exporting GenAI traces to Azure Application
Insights, enabling rich waterfall visualization and latency profiling directly
inside the Azure AI Foundry portal Tracing explorer.
"""

import os

from opentelemetry import trace
from opentelemetry.trace import Tracer

from fin_extractor.config import AppSettings, get_settings
from fin_extractor.utils.logger import setup_logger

logger = setup_logger("telemetry")

_IS_TRACING_CONFIGURED: bool = False


def get_tracer(name: str = "fin_extractor") -> Tracer:
    """Returns an OpenTelemetry tracer instance.

    Args:
        name: The instrumentation scope name for the tracer.

    Returns:
        Tracer: Active OpenTelemetry tracer.
    """
    return trace.get_tracer(name)


def is_tracing_active() -> bool:
    """Returns True if OpenTelemetry tracing is successfully configured and active."""
    return _IS_TRACING_CONFIGURED


def configure_tracing(settings: AppSettings | None = None) -> bool:
    """Configures OpenTelemetry tracing and exports spans to Azure AI Foundry / Application Insights.

    Args:
        settings: Optional custom AppSettings instance.

    Returns:
        bool: True if tracing was successfully initialized, False otherwise.
    """
    global _IS_TRACING_CONFIGURED
    if _IS_TRACING_CONFIGURED:
        return True

    cfg = settings or get_settings()

    if not cfg.enable_genai_tracing:
        logger.info("OpenTelemetry tracing is disabled via ENABLE_GENAI_TRACING=false.")
        return False

    # 1. Resolve Application Insights connection string
    connection_string = cfg.applicationinsights_connection_string

    if not connection_string and cfg.is_foundry_configured:
        # Dynamically discover Application Insights connection string from Foundry Project
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential

            project_client = AIProjectClient(
                endpoint=cfg.foundry_project_endpoint,
                credential=DefaultAzureCredential(),
            )
            connection_string = project_client.telemetry.get_application_insights_connection_string()
            logger.info("Dynamically discovered Application Insights connection string from Foundry Project.")
        except Exception as exc:  # noqa: BLE001 - Resilient fallback if credentials or network fail
            logger.debug("Automatic discovery of Application Insights connection string skipped: %s", exc)

    if not connection_string:
        logger.info(
            "Application Insights connection string not configured. "
            "Set APPLICATIONINSIGHTS_CONNECTION_STRING in .env to enable Azure AI Foundry tracing."
        )
        return False

    try:
        # 2. Configure GenAI experimental flags and content capture
        if cfg.enable_genai_tracing:
            os.environ["AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING"] = "true"
        if cfg.capture_message_content:
            os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"
            os.environ["ENABLE_SENSITIVE_DATA"] = "true"
            try:
                from agent_framework.observability import enable_sensitive_telemetry

                enable_sensitive_telemetry()
            except Exception as exc:  # noqa: BLE001 - Optional MAF feature
                logger.debug("MAF enable_sensitive_telemetry skipped: %s", exc)

        # 3. Configure Azure Monitor OpenTelemetry Distro
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=connection_string,
            enable_live_metrics=True,
        )

        # 4. Instrument Azure AI Projects SDK if available
        try:
            from azure.ai.projects.telemetry import AIProjectInstrumentor

            ai_instrumentor = AIProjectInstrumentor()
            if not ai_instrumentor.is_instrumented():
                ai_instrumentor.instrument(
                    enable_content_recording=cfg.capture_message_content,
                )
        except Exception as exc:  # noqa: BLE001 - Non-blocking optional instrumentor
            logger.debug("AIProjectInstrumentor instrumentation skipped: %s", exc)

        # 5. Instrument OpenAI SDK for GenAI semantic conventions (prompts, tokens, latency)
        try:
            from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor

            openai_instrumentor = OpenAIInstrumentor()
            if not openai_instrumentor.is_instrumented():
                openai_instrumentor.instrument()
        except Exception as exc:  # noqa: BLE001 - Non-blocking optional instrumentor
            logger.debug("OpenAIInstrumentor instrumentation skipped: %s", exc)

        _IS_TRACING_CONFIGURED = True
        logger.info("Azure AI Foundry OpenTelemetry tracing initialized successfully.")
        return True

    except Exception as exc:  # noqa: BLE001 - Resilient error handling for telemetry setup
        logger.warning("Failed to configure Azure Monitor OpenTelemetry tracing: %s", exc)
        return False
