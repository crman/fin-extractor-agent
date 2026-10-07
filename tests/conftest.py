"""Pytest configuration and telemetry isolation fixtures."""

from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True, scope="session")
def disable_live_azure_telemetry_in_tests() -> Generator[None, None, None]:
    """Isolates unit tests from live Azure Application Insights export.

    Prevents pytest from attaching live Azure Monitor exporters to the tracer,
    ensuring test spans run in-memory and do not pollute the Azure AI Foundry
    Tracing dashboard.
    """
    with (
        patch("azure.monitor.opentelemetry.configure_azure_monitor"),
        patch("azure.ai.projects.telemetry.AIProjectInstrumentor"),
        patch("opentelemetry.instrumentation.openai_v2.OpenAIInstrumentor"),
    ):
        yield
