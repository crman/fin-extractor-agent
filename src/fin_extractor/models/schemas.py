"""Pydantic schemas defining the predefined financial output format.

Passed to Microsoft Agent Framework as the target `response_format`,
guaranteeing that the agent outputs validated, type-safe financial metrics.
"""

from pydantic import BaseModel, Field


class FinancialReport(BaseModel):
    """Predefined core financial metrics extracted from a financial document."""

    # Company & Period Identification
    company_name: str = Field(
        ...,
        description="Legal name of the reporting company (e.g. 'TechNova Solutions Inc.').",
    )
    reporting_period: str = Field(
        ...,
        description="Reporting fiscal period (e.g. 'Q3 2026', 'FY 2025').",
    )
    currency: str = Field(
        "USD",
        description="Reporting currency code (e.g. 'USD', 'EUR').",
    )

    # Key Income Statement Metrics
    total_revenue: float | None = Field(
        None,
        description="Total revenue / net sales for the period.",
    )
    net_income: float | None = Field(
        None,
        description="Net income / net profit for the period.",
    )
    diluted_eps: float | None = Field(
        None,
        description="Diluted earnings per share (EPS).",
    )

    # Key Balance Sheet Metrics
    total_assets: float | None = Field(
        None,
        description="Total assets at period end.",
    )
    total_liabilities: float | None = Field(
        None,
        description="Total liabilities at period end.",
    )
    cash_and_equivalents: float | None = Field(
        None,
        description="Cash and cash equivalents at period end.",
    )

    # Performance Summary
    summary: str | None = Field(
        None,
        description="Brief narrative summary of company performance highlights.",
    )

    # Agent Skills Audit & Normalization Metadata
    audit_status: str | None = Field(
        None,
        description="Audit verdict from the financial-auditor skill (e.g. 'PASSED', 'WARNING_EQUATION_MISMATCH').",
    )
    audit_checks: list[str] = Field(
        default_factory=list,
        description="List of specific accounting and ratio validation checks executed by skills (e.g. balance sheet equation parity, profit margin percentage, and cash liquidity ratio).",
    )
    normalized_currency: str | None = Field(
        None,
        description="Normalized currency code (e.g. 'USD'). For USD-denominated reports, set to 'USD'.",
    )
