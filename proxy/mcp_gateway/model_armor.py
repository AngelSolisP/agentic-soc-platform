"""
Model Armor Integration — Prompt Injection & PII Protection.

Sanitizes MCP requests before they reach Chronicle and responses before
they reach the agent, using Google Cloud Model Armor API.

Protections:
    - Prompt injection / jailbreak detection
    - Malicious URL blocking
    - PII detection and redaction (configurable)
    - Dangerous content filtering

The middleware is applied in the MCP Gateway request pipeline:
    Agent → [Model Armor: sanitize input] → Chronicle MCP → [Model Armor: sanitize output] → Agent
"""

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx
import google.auth
import google.auth.transport.requests

logger = logging.getLogger(__name__)


class FilterResult(str, Enum):
    """Model Armor filter verdict."""
    SAFE = "SAFE"
    BLOCKED = "BLOCKED"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class SanitizeResult:
    """Result of a Model Armor sanitization call."""
    allowed: bool
    filter_result: FilterResult
    blocked_reason: Optional[str] = None
    sanitized_text: Optional[str] = None
    pii_redacted: bool = False
    details: Optional[dict] = None


class ModelArmorClient:
    """
    Client for Google Cloud Model Armor API.

    Uses the REST API directly via httpx for maximum compatibility
    and to reuse the existing async HTTP client from the gateway.

    Model Armor API:
        POST /v1/projects/{project}/locations/{location}/templates/{template}:sanitizeUserPrompt
        POST /v1/projects/{project}/locations/{location}/templates/{template}:sanitizeModelResponse
    """

    # Model Armor requires regional endpoints (global endpoint is discovery only)
    # Ref: https://docs.cloud.google.com/model-armor/data-residency
    BASE_URL_TEMPLATE = "https://modelarmor.{location}.rep.googleapis.com"

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        template_id: str = "agentic-soc-default",
        enabled: bool = True,
        fail_closed: bool = False,
    ):
        self._project_id = project_id
        self._location = location
        self._template_id = template_id
        self._enabled = enabled
        self._fail_closed = fail_closed
        self._token: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._credentials = None

    @property
    def base_url(self) -> str:
        return self.BASE_URL_TEMPLATE.format(location=self._location)

    @property
    def template_path(self) -> str:
        return (
            f"projects/{self._project_id}/locations/{self._location}"
            f"/templates/{self._template_id}"
        )

    def _get_auth_token(self) -> str:
        """Get OAuth2 token, caching credentials and refreshing only when expired."""
        if self._credentials is None:
            self._credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            # Always refresh on first load to obtain an initial access token.
            request = google.auth.transport.requests.Request()
            self._credentials.refresh(request)
        elif self._credentials.expired or not self._credentials.valid:
            request = google.auth.transport.requests.Request()
            self._credentials.refresh(request)

        return self._credentials.token

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10)
        return self._http_client

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def sanitize_user_prompt(self, text: str) -> SanitizeResult:
        """
        Sanitize user/agent input before forwarding to Chronicle MCP.

        Checks for:
        - Prompt injection / jailbreak attempts
        - Malicious URLs in the payload
        - Dangerous content
        """
        if not self._enabled:
            return SanitizeResult(allowed=True, filter_result=FilterResult.SAFE)

        try:
            client = await self._ensure_client()
            token = self._get_auth_token()

            url = f"{self.base_url}/v1/{self.template_path}:sanitizeUserPrompt"
            payload = {
                "userPromptData": {
                    "text": text
                }
            }

            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                logger.warning(
                    "Model Armor API error",
                    extra={
                        "status": response.status_code,
                        "body": response.text[:500],
                    },
                )
                # Configurable: fail-open (default) or fail-closed
                return SanitizeResult(
                    allowed=not self._fail_closed,
                    filter_result=FilterResult.ERROR,
                    details={"error": f"API returned {response.status_code}"},
                )

            result = response.json()
            return self._parse_sanitize_response(result, direction="input")

        except Exception as exc:
            logger.error("Model Armor sanitize_user_prompt failed", extra={"error": str(exc)})
            # Configurable: fail-open (default) or fail-closed
            return SanitizeResult(
                allowed=not self._fail_closed,
                filter_result=FilterResult.ERROR,
                details={"error": str(exc)},
            )

    async def sanitize_model_response(self, text: str) -> SanitizeResult:
        """
        Sanitize Chronicle MCP response before returning to agent.

        Checks for:
        - PII leakage (redacts if configured)
        - Malicious content in response
        """
        if not self._enabled:
            return SanitizeResult(allowed=True, filter_result=FilterResult.SAFE)

        try:
            client = await self._ensure_client()
            token = self._get_auth_token()

            url = f"{self.base_url}/v1/{self.template_path}:sanitizeModelResponse"
            payload = {
                "modelResponseData": {
                    "text": text
                }
            }

            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                logger.warning(
                    "Model Armor response sanitization error",
                    extra={"status": response.status_code},
                )
                # Configurable: fail-open (default) or fail-closed
                return SanitizeResult(
                    allowed=not self._fail_closed,
                    filter_result=FilterResult.ERROR,
                    details={"error": f"API returned {response.status_code}"},
                )

            result = response.json()
            return self._parse_sanitize_response(result, direction="output")

        except Exception as exc:
            logger.error("Model Armor sanitize_model_response failed", extra={"error": str(exc)})
            # Configurable: fail-open (default) or fail-closed
            return SanitizeResult(
                allowed=not self._fail_closed,
                filter_result=FilterResult.ERROR,
                details={"error": str(exc)},
            )

    def _parse_sanitize_response(self, response: dict, direction: str) -> SanitizeResult:
        """Parse the Model Armor API response into a SanitizeResult."""
        sanitization_result = response.get("sanitizationResult", {})
        filter_match_state = sanitization_result.get("filterMatchState", "FILTER_MATCH_STATE_UNSPECIFIED")

        # Check individual filter results (keys match Model Armor REST API response schema)
        filter_results = sanitization_result.get("filterResults", {})

        # Prompt injection / jailbreak filter
        pi_outer = filter_results.get("pi_and_jailbreak", {})
        pi_result = pi_outer.get("piAndJailbreakFilterResult", {})
        pi_match = pi_result.get("matchState", "NO_MATCH_FOUND")

        # Malicious URL filter
        url_outer = filter_results.get("malicious_uris", {})
        url_result = url_outer.get("maliciousUriFilterResult", {})
        url_match = url_result.get("matchState", "NO_MATCH_FOUND")

        # Sensitive Data Protection (PII) filter
        sdp_outer = filter_results.get("sdp", {})
        sdp_result = sdp_outer.get("sdpFilterResult", {})
        pii_result = sdp_result.get("inspectResult", {})
        pii_match = pii_result.get("matchState", "NO_MATCH_FOUND")

        # Determine if request should be blocked
        is_blocked = filter_match_state == "MATCH_FOUND"
        blocked_reasons = []

        if pi_match == "MATCH_FOUND":
            blocked_reasons.append("prompt_injection_detected")
        if url_match == "MATCH_FOUND":
            blocked_reasons.append("malicious_url_detected")

        # PII: warn but don't block (redact instead)
        pii_redacted = pii_match == "MATCH_FOUND"

        # Get sanitized text if available (PII redacted version)
        sanitized_text = sanitization_result.get("sanitizedText")

        if is_blocked:
            filter_result = FilterResult.BLOCKED
        elif pii_redacted:
            filter_result = FilterResult.WARN
        else:
            filter_result = FilterResult.SAFE

        logger.info(
            "Model Armor result",
            extra={
                "direction": direction,
                "filter_result": filter_result.value,
                "blocked_reasons": blocked_reasons,
                "pii_redacted": pii_redacted,
            },
        )

        return SanitizeResult(
            allowed=not is_blocked,
            filter_result=filter_result,
            blocked_reason=", ".join(blocked_reasons) if blocked_reasons else None,
            sanitized_text=sanitized_text,
            pii_redacted=pii_redacted,
            details={
                "filter_match_state": filter_match_state,
                "prompt_injection": pi_match,
                "malicious_uris": url_match,
                "pii_detection": pii_match,
            },
        )


def _resolve_fail_closed() -> bool:
    """Resolve fail-closed setting with backward compatibility.

    Reads MODEL_ARMOR_FAIL_MODE first (new, recommended).
    Falls back to legacy MODEL_ARMOR_FAIL_CLOSED if new var not set.
    Default: FAIL_CLOSED per Google official docs.
    """
    fail_mode = os.environ.get("MODEL_ARMOR_FAIL_MODE")
    if fail_mode is not None:
        return fail_mode.upper() == "FAIL_CLOSED"
    # Legacy env var (backward compat with existing deploys)
    legacy = os.environ.get("MODEL_ARMOR_FAIL_CLOSED")
    if legacy is not None:
        return legacy.lower() == "true"
    return True  # Default: fail-closed


def create_model_armor_client() -> ModelArmorClient:
    """Factory: create a ModelArmorClient from environment variables."""
    return ModelArmorClient(
        project_id=os.environ.get("PARTNER_PROJECT_ID", ""),
        location=os.environ.get("PARTNER_REGION", "us-central1"),
        template_id=os.environ.get("MODEL_ARMOR_TEMPLATE_ID", "agentic-soc-default"),
        enabled=os.environ.get("MODEL_ARMOR_ENABLED", "true").lower() == "true",
        fail_closed=_resolve_fail_closed(),
    )
