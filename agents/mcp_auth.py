"""
MCP Gateway Authentication — Identity token auth for Cloud Run.

Implements the official Google codelab pattern for authenticating ADK agents
to Cloud Run MCP servers:
  1. Static headers on StreamableHTTPConnectionParams (initial session)
  2. header_provider on McpToolset (per-execution token refresh)

Detection: env vars (GOOGLE_CLOUD_AGENT_ENGINE_ID, K_SERVICE) with URL-based
fallback (any https:// to non-localhost needs auth).

References:
    - Codelab: codelabs.developers.google.com/codelabs/cloud-run/use-mcp-server-on-cloud-run-with-an-adk-agent
    - ADK MCP tools: google.github.io/adk-docs/tools/mcp-tools/
    - Cloud Run S2S auth: cloud.google.com/run/docs/authenticating/service-to-service
    - ID tokens: cloud.google.com/docs/authentication/get-id-token
"""

import logging
import os
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Cache identity tokens per audience to avoid redundant metadata server calls
_id_token_cache: dict[str, tuple[str, float]] = {}
_TOKEN_BUFFER_SECONDS = 120  # Refresh 2 min before expiry


def _is_cloud_environment() -> bool:
    """Detect if running in a GCP environment that needs identity token auth."""
    return bool(
        os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")
        or os.environ.get("K_SERVICE")  # Cloud Run
        or os.environ.get("MCP_GATEWAY_AUTH", "").lower() in ("true", "1", "yes")
    )


def _url_needs_auth(url: str) -> bool:
    """Fallback: any https:// URL to a non-localhost target needs auth."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    hostname = parsed.hostname or ""
    return hostname not in ("localhost", "127.0.0.1", "0.0.0.0", "::1")


def needs_auth(url: str) -> bool:
    """Check if MCP connections to this URL need identity token auth."""
    return _is_cloud_environment() or _url_needs_auth(url)


def _fetch_id_token(audience: str) -> str:
    """Fetch a GCP OIDC identity token for the given audience.

    Uses google.oauth2.id_token.fetch_id_token() which works via:
      - GCE metadata server (Agent Engine, Cloud Run, GCE, GKE)
      - Service account key file (GOOGLE_APPLICATION_CREDENTIALS)

    Falls back to IAM Credentials API if fetch_id_token fails.
    """
    import google.auth.transport.requests

    request = google.auth.transport.requests.Request()

    # Strategy 1: Standard fetch_id_token (metadata server / SA key file)
    try:
        import google.oauth2.id_token
        token = google.oauth2.id_token.fetch_id_token(request, audience)
        logger.warning("MCP auth: got identity token via fetch_id_token (audience=%s)", audience)
        return token
    except Exception as e:
        logger.warning("MCP auth: fetch_id_token failed (%s), trying IAM Credentials API", e)

    # Strategy 2: IAM Credentials API generateIdToken
    # Works in environments where ADC provides access tokens but metadata
    # server identity endpoint is unavailable.
    import google.auth
    credentials, _project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not credentials.valid:
        credentials.refresh(request)

    sa_email = getattr(credentials, "service_account_email", None)
    if not sa_email:
        raise RuntimeError(
            f"Cannot determine SA email from ADC (type={type(credentials).__name__}). "
            f"Ensure Agent Engine SA has roles/run.invoker on Gateway."
        )

    import requests as stdlib_requests
    iam_url = (
        f"https://iamcredentials.googleapis.com/v1/"
        f"projects/-/serviceAccounts/{sa_email}:generateIdToken"
    )
    resp = stdlib_requests.post(
        iam_url,
        headers={"Authorization": f"Bearer {credentials.token}", "Content-Type": "application/json"},
        json={"audience": audience, "includeEmail": True},
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"IAM generateIdToken failed ({resp.status_code}): {resp.text}. "
            f"SA={sa_email}, audience={audience}."
        )
    token = resp.json()["token"]
    logger.warning("MCP auth: got identity token via IAM Credentials API (sa=%s, audience=%s)", sa_email, audience)
    return token


def get_id_token(audience: str) -> str:
    """Get a cached or fresh identity token for the given audience."""
    cached = _id_token_cache.get(audience)
    if cached and time.time() < cached[1] - _TOKEN_BUFFER_SECONDS:
        return cached[0]

    try:
        token = _fetch_id_token(audience)
    except Exception:
        logger.exception("MCP auth: FAILED to get identity token for %s", audience)
        raise

    expiry = time.time() + 3600  # ID tokens valid ~1 hour
    _id_token_cache[audience] = (token, expiry)
    return token


def build_mcp_connection(url: str, timeout: float = 30.0):
    """Build StreamableHTTPConnectionParams with static auth headers.

    Follows the official Google codelab pattern: inject an identity token
    as a static Authorization header. For long-lived agents, pair with
    build_mcp_auth_provider() on McpToolset for token refresh.

    Args:
        url: Full MCP endpoint URL (e.g. https://gateway.run.app/mcp/client-1)
        timeout: Connection timeout in seconds. Default 30s to accommodate
                 Cloud Run cold starts (default 5s is too tight).

    Returns:
        StreamableHTTPConnectionParams with auth headers if needed.
    """
    from google.adk.tools.mcp_tool.mcp_toolset import StreamableHTTPConnectionParams

    cloud_env = _is_cloud_environment()
    url_auth = _url_needs_auth(url)
    auth_needed = cloud_env or url_auth

    logger.warning(
        "MCP connection: url=%s cloud_env=%s url_auth=%s needs_auth=%s "
        "AGENT_ENGINE_ID=%s K_SERVICE=%s",
        url, cloud_env, url_auth, auth_needed,
        os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID", "<unset>"),
        os.environ.get("K_SERVICE", "<unset>"),
    )

    if auth_needed:
        parsed = urlparse(url)
        audience = f"{parsed.scheme}://{parsed.netloc}"
        token = get_id_token(audience)
        logger.warning("MCP auth: static header set for audience=%s", audience)
        return StreamableHTTPConnectionParams(
            url=url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    logger.warning("MCP connection: no auth (local dev mode)")
    return StreamableHTTPConnectionParams(url=url, timeout=timeout)


def build_mcp_auth_provider(url: str):
    """Build a header_provider for McpToolset that refreshes auth tokens.

    Returns None if auth is not needed (local dev). When auth is needed,
    returns a callable that fetches a fresh identity token per tool execution.

    Usage:
        toolset = McpToolset(
            connection_params=build_mcp_connection(mcp_url),
            header_provider=build_mcp_auth_provider(mcp_url),
            tool_filter=MY_TOOLS,
        )

    Args:
        url: Same MCP endpoint URL used with build_mcp_connection().

    Returns:
        Callable[[ReadonlyContext], dict] or None.
    """
    if not needs_auth(url):
        return None

    parsed = urlparse(url)
    audience = f"{parsed.scheme}://{parsed.netloc}"

    def _provider(readonly_context) -> dict:
        token = get_id_token(audience)
        return {"Authorization": f"Bearer {token}"}

    return _provider
