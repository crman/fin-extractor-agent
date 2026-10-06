"""Unit tests for FastAPI endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from fin_extractor.api.app import app
from fin_extractor.models import FinancialReport

client = TestClient(app)


def test_health_endpoint():
    """Verifies that the /health endpoint returns 200 OK and status info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "fin-extractor-agent"
    assert "foundry_configured" in data
    assert "foundry_model" in data
    assert "tracing_configured" in data
    assert "prompt_shield_enabled" in data


def test_extract_invalid_file_extension():
    """Verifies that non-PDF files return a 400 Bad Request."""
    response = client.post(
        "/api/v1/extract",
        files={"file": ("report.txt", b"Some text content", "text/plain")},
    )
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


def test_extract_empty_pdf_file():
    """Verifies that empty PDF uploads return a 400 Bad Request."""
    response = client.post(
        "/api/v1/extract",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@patch("fin_extractor.api.app.extract_financial_data", new_callable=AsyncMock)
def test_extract_endpoint_success(mock_extract):
    """Verifies that a valid PDF upload returns 200 OK and FinancialReport JSON."""
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
    mock_extract.return_value = mock_report

    # Simulate uploading a PDF
    fake_pdf_bytes = b"%PDF-1.4 simulated pdf bytes for test"
    response = client.post(
        "/api/v1/extract",
        files={"file": ("TechNova_Q3_2026.pdf", fake_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "TechNova Solutions Inc."
    assert data["reporting_period"] == "Q3 2026"
    assert data["total_revenue"] == 50000.0
    assert data["net_income"] == 12000.0
    assert data["diluted_eps"] == 0.24
    assert data["total_assets"] == 50000.0
    assert data["total_liabilities"] == 30000.0
    assert data["cash_and_equivalents"] == 15000.0
    assert "15% YoY revenue growth" in data["summary"]


@patch("fin_extractor.api.app.extract_financial_data", new_callable=AsyncMock)
def test_extract_endpoint_prompt_injection_blocked(mock_extract):
    """Verifies that detected prompt injection returns 422 Unprocessable Entity with security details."""
    from fin_extractor.security import DocumentInjectionError

    mock_extract.side_effect = DocumentInjectionError(
        page_number=2,
        message="Potential prompt injection attack detected on page 2 of the uploaded document.",
    )

    fake_pdf_bytes = b"%PDF-1.4 simulated pdf bytes for test"
    response = client.post(
        "/api/v1/extract",
        files={"file": ("malicious_report.pdf", fake_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error"] == "SecurityViolation"
    assert data["detail"]["attack_type"] == "indirect_document_injection"
    assert data["detail"]["page"] == 2
    assert "prompt injection attack detected" in data["detail"]["message"].lower()
