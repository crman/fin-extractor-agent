"""Pytest configuration and telemetry isolation fixtures."""

from collections.abc import Generator
from unittest.mock import patch

import pytest

_PATCHERS = []


def pytest_configure(config: pytest.Config) -> None:
    """Disarms live Azure Monitor export before any test module is imported."""
    p1 = patch("azure.monitor.opentelemetry.configure_azure_monitor")
    p2 = patch("azure.ai.projects.telemetry.AIProjectInstrumentor")
    p3 = patch("opentelemetry.instrumentation.openai_v2.OpenAIInstrumentor")
    p1.start()
    p2.start()
    p3.start()
    _PATCHERS.extend([p1, p2, p3])


def pytest_unconfigure(config: pytest.Config) -> None:
    """Stops all mock patchers on test suite shutdown."""
    for p in reversed(_PATCHERS):
        p.stop()
    _PATCHERS.clear()


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
