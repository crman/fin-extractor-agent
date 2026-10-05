"""Unit tests for the Microsoft Agent Framework Financial Extractor Agent."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from agent_framework import Agent, AgentResponse
from agent_framework_foundry import FoundryChatClient

from fin_extractor.agents import (
    create_financial_agent,
    extract_financial_data,
    get_chat_client,
)
from fin_extractor.config import AppSettings
from fin_extractor.models import FinancialReport

SAMPLE_PDF = "data/samples/TechNova Q3 2026 Financial Results.pdf"


def test_create_financial_agent_structure():
    """Verifies that the agent is properly configured with tools, instructions, and schema."""
    mock_client = MagicMock()
    agent = create_financial_agent(client=mock_client)

    assert isinstance(agent, Agent)
    assert agent.name == "FinancialExtractorAgent"
    assert "predefined financial metrics" in agent.default_options["instructions"]

    # Verify tool registration
    tools = agent.default_options.get("tools", [])
    assert len(tools) == 1
    assert tools[0].name == "extract_pdf_text"

    # Verify structured response format
    assert agent.default_options.get("response_format") is FinancialReport
    assert agent.default_options.get("temperature") == 0.0


def test_get_chat_client_selects_foundry():
    """Verifies that FoundryChatClient is chosen when Foundry settings are present."""
    settings = AppSettings(
        foundry_project_endpoint="https://my-proj.services.ai.azure.com",
        foundry_model="gpt-4o",
    )
    client = get_chat_client(settings=settings)
    assert isinstance(client, FoundryChatClient)


def test_get_chat_client_raises_when_foundry_missing():
    """Verifies that an informative ValueError is raised if Azure AI Foundry is not configured."""
    settings = AppSettings(foundry_project_endpoint=None)
    with pytest.raises(ValueError, match="Azure AI Foundry is not configured"):
        get_chat_client(settings=settings)


@pytest.mark.asyncio
async def test_extract_financial_data_file_not_found():
    """Verifies that extract_financial_data raises FileNotFoundError for missing PDF."""
    with pytest.raises(FileNotFoundError):
        await extract_financial_data("non_existent_file.pdf")


@pytest.mark.asyncio
async def test_extract_financial_data_pipeline_run():
    """Verifies the automated pipeline execution flow with a mocked MAF agent."""
    mock_report = FinancialReport(
        company_name="TechNova Solutions Inc.",
        reporting_period="Q3 2026",
        currency="USD",
        total_revenue=50000.0,
        net_income=12000.0,
        diluted_eps=0.24,
        total_assets=50000.0,
        total_liabilities=30000.0,
        cash_and_equivalents=15000.0,
        summary="Strong 15% YoY revenue growth driven by cloud division.",
    )

    mock_agent = MagicMock(spec=Agent)
    mock_response = MagicMock(spec=AgentResponse)
    mock_response.value = mock_report
    mock_response.text = mock_report.model_dump_json()

    mock_agent.run = AsyncMock(return_value=mock_response)

    # Run pipeline
    result = await extract_financial_data(SAMPLE_PDF, agent=mock_agent)

    # Verify agent was called with the document path prompt
    mock_agent.run.assert_awaited_once()
    called_prompt = mock_agent.run.call_args[0][0]
    assert "TechNova Q3 2026 Financial Results.pdf" in called_prompt

    # Verify returned result
    assert isinstance(result, FinancialReport)
    assert result.company_name == "TechNova Solutions Inc."
    assert result.total_revenue == 50000.0
    assert result.net_income == 12000.0
    assert result.total_assets == 50000.0
