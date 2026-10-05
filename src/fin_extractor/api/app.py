"""FastAPI application for the Financial PDF Extractor Agent."""

import tempfile
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, HTTPException, UploadFile, status

from fin_extractor.agents import extract_financial_data
from fin_extractor.config import get_settings
from fin_extractor.models import FinancialReport
from fin_extractor.utils.logger import setup_logger

logger = setup_logger("api")

app = FastAPI(
    title="Financial PDF Extractor API",
    version="0.1.0",
    description=(
        "Enterprise API powered by Microsoft Agent Framework and Azure AI Foundry. "
        "Upload a financial PDF document to extract validated structured financial metrics."
    ),
)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, Any]:
    """Returns the service health status and Azure AI Foundry configuration state."""
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "fin-extractor-agent",
        "version": "0.1.0",
        "foundry_configured": settings.is_foundry_configured,
        "foundry_model": settings.foundry_model,
    }


@app.post(
    "/api/v1/extract",
    response_model=FinancialReport,
    status_code=status.HTTP_200_OK,
    tags=["Extraction"],
    summary="Extract structured financial metrics from an uploaded PDF",
)
async def extract_financial_metrics(
    file: Annotated[
        UploadFile,
        File(
            description="The corporate financial PDF document (e.g. 10-K, 10-Q, Earnings Release).",
        ),
    ],
) -> FinancialReport:
    """Uploads a financial statement PDF, executes the MAF extraction agent, and returns structured JSON."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a PDF file with a '.pdf' extension.",
        )

    logger.info("Received PDF upload for extraction: %s", file.filename)

    # Save uploaded file to a temporary location for the MAF tool to read
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        temp_path = Path(tmp_file.name)
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded PDF file is empty (0 bytes).",
            )
        tmp_file.write(file_bytes)

    try:
        report = await extract_financial_data(temp_path)
        return report
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Extraction error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Financial extraction failed: {exc}",
        )
    finally:
        # Clean up temporary file
        if temp_path.exists():
            temp_path.unlink()
