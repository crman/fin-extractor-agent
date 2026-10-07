"""FastAPI application for the Financial PDF Extractor Agent."""

import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, HTTPException, UploadFile, status

from fin_extractor.agents import extract_financial_data
from fin_extractor.config import get_settings
from fin_extractor.models import FinancialReport
from fin_extractor.security import DocumentInjectionError, PromptShieldError
from fin_extractor.utils import configure_tracing, is_tracing_active, setup_logger

logger = setup_logger("api")
setup_logger("skills_runner")
setup_logger("agent_framework")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    configure_tracing()
    yield


app = FastAPI(
    title="Financial PDF Extractor API",
    version="0.1.0",
    description=(
        "Enterprise API powered by Microsoft Agent Framework and Azure AI Foundry. "
        "Upload a financial PDF document to extract validated structured financial metrics."
    ),
    lifespan=lifespan,
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
        "tracing_configured": is_tracing_active() or settings.is_tracing_configured,
        "prompt_shield_enabled": settings.is_prompt_shield_configured,
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
    except DocumentInjectionError as exc:
        logger.warning("Indirect prompt injection detected in uploaded PDF: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "SecurityViolation",
                "attack_type": exc.attack_type,
                "page": exc.page_number,
                "message": exc.message,
            },
        )
    except PromptShieldError as exc:
        logger.warning("Prompt safety violation detected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "SecurityViolation",
                "attack_type": exc.attack_type,
                "message": exc.message,
            },
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Financial extraction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Financial extraction failed: {exc}",
        )
    finally:
        # Clean up temporary file
        if temp_path.exists():
            temp_path.unlink()
