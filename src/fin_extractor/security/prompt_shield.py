"""Security guardrails for input safety and prompt injection protection."""

import json
from typing import Any
from urllib.parse import urlparse

from azure.ai.contentsafety import ContentSafetyClient
from azure.core.rest import HttpRequest
from azure.identity import DefaultAzureCredential
from opentelemetry.trace import Status, StatusCode

from fin_extractor.config import AppSettings, get_settings
from fin_extractor.utils.logger import setup_logger
from fin_extractor.utils.telemetry import get_tracer

logger = setup_logger("security.prompt_shield")
tracer = get_tracer("fin_extractor.security")


try:
    from agent_framework import MiddlewareFailure

    _BaseSecurityError = MiddlewareFailure
except ImportError:
    _BaseSecurityError = Exception


class PromptShieldError(_BaseSecurityError):
    """Base exception for prompt security and safety violations.

    Inherits from MAF MiddlewareFailure to trigger fail-closed abort of the agent loop.
    """

    def __init__(self, message: str, attack_type: str = "prompt_injection"):
        super().__init__(message)
        self.message = message
        self.attack_type = attack_type


class DocumentInjectionError(PromptShieldError):
    """Raised when an indirect prompt injection attack is detected in an uploaded document."""

    def __init__(self, page_number: int | None, message: str):
        super().__init__(message, attack_type="indirect_document_injection")
        self.page_number = page_number


class UserPromptInjectionError(PromptShieldError):
    """Raised when a direct user prompt injection or jailbreak attempt is detected."""

    def __init__(self, message: str):
        super().__init__(message, attack_type="direct_prompt_injection")


DEFAULT_SHIELD_PROMPT_PATH = "/contentsafety/text:shieldPrompt"


def _get_content_safety_client(endpoint: str) -> ContentSafetyClient:
    """Instantiate and return a ContentSafetyClient with DefaultAzureCredential."""
    return ContentSafetyClient(endpoint=endpoint, credential=DefaultAzureCredential())


def _normalize_endpoint(endpoint: str) -> str:
    """Normalizes an Azure endpoint URL to scheme + netloc."""
    parsed = urlparse(endpoint)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return endpoint.rstrip("/")


def _execute_shield_prompt_request(
    client: Any,
    shield_url: str,
    documents: list[str],
    user_prompt: str = "",
) -> dict[str, Any] | None:
    """Constructs and executes the shieldPrompt REST request using the client transport pipeline.

    Args:
        client: The ContentSafetyClient instance with credentials attached.
        shield_url: Pre-computed full REST URL including action path and api-version.
        documents: List of document text strings to analyze for indirect injection.
        user_prompt: Optional direct user prompt text to analyze for jailbreak attempts.

    Returns:
        Decoded JSON dictionary response from the Content Safety service, or None on failure.
    """
    payload = {
        "userPrompt": user_prompt,
        "documents": documents,
    }
    request = HttpRequest(
        method="POST",
        url=shield_url,
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    response = client.send_request(request)

    if response.status_code == 200:
        return response.json()

    logger.warning(
        "Content Safety shieldPrompt returned non-200 status %s: %s",
        response.status_code,
        response.text,
    )
    return None


def scan_document_pages_for_injection(
    pages: dict[int, str] | list[tuple[int, str]],
    settings: AppSettings | None = None,
    client: Any | None = None,
) -> bool:
    """Scans extracted PDF document pages for indirect prompt injection attacks.

    Args:
        pages: A mapping of page numbers to extracted page text, or a list of (page_num, text) tuples.
        settings: Optional AppSettings override.
        client: Optional pre-configured client (useful for unit test injection).

    Returns:
        True if all pages are clean and safe.

    Raises:
        DocumentInjectionError: If an indirect prompt injection is detected on any page.
    """
    cfg = settings or get_settings()

    if not cfg.enable_prompt_shield:
        logger.debug("Prompt Shield screening is disabled (ENABLE_PROMPT_SHIELD=false).")
        return True

    endpoint = cfg.resolved_content_safety_endpoint
    if not endpoint and client is None:
        logger.warning(
            "Prompt Shield is enabled but no Content Safety or Foundry endpoint is configured. "
            "Skipping document injection scan."
        )
        return True

    page_items = pages.items() if isinstance(pages, dict) else pages
    total_pages = len(page_items)

    with tracer.start_as_current_span("guardrail_prompt_shield") as span:
        span.set_attribute("gen_ai.system", "azure_ai_contentsafety")
        span.set_attribute("gen_ai.operation.name", "guardrail_prompt_shield")
        span.set_attribute("security.guardrail", "prompt_shield")
        span.set_attribute("security.target", "document_text")
        span.set_attribute("security.pages_count", total_pages)
        if endpoint:
            span.set_attribute("security.endpoint", endpoint)

        try:
            safety_client = client or _get_content_safety_client(_normalize_endpoint(endpoint))

            # Pre-compute shieldPrompt REST endpoint URL once for all pages
            base_url = _normalize_endpoint(endpoint or "https://localhost")
            api_version = getattr(cfg, "content_safety_api_version", "2024-09-01")
            shield_url = f"{base_url}{DEFAULT_SHIELD_PROMPT_PATH}?api-version={api_version}"

            for page_num, page_text in page_items:
                clean_text = (page_text or "").strip()
                if not clean_text:
                    continue

                result = _execute_shield_prompt_request(
                    client=safety_client,
                    shield_url=shield_url,
                    documents=[clean_text],
                )

                if result:
                    docs_analysis = result.get("documentsAnalysis", [])
                    for doc in docs_analysis:
                        if doc.get("attackDetected", False):
                            err = DocumentInjectionError(
                                page_number=page_num,
                                message=(
                                    f"Potential prompt injection attack detected on page {page_num} "
                                    "of the uploaded document. Execution terminated for safety."
                                ),
                            )
                            span.set_status(Status(StatusCode.ERROR, description=err.message))
                            span.set_attribute("error.type", "DocumentInjectionError")
                            span.set_attribute("error.message", err.message)
                            span.set_attribute("security.attack_detected", True)
                            span.set_attribute("security.violation_page", page_num)
                            span.record_exception(err)
                            logger.warning(
                                "Security Guardrail Alert: Indirect prompt injection detected on page %d.",
                                page_num,
                            )
                            raise err

            span.set_attribute("security.attack_detected", False)
            logger.debug("Prompt Shield scan completed cleanly for %d page(s).", total_pages)
            return True

        except DocumentInjectionError:
            raise
        except Exception as exc:  # noqa: BLE001 - Non-blocking fallback for dev / connectivity hiccups
            logger.warning("Prompt Shield screening encountered an unexpected error: %s", exc)
            span.record_exception(exc)
            return True
