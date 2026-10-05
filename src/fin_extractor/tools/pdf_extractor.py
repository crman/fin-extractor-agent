"""Simple PDF text extraction tool for Microsoft Agent Framework."""

from pathlib import Path
from typing import Annotated, Optional

import pymupdf
from agent_framework import tool

from fin_extractor.utils.logger import setup_logger

logger = setup_logger("pdf_extractor")


def read_pdf_text(file_path: str, pages: Optional[list[int]] = None) -> str:
    """Reads and extracts text from a PDF file page by page using PyMuPDF.

    Args:
        file_path: Path to the PDF file.
        pages: Optional list of 1-based page numbers. If None, extracts all pages.

    Returns:
        Formatted string containing document metadata and page text.
    """
    path = Path(file_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    doc = pymupdf.open(str(path))
    total_pages = len(doc)
    if total_pages == 0:
        doc.close()
        raise ValueError(f"PDF document is empty: {path}")

    # Determine which pages to read (1-based indexing)
    target_pages = [p for p in pages if 1 <= p <= total_pages] if pages else list(range(1, total_pages + 1))

    logger.info("Reading %d page(s) from %s", len(target_pages), path.name)

    output_parts = [
        f"# Document: {path.name}",
        f"- Total Pages: {total_pages}",
        f"- Extracted Pages: {target_pages}",
        "---",
    ]

    for page_num in target_pages:
        page = doc[page_num - 1]
        page_text = page.get_text("text").strip()
        output_parts.append(f"--- PAGE {page_num} ---\n{page_text}")

    doc.close()
    return "\n\n".join(output_parts)


# ==============================================================================
# Microsoft Agent Framework (MAF) Tool Definition
# ==============================================================================
@tool(
    name="extract_pdf_text",
    description="Extracts the text content from a financial PDF document page by page.",
)
def extract_pdf_tool(
    file_path: Annotated[str, "The file path to the financial PDF document."],
    pages: Annotated[
        Optional[list[int]],
        "Optional list of 1-based page numbers to extract. Defaults to all pages.",
    ] = None,
) -> str:
    """Tool callable by Microsoft Agent Framework agents to read PDF text."""
    return read_pdf_text(file_path=file_path, pages=pages)
