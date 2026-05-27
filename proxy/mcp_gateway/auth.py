"""
Service Account Impersonation for per-client MCP routing.

Each client has a dedicated service account stored in Secret Manager.
The proxy impersonates it to call the client's Chronicle MCP endpoint
using short-lived tokens (1 hour TTL, refreshed automatically).
"""

import time
import logging
from typing import Optional

import google.auth
import google.auth.transport.requests
from google.auth import impersonated_credentials
from google.cloud import secretmanager
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Chronicle MCP requires these OAuth scopes
CHRONICLE_MCP_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
]

# Token cache: client_id -> (token, expiry_epoch)
_token_cache: dict[str, tuple[str, float]] = {}
_TOKEN_BUFFER_SECONDS = 300  # Refresh 5 min before expiry

# Per-client locks to prevent thundering herd on token refresh
import threading

_token_locks: dict[str, threading.Lock] = {}
_locks_lock = threading.Lock()


def _get_client_lock(client_id: str) -> threading.Lock:
    """Get or create a per-client lock for token refresh."""
    if client_id not in _token_locks:
        with _locks_lock:
            if client_id not in _token_locks:
                _token_locks[client_id] = threading.Lock()
    return _token_locks[client_id]


def _get_secret(secret_id: str, project_id: str) -> str:
    """Retrieve a secret value from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8")


def get_impersonated_token(
    client_id: str,
    client_sa_email: str,
    partner_project_id: str,
    force_refresh: bool = False,
) -> str:
    """
    Return a short-lived bearer token for impersonating the client's SA.

    Tokens are cached in memory. In a multi-replica Cloud Run deployment,
    each replica maintains its own cache (acceptable — just means more token
    refreshes, no correctness issue).

    Args:
        client_id: Logical client identifier (for cache key).
        client_sa_email: Full service account email of the client SA.
        partner_project_id: GCP project owning the source credentials.
        force_refresh: Bypass cache and fetch a fresh token.

    Returns:
        Bearer token string.
    """
    now = time.time()

    # Quick check outside lock (cache hit path is lock-free)
    if not force_refresh and client_id in _token_cache:
        token, expiry = _token_cache[client_id]
        if now < expiry - _TOKEN_BUFFER_SECONDS:
            return token

    lock = _get_client_lock(client_id)
    with lock:
        # Re-check cache inside lock (another thread may have refreshed)
        now = time.time()
        if not force_refresh and client_id in _token_cache:
            token, expiry = _token_cache[client_id]
            if now < expiry - _TOKEN_BUFFER_SECONDS:
                return token

        logger.info(
            "Refreshing impersonated token",
            extra={"client_id": client_id, "target_sa": client_sa_email},
        )

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=5),
            reraise=True,
        )
        def _refresh_token():
            source_credentials, _ = google.auth.default(scopes=CHRONICLE_MCP_SCOPES)
            target_creds = impersonated_credentials.Credentials(
                source_credentials=source_credentials,
                target_principal=client_sa_email,
                target_scopes=CHRONICLE_MCP_SCOPES,
                lifetime=3600,  # 1 hour
            )
            request = google.auth.transport.requests.Request()
            target_creds.refresh(request)
            return target_creds

        target_credentials = _refresh_token()

        token = target_credentials.token
        expiry_epoch = target_credentials.expiry.timestamp() if target_credentials.expiry else now + 3600

        _token_cache[client_id] = (token, expiry_epoch)
        logger.info(
            "Token refreshed",
            extra={"client_id": client_id, "expires_in": int(expiry_epoch - now)},
        )
        return token


def get_client_sa_email(
    client_id: str,
    partner_project_id: str,
    secret_prefix: str = "agentic-soc",
) -> str:
    """
    Retrieve the client's service account email from Secret Manager.

    Secret naming convention:
        {secret_prefix}-{client_id}-sa-email

    Example: agentic-soc-acme-corp-sa-email
    """
    secret_id = f"{secret_prefix}-{client_id}-sa-email"
    try:
        return _get_secret(secret_id, partner_project_id)
    except Exception as exc:
        logger.error(
            "Failed to retrieve client SA email",
            extra={"client_id": client_id, "secret_id": secret_id, "error": str(exc)},
        )
        raise
