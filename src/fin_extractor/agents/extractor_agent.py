"""Financial PDF Extractor Agent built with Microsoft Agent Framework (MAF).

Orchestrates Azure AI Foundry chat clients, binds the PDF extraction tool,
and executes the extraction loop to return validated FinancialReport structured output.
"""

from pathlib import Path
from typing import Any

from agent_framework import Agent

from fin_extractor.config import AppSettings, get_settings
from fin_extractor.models import FinancialReport
from fin_extractor.prompts import FINANCIAL_EXTRACTOR_SYSTEM_INSTRUCTIONS
from fin_extractor.tools import extract_pdf_tool
from fin_extractor.utils.logger import setup_logger

logger = setup_logger("extractor_agent")


def get_chat_client(settings: AppSettings | None = None) -> Any:
    """Instantiates the Azure AI Foundry chat client.

    Raises:
        ValueError: If FOUNDRY_PROJECT_ENDPOINT is not configured.
    """
    cfg = settings or get_settings()

    if not cfg.is_foundry_configured:
        raise ValueError(
            "Azure AI Foundry is not configured. "
            "Please set FOUNDRY_PROJECT_ENDPOINT in your .env file or environment variables."
        )

    logger.info(
        "Configuring Azure AI Foundry client: %s (model: %s)",
        cfg.foundry_project_endpoint,
        cfg.foundry_model,
    )
    from agent_framework_foundry import FoundryChatClient
    from azure.identity import DefaultAzureCredential

    return FoundryChatClient(
        project_endpoint=cfg.foundry_project_endpoint,
        model=cfg.foundry_model,
        credential=DefaultAzureCredential(),
    )


def create_financial_agent(
    client: Any | None = None,
    settings: AppSettings | None = None,
    instructions: str | None = None,
) -> Agent:
    """Creates and configures a Microsoft Agent Framework Agent for financial extraction.

    Args:
        client: Optional pre-initialized MAF chat client.
        settings: Optional custom AppSettings.
        instructions: Optional custom system instructions.

    Returns:
        Configured Agent instance with tool binding and structured response format.
    """
    chat_client = client if client is not None else get_chat_client(settings=settings)
    system_instructions = instructions or FINANCIAL_EXTRACTOR_SYSTEM_INSTRUCTIONS

    logger.info("Initializing FinancialExtractorAgent with extract_pdf_text tool.")
    return Agent(
        client=chat_client,
        name="FinancialExtractorAgent",
        description="Autonomous agent that extracts structured financial metrics from documents.",
        instructions=system_instructions,
        tools=[extract_pdf_tool],
        default_options={
            "response_format": FinancialReport,
            "temperature": 0.0,
        },
    )


async def extract_financial_data(
    pdf_path: str | Path,
    agent: Agent | None = None,
) -> FinancialReport:
    """Automated extraction pipeline: takes a PDF file path and returns validated FinancialReport.

    The user does not need to provide any prompt. The agent executes the fixed workflow:
      1. Calls extract_pdf_text tool on the document.
      2. Maps the extracted text into predefined financial metrics.
      3. Returns the structured FinancialReport.

    Args:
        pdf_path: Path to the financial PDF file to analyze.
        agent: Optional pre-configured Agent instance. If None, one is created.

    Returns:
        FinancialReport: Strongly-typed Pydantic model populated with extracted metrics.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If extraction output cannot be parsed into FinancialReport.
    """
    resolved_path = Path(pdf_path).resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Financial PDF file not found: {resolved_path}")

    active_agent = agent if agent is not None else create_financial_agent()
    internal_prompt = f"Extract the predefined financial metrics from the document at: {resolved_path}"

    logger.info("Starting automated financial extraction for: %s", resolved_path.name)
    response = await active_agent.run(internal_prompt)

    # MAF automatically parses structured output into response.value
    if response.value is not None:
        if isinstance(response.value, FinancialReport):
            return response.value
        if isinstance(response.value, dict):
            return FinancialReport.model_validate(response.value)

    # Fallback parsing from response text if value was not pre-populated
    if response.text:
        return FinancialReport.model_validate_json(response.text)

    raise ValueError(f"Agent did not return valid structured output for {resolved_path.name}")
