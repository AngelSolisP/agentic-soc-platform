"""
Authentication middleware for MCP Gateway and HITL Dashboard.

Supports two auth modes:
1. Google ID Token verification (for service-to-service calls in Cloud Run)
2. API Key verification (for local development and external integrations)

In production (Cloud Run), the preferred pattern is:
- Cloud Run IAM restricts who can invoke the service
- This middleware additionally verifies the caller identity from the token

In development (DEV_MODE=true), auth is disabled entirely.
"""

import logging
import os
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

def _is_dev_mode() -> bool:
    """Check DEV_MODE at runtime (not import time) for testability."""
    return os.environ.get("DEV_MODE", "false").lower() == "true"


def _get_api_keys() -> set:
    return set(filter(None, os.environ.get("API_KEYS", "").split(",")))


def _get_allowed_callers() -> set:
    return set(filter(None, os.environ.get("ALLOWED_CALLERS", "").split(",")))


def _get_expected_audience() -> Optional[str]:
    """The service URL this gateway expects in token `aud` claim.

    Set EXPECTED_AUDIENCE to the Cloud Run service URL
    (e.g. https://your-mcp-gateway-url.run.app). Required outside DEV_MODE.
    """
    return os.environ.get("EXPECTED_AUDIENCE") or None


def _verify_google_id_token(token: str) -> dict:
    """Verify a Google-issued ID token and return claims.

    Audience verification is enforced: tokens minted for other services
    (even by the same caller) are rejected. This prevents token-replay
    attacks where an attacker obtains a valid Google ID token from any
    Google API call and tries to authenticate against this gateway.
    """
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request as GoogleRequest

    audience = _get_expected_audience()
    if not audience:
        raise HTTPException(
            status_code=500,
            detail="EXPECTED_AUDIENCE is not configured — refusing to verify tokens.",
        )

    try:
        claims = id_token.verify_oauth2_token(token, GoogleRequest(), audience=audience)
        return claims
    except Exception:
        try:
            claims = id_token.verify_token(token, GoogleRequest(), audience=audience)
            return claims
        except Exception as exc:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {exc}",
            )


async def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency that enforces authentication.

    Returns caller identity dict with at least {"email": str, "auth_method": str}.

    Auth methods (tried in order):
    1. DEV_MODE=true → skip auth, return dev identity
    2. Bearer token is an API key → return API key identity
    3. Bearer token is a Google ID token → verify and return claims
    4. No token → 401
    """
    # Dev mode: skip all auth
    if _is_dev_mode():
        return {"email": "dev@local", "auth_method": "dev_mode"}

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check API key
    api_keys = _get_api_keys()
    if api_keys and token in api_keys:
        logger.info("Authenticated via API key")
        return {"email": "api-key-user", "auth_method": "api_key"}

    # Verify Google ID token (audience-bound — rejects tokens minted for other services)
    claims = _verify_google_id_token(token)
    caller_email = claims.get("email", "unknown")

    # Fail-closed allowlist: ALLOWED_CALLERS must be set outside DEV_MODE.
    # Empty allowlist would otherwise grant access to any authenticated Google identity.
    allowed_callers = _get_allowed_callers()
    if not allowed_callers:
        logger.error("ALLOWED_CALLERS is empty in non-dev mode — refusing request")
        raise HTTPException(
            status_code=500,
            detail="ALLOWED_CALLERS is not configured — server refusing requests fail-closed.",
        )
    if caller_email not in allowed_callers:
        logger.warning("Caller not in allowlist", extra={"email": caller_email})
        raise HTTPException(
            status_code=403,
            detail=f"Caller '{caller_email}' not authorized",
        )

    logger.info("Authenticated", extra={"email": caller_email, "method": "google_id_token"})
    return {
        "email": caller_email,
        "auth_method": "google_id_token",
        "claims": claims,
    }


async def require_analyst_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> dict:
    """
    Stricter auth for HITL endpoints — requires a human analyst identity.

    Same as require_auth but rejects service account tokens
    (only humans should approve/reject actions).
    """
    identity = await require_auth(request, credentials)

    # In dev mode, allow everything
    if identity.get("auth_method") == "dev_mode":
        return identity

    # Service accounts should not approve HITL actions
    email = identity.get("email", "")
    if email.endswith(".iam.gserviceaccount.com"):
        raise HTTPException(
            status_code=403,
            detail="HITL actions require a human analyst identity, not a service account.",
        )

    return identity
