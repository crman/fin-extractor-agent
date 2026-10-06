"""Unit tests for OpenTelemetry and Azure AI Foundry tracing integration."""

from unittest.mock import MagicMock, patch

from fin_extractor.config import AppSettings
from fin_extractor.utils.telemetry import configure_tracing, get_tracer


def test_get_tracer():
    """Verifies that get_tracer returns a valid OpenTelemetry tracer."""
    tracer = get_tracer("test_scope")
    assert tracer is not None
    assert hasattr(tracer, "start_as_current_span")


def test_configure_tracing_disabled_when_no_credentials():
    """Verifies that configure_tracing gracefully returns False when no App Insights connection string exists."""
    settings = AppSettings(
        foundry_project_endpoint=None,
        applicationinsights_connection_string=None,
        _env_file=None,
    )
    with patch("fin_extractor.utils.telemetry._IS_TRACING_CONFIGURED", False):
        result = configure_tracing(settings=settings)
        assert result is False


def test_configure_tracing_success_with_connection_string():
    """Verifies that configure_tracing initializes Azure Monitor when connection string is provided."""
    settings = AppSettings(
        applicationinsights_connection_string="InstrumentationKey=00000000-0000-0000-0000-000000000000;IngestionEndpoint=https://test.in.applicationinsights.azure.com/;",
        enable_genai_tracing=True,
        capture_message_content=True,
        _env_file=None,
    )

    with (
        patch("fin_extractor.utils.telemetry._IS_TRACING_CONFIGURED", False),
        patch("azure.monitor.opentelemetry.configure_azure_monitor") as mock_azure_monitor,
        patch("azure.ai.projects.telemetry.AIProjectInstrumentor") as mock_ai_proj_cls,
        patch("opentelemetry.instrumentation.openai_v2.OpenAIInstrumentor") as mock_openai_cls,
    ):
        mock_ai_inst = MagicMock()
        mock_ai_inst.is_instrumented.return_value = False
        mock_ai_proj_cls.return_value = mock_ai_inst

        mock_openai_inst = MagicMock()
        mock_openai_inst.is_instrumented.return_value = False
        mock_openai_cls.return_value = mock_openai_inst

        result = configure_tracing(settings=settings)

        assert result is True
        mock_azure_monitor.assert_called_once()
        mock_ai_inst.instrument.assert_called_once_with(enable_content_recording=True)
        mock_openai_inst.instrument.assert_called_once()


def test_configure_tracing_handles_exception_gracefully():
    """Verifies that configure_tracing does not raise exceptions if Azure Monitor setup fails."""
    settings = AppSettings(
        applicationinsights_connection_string="InstrumentationKey=faulty-key;",
        _env_file=None,
    )

    with (
        patch("fin_extractor.utils.telemetry._IS_TRACING_CONFIGURED", False),
        patch("azure.monitor.opentelemetry.configure_azure_monitor", side_effect=RuntimeError("Network failure")),
    ):
        result = configure_tracing(settings=settings)
        assert result is False
