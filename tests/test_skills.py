"""Unit and integration tests for Microsoft Agent Framework Skills integration."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from agent_framework import Agent, SkillsProvider

from fin_extractor.agents import create_financial_agent
from fin_extractor.config import AppSettings
from fin_extractor.models import FinancialReport
from fin_extractor.skills import create_skills_provider
from fin_extractor.skills.runner import execute_skill_script as runner_execute


@pytest.mark.asyncio
async def test_skills_provider_discovery():
    """Verifies that create_skills_provider discovers both financial-auditor and currency-normalizer skills."""
    provider = create_skills_provider()
    assert isinstance(provider, SkillsProvider)

    skills = await provider._source.get_skills(None)
    skill_names = {s.frontmatter.name for s in skills}

    assert "financial-auditor" in skill_names
    assert "currency-normalizer" in skill_names


@pytest.mark.asyncio
async def test_skills_frontmatter_metadata():
    """Verifies frontmatter compliance with the Agent Skills specification."""
    provider = create_skills_provider()
    skills = await provider._source.get_skills(None)

    auditor_skill = next(s for s in skills if s.frontmatter.name == "financial-auditor")
    assert "balance sheet" in auditor_skill.frontmatter.description.lower()
    assert auditor_skill.frontmatter.license == "Apache-2.0"

    currency_skill = next(s for s in skills if s.frontmatter.name == "currency-normalizer")
    assert "foreign" in currency_skill.frontmatter.description.lower()
    assert currency_skill.frontmatter.license == "Apache-2.0"


@pytest.mark.asyncio
async def test_read_audit_rules_resource():
    """Verifies that financial-auditor's audit_rules.json resource is readable and valid."""
    provider = create_skills_provider()
    skills = await provider._source.get_skills(None)
    auditor_skill = next(s for s in skills if s.frontmatter.name == "financial-auditor")

    resource = await auditor_skill.get_resource("resources/audit_rules.json")
    assert resource is not None
    content = await resource.read()
    assert "balance_sheet_equation" in content
    assert "net_profit_margin" in content


@pytest.mark.asyncio
async def test_read_exchange_rates_resource():
    """Verifies that currency-normalizer's exchange_rates.json resource is readable and valid."""
    provider = create_skills_provider()
    skills = await provider._source.get_skills(None)
    currency_skill = next(s for s in skills if s.frontmatter.name == "currency-normalizer")

    resource = await currency_skill.get_resource("resources/exchange_rates.json")
    assert resource is not None
    content = await resource.read()
    assert "rates_to_usd" in content
    assert "EUR" in content


@pytest.mark.asyncio
async def test_financial_auditor_script_execution_pass():
    """Verifies that audit_calc.py correctly validates balanced financial statements."""
    provider = create_skills_provider()
    skills = await provider._source.get_skills(None)
    auditor_skill = next(s for s in skills if s.frontmatter.name == "financial-auditor")
    script = await auditor_skill.get_script("scripts/audit_calc.py")
    assert script is not None

    payload = {
        "total_assets": 50000.0,
        "total_liabilities": 30000.0,
        "total_equity": 20000.0,
        "total_revenue": 50000.0,
        "net_income": 12000.0,
        "cash_and_equivalents": 15000.0,
    }
    result = await script.run(auditor_skill, payload)

    assert isinstance(result, dict)
    assert result["verdict"] == "PASSED"
    assert result["net_profit_margin_pct"] == 24.0
    assert result["cash_ratio_pct"] == 30.0
    assert len(result["issues"]) == 0
    assert any("Balanced" in c for c in result["checks"])


@pytest.mark.asyncio
async def test_financial_auditor_script_execution_warning():
    """Verifies that audit_calc.py flags imbalanced balance sheets and abnormal margins."""
    provider = create_skills_provider()
    skills = await provider._source.get_skills(None)
    auditor_skill = next(s for s in skills if s.frontmatter.name == "financial-auditor")
    script = await auditor_skill.get_script("scripts/audit_calc.py")

    payload = {
        "total_assets": 50000.0,
        "total_liabilities": 40000.0,
        "total_equity": 30000.0,  # 40000 + 30000 = 70000 != 50000
        "total_revenue": 10000.0,
        "net_income": 20000.0,  # 200% margin (anomaly)
    }
    result = await script.run(auditor_skill, payload)

    assert result["verdict"] == "WARNING"
    assert len(result["issues"]) >= 2
    assert any("Mismatch" in i for i in result["issues"])
    assert any("Anomalous Net Profit Margin" in i for i in result["issues"])


@pytest.mark.asyncio
async def test_currency_converter_script_execution():
    """Verifies that convert_currency.py converts foreign figures into USD."""
    provider = create_skills_provider()
    skills = await provider._source.get_skills(None)
    curr_skill = next(s for s in skills if s.frontmatter.name == "currency-normalizer")
    script = await curr_skill.get_script("scripts/convert_currency.py")
    assert script is not None

    payload = {
        "amount": 1000.0,
        "from_currency": "EUR",
        "to_currency": "USD",
    }
    result = await script.run(curr_skill, payload)

    assert isinstance(result, dict)
    assert result["from_currency"] == "EUR"
    assert result["to_currency"] == "USD"
    assert result["converted_amount"] == 1085.0
    assert "Converted 1,000.00 EUR to 1,085.00 USD" in result["note"]


def test_agent_skills_wiring_enabled():
    """Verifies that create_financial_agent registers SkillsProvider when enable_skills=True."""
    mock_client = MagicMock()
    settings = AppSettings(
        foundry_project_endpoint="https://test.services.ai.azure.com",
        enable_skills=True,
    )
    agent = create_financial_agent(client=mock_client, settings=settings)

    assert isinstance(agent, Agent)
    assert agent.context_providers is not None
    assert len(agent.context_providers) == 1
    assert isinstance(agent.context_providers[0], SkillsProvider)


def test_agent_skills_wiring_disabled():
    """Verifies that create_financial_agent omits SkillsProvider when enable_skills=False."""
    mock_client = MagicMock()
    settings = AppSettings(
        foundry_project_endpoint="https://test.services.ai.azure.com",
        enable_skills=False,
    )
    agent = create_financial_agent(client=mock_client, settings=settings)

    assert isinstance(agent, Agent)
    assert not agent.context_providers


def test_financial_report_schema_with_audit_fields():
    """Verifies that FinancialReport serializes and deserializes skill audit metadata."""
    report = FinancialReport(
        company_name="TechNova Solutions Inc.",
        reporting_period="Q3 2026",
        currency="EUR",
        normalized_currency="USD",
        total_revenue=50000.0,
        net_income=12000.0,
        audit_status="PASSED",
        audit_checks=[
            "Balance sheet equation reconciled",
            "Net margin 24.0% verified",
        ],
        summary="Audit passed successfully.",
    )

    data = report.model_dump()
    assert data["audit_status"] == "PASSED"
    assert data["normalized_currency"] == "USD"
    assert len(data["audit_checks"]) == 2

    # Roundtrip validation
    reloaded = FinancialReport.model_validate(data)
    assert reloaded.audit_status == "PASSED"
    assert reloaded.normalized_currency == "USD"
    assert reloaded.audit_checks == report.audit_checks


def test_skills_runner_direct_invocation():
    """Verifies that execute_skill_script runner executes successfully."""
    script_path = Path("src/fin_extractor/skills/financial-auditor/scripts/audit_calc.py")
    mock_script = MagicMock()
    mock_script.full_path = script_path
    mock_script.name = "audit_calc.py"
    mock_skill = MagicMock()

    payload = {"total_assets": 1000.0, "total_liabilities": 600.0, "total_equity": 400.0}
    out = runner_execute(mock_skill, mock_script, payload)
    assert isinstance(out, dict)
    assert out["verdict"] == "PASSED"


def test_audit_calc_cli_positional_and_named_args():
    """Verifies that audit_calc accepts positional numbers and named flags via runner."""
    script_path = Path("src/fin_extractor/skills/financial-auditor/scripts/audit_calc.py")
    mock_script = MagicMock(full_path=script_path, name="audit_calc.py")
    mock_skill = MagicMock()

    # Positional list: [assets, liabilities, equity, revenue, net_income, cash]
    pos_args = ["50000", "30000", "20000", "50000", "12000", "15000"]
    out = runner_execute(mock_skill, mock_script, pos_args)
    assert isinstance(out, dict)
    assert out["verdict"] == "PASSED"
    assert len(out["checks"]) == 3

    # Named flags: --total_assets 50000 --total_liabilities 30000
    flag_args = ["--total_assets", "50000", "--total_liabilities", "30000"]
    out_flag = runner_execute(mock_skill, mock_script, flag_args)
    assert isinstance(out_flag, dict)
    assert out_flag["verdict"] == "PASSED"


def test_convert_currency_cli_positional_and_named_args():
    """Verifies that convert_currency accepts positional arguments and named flags via runner."""
    script_path = Path("src/fin_extractor/skills/currency-normalizer/scripts/convert_currency.py")
    mock_script = MagicMock(full_path=script_path, name="convert_currency.py")
    mock_skill = MagicMock()

    # Positional list: [amount, from_currency, to_currency]
    pos_args = ["1000", "EUR", "USD"]
    out = runner_execute(mock_skill, mock_script, pos_args)
    assert isinstance(out, dict)
    assert out["converted_amount"] == 1085.0

    # Same currency (USD to USD)
    same_args = ["50000", "USD", "USD"]
    out_same = runner_execute(mock_skill, mock_script, same_args)
    assert isinstance(out_same, dict)
    assert out_same["converted_amount"] == 50000.0
    assert out_same["effective_rate"] == 1.0
