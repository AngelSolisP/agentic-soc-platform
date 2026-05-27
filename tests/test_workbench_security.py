"""Tests for SOC Workbench security hardening.

Covers: OWASP Top 10 mitigations, security headers, rate limiting,
client_id validation, path traversal, WebSocket auth, DEV_MODE guard.
"""
import os
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("PARTNER_PROJECT_ID", "test-project")
os.environ["DEV_MODE"] = "true"

from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI


# ---------------------------------------------------------------------------
# Security module unit tests
# ---------------------------------------------------------------------------

class TestClientIdValidation:
    def test_valid_client_ids(self):
        from workbench.backend.security import validate_client_id

        assert validate_client_id("zevorus-nfr") == "zevorus-nfr"
        assert validate_client_id("client-alpha") == "client-alpha"
        assert validate_client_id("abc") == "abc"
        assert validate_client_id("a" * 63) == "a" * 63

    def test_invalid_client_ids(self):
        from workbench.backend.security import validate_client_id
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_client_id("")
        assert exc_info.value.status_code == 400

        with pytest.raises(HTTPException):
            validate_client_id("AB-UPPER")  # uppercase not allowed

        with pytest.raises(HTTPException):
            validate_client_id("a")  # too short (min 3)

        with pytest.raises(HTTPException):
            validate_client_id("1starts-with-number")

        with pytest.raises(HTTPException):
            validate_client_id("has spaces")

        with pytest.raises(HTTPException):
            validate_client_id("../traversal")

        with pytest.raises(HTTPException):
            validate_client_id("inject'; DROP TABLE--")


class TestPathTraversal:
    def test_safe_path(self, tmp_path):
        from workbench.backend.security import is_safe_path

        child = tmp_path / "subdir" / "file.txt"
        child.parent.mkdir(parents=True)
        child.touch()
        assert is_safe_path(tmp_path, child) is True

    def test_unsafe_path_parent_traversal(self, tmp_path):
        from workbench.backend.security import is_safe_path

        outside = tmp_path / ".." / "etc" / "passwd"
        assert is_safe_path(tmp_path, outside) is False

    def test_unsafe_path_absolute(self, tmp_path):
        from workbench.backend.security import is_safe_path

        assert is_safe_path(tmp_path, Path("/etc/passwd")) is False


class TestRateLimiter:
    def test_allows_under_limit(self):
        from workbench.backend.security import RateLimiter

        rl = RateLimiter()
        for _ in range(5):
            assert rl.check("test-key", max_requests=10) is True

    def test_blocks_over_limit(self):
        from workbench.backend.security import RateLimiter

        rl = RateLimiter()
        for _ in range(5):
            rl.check("test-key", max_requests=5)
        assert rl.check("test-key", max_requests=5) is False

    def test_separate_keys(self):
        from workbench.backend.security import RateLimiter

        rl = RateLimiter()
        for _ in range(5):
            rl.check("key-a", max_requests=5)
        # key-a is exhausted, but key-b should still work
        assert rl.check("key-b", max_requests=5) is True


class TestDevModeGuard:
    def test_dev_mode_blocked_in_production(self):
        from workbench.backend.security import check_dev_mode_safety

        with patch.dict(os.environ, {"DEV_MODE": "true", "K_SERVICE": "my-cloud-run-svc"}):
            with pytest.raises(RuntimeError, match="DEV_MODE=true is not allowed in production"):
                check_dev_mode_safety()

    def test_dev_mode_allowed_locally(self):
        from workbench.backend.security import check_dev_mode_safety

        with patch.dict(os.environ, {"DEV_MODE": "true"}, clear=False):
            # Remove production indicators
            env = os.environ.copy()
            env.pop("K_SERVICE", None)
            env.pop("ENVIRONMENT", None)
            with patch.dict(os.environ, env, clear=True):
                check_dev_mode_safety()  # Should not raise


class TestFailedAuthLogging:
    def test_logs_failed_attempt(self):
        from workbench.backend.security import log_failed_auth, _failed_auth_counts

        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.url.path = "/api/me"
        mock_request.headers.get.return_value = "test-agent"

        # Reset counter for this test
        _failed_auth_counts.pop("192.168.1.100", None)

        log_failed_auth(mock_request, "test_reason")
        assert _failed_auth_counts["192.168.1.100"] == 1


# ---------------------------------------------------------------------------
# Integration tests — security headers on actual FastAPI app
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    db = MagicMock()
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = {
        "email": "dev@local",
        "role": "admin",
        "allowed_clients": [],
    }
    db.collection.return_value.document.return_value.get.return_value = doc
    db.collection.return_value.limit.return_value.stream.return_value = []
    return db


@pytest_asyncio.fixture
async def secure_client(mock_db):
    """Create test client with the full workbench app (security middleware active)."""
    with patch.dict(os.environ, {"DEV_MODE": "true"}):
        # Re-import to pick up security middleware
        import importlib
        import workbench.backend.main as main_mod
        importlib.reload(main_mod)

        app = main_mod.app
        app.state.db = mock_db
        app.state.http_client = MagicMock()
        app.state.mcp_gateway_url = "http://localhost:8080"
        app.state.mcp_client = None
        app.state.audit = MagicMock()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client


@pytest.mark.asyncio
async def test_security_headers_present(secure_client):
    """OWASP A05: All security headers must be present on API responses."""
    resp = await secure_client.get("/health")
    assert resp.status_code == 200

    # Required headers
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in resp.headers.get("Permissions-Policy", "")


@pytest.mark.asyncio
async def test_api_no_cache_headers(secure_client):
    """OWASP A05: API responses must have no-cache headers."""
    resp = await secure_client.get("/api/me")
    assert resp.status_code == 200

    cache_control = resp.headers.get("Cache-Control", "")
    assert "no-store" in cache_control


@pytest.mark.asyncio
async def test_health_ready_no_error_leak(secure_client):
    """OWASP A09: Health endpoint must not leak internal error details."""
    # Force a Firestore error
    secure_client._transport.app.state.db.collection.side_effect = Exception(
        "Connection refused to firestore.googleapis.com:443"
    )

    resp = await secure_client.get("/health/ready")
    assert resp.status_code == 503

    body = resp.json()
    assert body["error"] == "database_unavailable"
    assert "firestore.googleapis.com" not in body.get("error", "")


@pytest.mark.asyncio
async def test_rate_limiting_blocks_excess(secure_client):
    """OWASP A04: Rate limiting must block excessive requests."""
    from workbench.backend.security import _rate_limiter

    # Exhaust the rate limit for a test IP
    test_key = "auth:testclient"
    for _ in range(25):
        _rate_limiter._requests[test_key].append(0)  # fake timestamps in the past won't be cleaned

    # The middleware uses time.monotonic() internally; we test the limiter directly
    from workbench.backend.security import RateLimiter
    rl = RateLimiter()
    for _ in range(20):
        rl.check("test-ip", max_requests=20)
    assert rl.check("test-ip", max_requests=20) is False


@pytest.mark.asyncio
async def test_request_size_limit():
    """OWASP A04: Oversized request bodies must be rejected."""
    from workbench.backend.security import RequestSizeLimitMiddleware

    inner_app = FastAPI()

    @inner_app.post("/test")
    async def test_endpoint():
        return {"ok": True}

    inner_app.add_middleware(RequestSizeLimitMiddleware)

    async with AsyncClient(
        transport=ASGITransport(app=inner_app), base_url="http://test"
    ) as client:
        # Request with Content-Length exceeding 1MB
        resp = await client.post(
            "/test",
            headers={"Content-Length": str(2 * 1024 * 1024)},
            content=b"x",
        )
        assert resp.status_code == 413


@pytest.mark.asyncio
async def test_error_sanitization_case_not_found(secure_client):
    """OWASP A09: MCP errors must not leak gateway internals."""
    from workbench.backend.mcp_client import MCPToolError

    mock_mcp = MagicMock()
    mock_mcp.call_tool = MagicMock(side_effect=MCPToolError("get_case", "HTTP 500: Connection to chronicle-mcp-us.googleapis.com failed"))
    secure_client._transport.app.state.mcp_client = mock_mcp

    resp = await secure_client.get("/api/cases/999?client_id=zevorus-nfr")
    assert resp.status_code == 404
    body = resp.json()
    # Must NOT contain internal MCP details
    assert "chronicle-mcp" not in body.get("detail", "")
    assert body["detail"] == "Case not found"
