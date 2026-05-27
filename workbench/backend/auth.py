"""Google Sign-In authentication + Firestore RBAC for SOC Workbench.

Security model (OWASP A01, A07):
- Production: Google Sign-In OIDC token verification (Bearer token)
- Fallback: Bearer API key for service-to-service calls
- Dev mode: bypasses auth (blocked in production by security.check_dev_mode_safety)
- Domain restriction: ALLOWED_DOMAINS limits sign-in to org accounts
"""
import logging
import os
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

API_KEYS = [k.strip() for k in os.environ.get("API_KEYS", "").split(",") if k.strip()]
ANALYST_COLLECTION = "analyst_assignments"
# Google Sign-In: OAuth Client ID for audience verification
GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
# Domain restriction: comma-separated list of allowed email domains (e.g. "example.com")
ALLOWED_DOMAINS = [d.strip() for d in os.environ.get("ALLOWED_DOMAINS", "").split(",") if d.strip()]

_bearer_scheme = HTTPBearer(auto_error=False)


def _is_dev_mode() -> bool:
    """Read DEV_MODE at request time so reloads and env changes take effect."""
    return os.environ.get("DEV_MODE", "false").lower() == "true"


# Module-level alias — updated by importlib.reload() in tests
DEV_MODE = _is_dev_mode()


def _verify_oidc_token(token: str) -> Optional[str]:
    """Verify a Google OIDC/ID token and return the email.

    Supports:
    - Google Sign-In (GIS) ID tokens (audience = OAuth Client ID)
    - gcloud proxy identity tokens
    - Service-to-service OIDC tokens
    """
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        decoded = google_id_token.verify_token(
            token,
            google_requests.Request(),
            audience=GOOGLE_OAUTH_CLIENT_ID or None,
        )
        email = decoded.get("email")
        if not email:
            logger.warning("OIDC token has no email claim")
            return None

        # Domain restriction
        if ALLOWED_DOMAINS:
            domain = email.rsplit("@", 1)[-1] if "@" in email else ""
            if domain not in ALLOWED_DOMAINS:
                logger.warning("OIDC login from unauthorized domain: %s", domain)
                return None

        return email
    except ImportError:
        logger.warning("google-auth not available for OIDC token verification")
        return None
    except Exception as e:
        logger.warning("OIDC token verification failed: %s", e)
        return None


def _load_analyst_profile(db, email: str) -> Optional[dict]:
    doc = db.collection(ANALYST_COLLECTION).document(email).get()
    if not doc.exists:
        return None
    return doc.to_dict()


async def get_current_analyst(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    from workbench.backend.security import log_failed_auth

    db = request.app.state.db
    email = None

    # 1. Dev mode
    if _is_dev_mode():
        email = "dev@local"
        profile = _load_analyst_profile(db, email)
        if not profile:
            return {
                "email": email,
                "role": "admin",
                "allowed_clients": [],
                "auth_method": "dev_mode",
            }
        return {**profile, "auth_method": "dev_mode"}

    # 2. Bearer OIDC identity token (Google Sign-In, gcloud proxy, service-to-service)
    if credentials and credentials.credentials not in API_KEYS:
        email = _verify_oidc_token(credentials.credentials)

    # 3. Bearer API key
    if not email and credentials and credentials.credentials in API_KEYS:
        email = "api-key-user"
        return {
            "email": email,
            "role": "admin",
            "allowed_clients": [],
            "auth_method": "api_key",
        }

    if not email:
        log_failed_auth(request, "no_credentials")
        raise HTTPException(status_code=401, detail="Authentication required")

    profile = _load_analyst_profile(db, email)
    if not profile:
        log_failed_auth(request, f"unknown_user:{email}")
        logger.warning("Authenticated user not in analyst_assignments", extra={"email": email})
        raise HTTPException(
            status_code=403,
            detail="User is not registered as an analyst",
        )

    return {**profile, "email": email, "auth_method": "oidc"}


async def require_admin(analyst: dict = Depends(get_current_analyst)) -> dict:
    if analyst.get("role") != "admin":
        raise HTTPException(
            status_code=403, detail="Admin access required"
        )
    return analyst
