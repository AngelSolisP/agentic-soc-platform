"""Security middleware and hardening for SOC Workbench.

Implements OWASP-recommended security headers, request validation,
rate limiting, and production safety guards.
"""
import logging
import os
import re
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# OWASP client_id validation (reuse pattern from agents/validation.py)
CLIENT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,62}$")

# Rate limiting defaults
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "100"))
RATE_LIMIT_AUTH_MAX = int(os.environ.get("RATE_LIMIT_AUTH_MAX", "20"))
RATE_LIMIT_TRIGGER_MAX = int(os.environ.get("RATE_LIMIT_TRIGGER_MAX", "10"))

# Request body size limit (1MB default)
MAX_BODY_SIZE = int(os.environ.get("MAX_BODY_SIZE", str(1 * 1024 * 1024)))


def is_production() -> bool:
    """Check if running in production (Cloud Run sets K_SERVICE)."""
    return bool(os.environ.get("K_SERVICE") or os.environ.get("ENVIRONMENT") in ("staging", "production"))


# ---------------------------------------------------------------------------
# Security Headers Middleware (OWASP A05)
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers to all responses.

    Addresses:
    - OWASP A05: Security Misconfiguration
    - MITRE T1190: Exploit Public-Facing Application
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing (XSS via content-type confusion)
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking — only allow same-origin framing
        response.headers["X-Frame-Options"] = "DENY"

        # Control referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
            "magnetometer=(), gyroscope=(), accelerometer=()"
        )

        # Prevent caching of API responses (sensitive SOC data)
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # CSP — strict policy for SPA (inline styles needed for MUI)
        if not request.url.path.startswith("/api"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' https://accounts.google.com/gsi/; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://accounts.google.com/gsi/; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https://lh3.googleusercontent.com; "
                "connect-src 'self' ws: wss: https://accounts.google.com; "
                "frame-src https://accounts.google.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )

        # HSTS — enforce HTTPS (only in production, Cloud Run handles TLS)
        if is_production():
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


# ---------------------------------------------------------------------------
# Rate Limiting (OWASP A04 + MITRE T1110)
# ---------------------------------------------------------------------------

class RateLimiter:
    """Simple in-memory rate limiter per IP.

    Sufficient for single-instance Cloud Run. For multi-instance,
    Cloud Armor rate limiting should be used in addition.
    """

    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, key: str, window: int) -> None:
        cutoff = time.monotonic() - window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def check(self, key: str, max_requests: int, window: int = RATE_LIMIT_WINDOW) -> bool:
        """Return True if request is allowed, False if rate limited."""
        self._cleanup(key, window)
        if len(self._requests[key]) >= max_requests:
            return False
        self._requests[key].append(time.monotonic())
        return True


_rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply rate limiting per client IP.

    Different limits for different endpoint categories:
    - /api/trigger: 10/min (pipeline execution is expensive)
    - /api/me, auth: 20/min (prevent brute force)
    - General API: 100/min
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/health/ready"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Determine rate limit tier
        if path == "/api/trigger":
            limit = RATE_LIMIT_TRIGGER_MAX
            key = f"trigger:{client_ip}"
        elif path == "/api/me":
            limit = RATE_LIMIT_AUTH_MAX
            key = f"auth:{client_ip}"
        elif path.startswith("/api"):
            limit = RATE_LIMIT_MAX_REQUESTS
            key = f"api:{client_ip}"
        else:
            # Static assets — no rate limit
            return await call_next(request)

        if not _rate_limiter.check(key, limit):
            logger.warning(
                "Rate limited", extra={"ip": client_ip, "path": path, "limit": limit}
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please retry later."},
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Request Size Limit (OWASP A04)
# ---------------------------------------------------------------------------

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies exceeding MAX_BODY_SIZE.

    Prevents resource exhaustion via oversized payloads.
    """

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)


# ---------------------------------------------------------------------------
# Client ID Validation (OWASP A01 + A03)
# ---------------------------------------------------------------------------

def validate_client_id(client_id: str) -> str:
    """Validate client_id format. Raises HTTPException on invalid input.

    Reuses the same pattern as agents/validation.py to ensure consistency.
    """
    if not client_id or not CLIENT_ID_PATTERN.match(client_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid client_id format. Must be 3-63 lowercase alphanumeric with hyphens.",
        )
    return client_id


# ---------------------------------------------------------------------------
# WebSocket Authentication (OWASP A01 + A07)
# ---------------------------------------------------------------------------

async def authenticate_websocket(websocket: WebSocket) -> Optional[dict]:
    """Authenticate WebSocket connection via query parameter token.

    WebSockets can't use standard HTTP auth headers, so we accept
    the token as a query parameter: ws://host/ws/path?token=<bearer_token>

    Returns analyst dict or None if auth fails.
    """
    from workbench.backend.auth import API_KEYS, _is_dev_mode, _load_analyst_profile, _verify_oidc_token

    db = websocket.app.state.db

    # Dev mode bypass
    if _is_dev_mode():
        profile = _load_analyst_profile(db, "dev@local")
        if not profile:
            return {
                "email": "dev@local",
                "role": "admin",
                "allowed_clients": [],
            }
        return profile

    # Check query param token (Google Sign-In ID token or API key)
    token = websocket.query_params.get("token")
    email = None

    if token:
        if token in API_KEYS:
            return {
                "email": "api-key-user",
                "role": "admin",
                "allowed_clients": [],
            }
        # OIDC/Google Sign-In token verification
        email = _verify_oidc_token(token)

    if not email:
        return None

    profile = _load_analyst_profile(db, email)
    if not profile:
        return None

    return {**profile, "email": email}


# ---------------------------------------------------------------------------
# Pub/Sub Token Verification (OWASP A01 + A07)
# ---------------------------------------------------------------------------

async def verify_pubsub_token(request: Request) -> bool:
    """Verify that a Pub/Sub push request has a valid OIDC token.

    Pub/Sub push subscriptions send an Authorization: Bearer <oidc_token>
    header. We verify it against Google's public keys.

    In DEV_MODE, this check is skipped.
    """
    from workbench.backend.auth import _is_dev_mode

    if _is_dev_mode():
        return True

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("Pub/Sub trigger: missing Bearer token")
        return False

    token = auth_header[7:]

    # In production, verify the OIDC token
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        claims = google_id_token.verify_oauth2_token(
            token, google_requests.Request()
        )

        # Verify the token is from Pub/Sub
        expected_sa = os.environ.get("PUBSUB_SERVICE_ACCOUNT", "")
        if expected_sa and claims.get("email") != expected_sa:
            logger.warning(
                "Pub/Sub trigger: unexpected SA",
                extra={"expected": expected_sa, "got": claims.get("email")},
            )
            return False

        return True
    except ImportError:
        # google-auth not available (shouldn't happen in production)
        logger.error("google-auth not available for Pub/Sub token verification")
        return not is_production()  # allow in dev, deny in prod
    except Exception as e:
        logger.warning("Pub/Sub trigger: token verification failed", extra={"error": str(e)})
        return False


# ---------------------------------------------------------------------------
# DEV_MODE Production Guard (OWASP A05)
# ---------------------------------------------------------------------------

def check_dev_mode_safety() -> None:
    """Log a prominent warning if DEV_MODE is enabled.

    In production (K_SERVICE set), refuse to start with DEV_MODE=true.
    """
    from workbench.backend.auth import _is_dev_mode

    if not _is_dev_mode():
        return

    if is_production():
        raise RuntimeError(
            "FATAL: DEV_MODE=true is not allowed in production. "
            "Remove DEV_MODE env var from Cloud Run service."
        )

    logger.warning(
        "=" * 60 + "\n"
        "  WARNING: DEV_MODE is enabled — all auth is bypassed!\n"
        "  Do NOT deploy with this setting.\n" +
        "=" * 60
    )


# ---------------------------------------------------------------------------
# Error Sanitization (OWASP A09)
# ---------------------------------------------------------------------------

def sanitized_error_response(status_code: int, detail: str) -> JSONResponse:
    """Return a sanitized error response that doesn't leak internals."""
    # Strip internal details in production
    if is_production() and status_code >= 500:
        return JSONResponse(
            status_code=status_code,
            content={"detail": "Internal server error"},
        )
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
    )


# ---------------------------------------------------------------------------
# Failed Auth Logging (OWASP A09 + MITRE T1110)
# ---------------------------------------------------------------------------

_failed_auth_counts: dict[str, int] = defaultdict(int)


def log_failed_auth(request: Request, reason: str) -> None:
    """Log failed authentication attempts for security monitoring."""
    client_ip = request.client.host if request.client else "unknown"
    _failed_auth_counts[client_ip] += 1

    extra = {
        "ip": client_ip,
        "reason": reason,
        "path": str(request.url.path),
        "user_agent": request.headers.get("user-agent", ""),
        "attempt_count": _failed_auth_counts[client_ip],
    }

    if _failed_auth_counts[client_ip] >= 5:
        logger.error("Repeated auth failures detected — possible brute force", extra=extra)
    else:
        logger.warning("Authentication failed", extra=extra)


# ---------------------------------------------------------------------------
# Path Traversal Protection (OWASP A01)
# ---------------------------------------------------------------------------

def is_safe_path(base_dir, requested_path) -> bool:
    """Verify that resolved path stays within base directory."""
    try:
        resolved = requested_path.resolve()
        base_resolved = base_dir.resolve()
        return resolved.is_relative_to(base_resolved)
    except (ValueError, OSError):
        return False
