"""Agent implementations using Microsoft Agent Framework."""

from fin_extractor.agents.extractor_agent import (
    create_financial_agent,
    extract_financial_data,
    get_chat_client,
)
from fin_extractor.prompts import FINANCIAL_EXTRACTOR_SYSTEM_INSTRUCTIONS

__all__ = [
    "FINANCIAL_EXTRACTOR_SYSTEM_INSTRUCTIONS",
    "create_financial_agent",
    "extract_financial_data",
    "get_chat_client",
]
