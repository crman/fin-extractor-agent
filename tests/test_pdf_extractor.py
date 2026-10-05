"""Unit tests for the simple PDF extraction tool."""

import pytest
from fin_extractor.tools import extract_pdf_tool, read_pdf_text

SAMPLE_PDF_PATH = "data/samples/TechNova Q3 2026 Financial Results.pdf"


def test_read_pdf_text_all_pages():
    """Verifies reading all pages of the sample PDF."""
    text = read_pdf_text(SAMPLE_PDF_PATH)

    assert "TechNova Solutions Inc." in text
    assert "--- PAGE 1 ---" in text
    assert "--- PAGE 2 ---" in text
    assert "--- PAGE 3 ---" in text
    # Checks financial metrics exist in the text
    assert "Total Revenue" in text
    assert "50,000" in text
    assert "Net Income" in text


def test_read_pdf_text_single_page():
    """Verifies reading only a single target page."""
    text = read_pdf_text(SAMPLE_PDF_PATH, pages=[2])

    assert "--- PAGE 2 ---" in text
    assert "--- PAGE 1 ---" not in text
    assert "Consolidated Statement of Income" in text


def test_read_pdf_file_not_found():
    """Verifies FileNotFoundError on non-existent path."""
    with pytest.raises(FileNotFoundError):
        read_pdf_text("invalid_file_path.pdf")


@pytest.mark.asyncio
async def test_maf_tool_invocation():
    """Verifies tool invocation through Microsoft Agent Framework."""
    content_list = await extract_pdf_tool.invoke(
        arguments={"file_path": SAMPLE_PDF_PATH, "pages": [2]}
    )

    assert isinstance(content_list, list)
    assert len(content_list) > 0
    first_item = content_list[0]
    assert hasattr(first_item, "text")
    assert "TechNova Solutions Inc." in first_item.text
    assert "Total Revenue" in first_item.text
