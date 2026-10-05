"""Unit tests for simplified predefined financial Pydantic models."""

import pytest
from pydantic import ValidationError

from fin_extractor.models import FinancialReport


def test_financial_report_required_fields():
    """Verifies validation on required company name and reporting period."""
    report = FinancialReport(
        company_name="TechNova Solutions Inc.",
        reporting_period="Q3 2026",
    )
    assert report.company_name == "TechNova Solutions Inc."
    assert report.reporting_period == "Q3 2026"
    assert report.currency == "USD"
    assert report.total_revenue is None
    assert report.net_income is None

    # Missing required field raises ValidationError
    with pytest.raises(ValidationError):
        FinancialReport(reporting_period="Q3 2026")


def test_financial_report_complete():
    """Verifies creation with all financial metrics populated."""
    report = FinancialReport(
        company_name="TechNova Solutions Inc.",
        reporting_period="Q3 2026",
        currency="USD",
        total_revenue=50000.0,
        net_income=12000.0,
        diluted_eps=0.24,
        total_assets=50000.0,
        total_liabilities=30000.0,
        cash_and_equivalents=15000.0,
        summary="Strong 15% revenue growth driven by cloud division.",
    )

    assert report.total_revenue == 50000.0
    assert report.net_income == 12000.0
    assert report.diluted_eps == 0.24
    assert report.total_assets == 50000.0
    assert report.cash_and_equivalents == 15000.0
    assert "15% revenue growth" in (report.summary or "")


def test_json_roundtrip_serialization():
    """Verifies model_dump_json and model_validate_json serialization."""
    original = FinancialReport(
        company_name="TechNova Solutions Inc.",
        reporting_period="Q3 2026",
        total_revenue=50000.0,
        net_income=12000.0,
    )

    json_str = original.model_dump_json()
    reconstructed = FinancialReport.model_validate_json(json_str)

    assert reconstructed.company_name == original.company_name
    assert reconstructed.reporting_period == original.reporting_period
    assert reconstructed.total_revenue == original.total_revenue
    assert reconstructed.net_income == original.net_income


def test_json_schema_compatibility():
    """Verifies that the model generates a valid JSON schema for MAF response_format."""
    schema = FinancialReport.model_json_schema()

    assert schema["type"] == "object"
    assert "company_name" in schema["properties"]
    assert "total_revenue" in schema["properties"]
    assert "net_income" in schema["properties"]
    assert "total_assets" in schema["properties"]
    assert schema["required"] == ["company_name", "reporting_period"]
