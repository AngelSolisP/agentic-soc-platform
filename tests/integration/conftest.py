"""
Shared fixtures for MVP integration tests.

Mode selection:
    INTEGRATION_TEST_MODE=mock  (default) - all GCP calls are patched
    INTEGRATION_TEST_MODE=live  - real Chronicle NFR tenant, requires GCP credentials

Constants and helpers are in helpers.py (importable from test modules).
This file only contains pytest fixtures.

Note: httpx ASGITransport does NOT trigger FastAPI lifespan events.
All app.state attributes must be injected manually in fixtures.
"""

import os
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch

import httpx
from httpx import AsyncClient, ASGITransport

from proxy.mcp_gateway.circuit_breaker import CircuitBreaker
from proxy.mcp_gateway.rate_limiter import RateLimiter

from .helpers import (
    IS_LIVE,
    SYNTHETIC,
    CLIENT_A_CONFIG,
    CLIENT_B_CONFIG,
    safe_armor_result,
)


# ---------------------------------------------------------------------------
# Fixtures: test data
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def integration_mode():
    """Return the current integration test mode."""
    return "live" if IS_LIVE else "mock"


@pytest.fixture
def synthetic_data():
    """Canonical test data dict. Each field has an env var override for live mode."""
    return SYNTHETIC.copy()


# ---------------------------------------------------------------------------
# Mock GCP dependencies (reused across all integration tests in mock mode)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_gcp_all():
    """Patch all GCP client initializations so tests run without credentials."""
    if IS_LIVE:
        yield
        return
    with (
        patch("proxy.mcp_gateway.router.firestore.Client"),
        patch("proxy.mcp_gateway.auth.secretmanager.SecretManagerServiceClient"),
        patch("proxy.mcp_gateway.auth.google.auth.default"),
        patch("proxy.mcp_gateway.auth.impersonated_credentials.Credentials"),
        patch("agents.response.agent.firestore.Client"),
        patch("agents.dedup.firestore.Client"),
    ):
        yield


def _inject_gateway_state(app, router_mock, armor_mock):
    """Inject all required app.state attributes for the MCP Gateway.

    httpx ASGITransport does not trigger FastAPI lifespan, so we must
    manually set everything that lifespan() would normally create.
    """
    app.state.router = router_mock
    app.state.http_client = httpx.AsyncClient(timeout=5)
    app.state.model_armor = armor_mock
    app.state.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    app.state.rate_limiter = RateLimiter(max_tokens=100, refill_rate=10.0)
    # GTI backend state
    app.state.gti_http_client = httpx.AsyncClient(timeout=5)
    app.state.gti_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)


# ---------------------------------------------------------------------------
# MCP Gateway test client
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def gateway_client(synthetic_data):
    """FastAPI test client for the MCP Gateway (mock mode)."""
    if IS_LIVE:
        url = os.environ.get("MCP_GATEWAY_URL", "http://localhost:8080")
        async with AsyncClient(base_url=url) as client:
            yield client
        return

    os.environ["PARTNER_PROJECT_ID"] = synthetic_data["partner_project_id"]
    os.environ["DEV_MODE"] = "true"

    from proxy.mcp_gateway.main import app

    router_mock = MagicMock()
    router_mock.get_client.return_value = CLIENT_A_CONFIG

    armor_mock = AsyncMock()
    armor_mock.sanitize_user_prompt.return_value = safe_armor_result()
    armor_mock.sanitize_model_response.return_value = safe_armor_result()

    _inject_gateway_state(app, router_mock, armor_mock)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    await app.state.http_client.aclose()
    await app.state.gti_http_client.aclose()


@pytest_asyncio.fixture
async def gateway_client_dual(synthetic_data):
    """Gateway test client configured with TWO clients for multi-tenancy tests."""
    if IS_LIVE:
        url = os.environ.get("MCP_GATEWAY_URL", "http://localhost:8080")
        async with AsyncClient(base_url=url) as client:
            yield client
        return

    os.environ["PARTNER_PROJECT_ID"] = synthetic_data["partner_project_id"]
    os.environ["DEV_MODE"] = "true"

    from proxy.mcp_gateway.main import app

    router_mock = MagicMock()

    def route_client(cid):
        if cid == SYNTHETIC["client_id_a"]:
            return CLIENT_A_CONFIG
        if cid == SYNTHETIC["client_id_b"]:
            return CLIENT_B_CONFIG
        raise KeyError(f"Client '{cid}' not found")

    router_mock.get_client.side_effect = route_client

    armor_mock = AsyncMock()
    armor_mock.sanitize_user_prompt.return_value = safe_armor_result()
    armor_mock.sanitize_model_response.return_value = safe_armor_result()

    _inject_gateway_state(app, router_mock, armor_mock)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    await app.state.http_client.aclose()
    await app.state.gti_http_client.aclose()


# ---------------------------------------------------------------------------
# HITL Dashboard test client
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def hitl_client():
    """FastAPI test client for the HITL Dashboard backend."""
    if IS_LIVE:
        url = os.environ.get("HITL_BACKEND_URL", "http://localhost:8081")
        async with AsyncClient(base_url=url) as client:
            yield client
        return

    os.environ["PARTNER_PROJECT_ID"] = SYNTHETIC["partner_project_id"]
    os.environ["DEV_MODE"] = "true"
    os.environ["ENFORCE_CLIENT_AUTH"] = "false"

    with patch("ui.hitl_dashboard.backend.main.get_db") as mock_get_db, \
         patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", False):
        db_mock = MagicMock()
        mock_get_db.return_value = db_mock

        from ui.hitl_dashboard.backend.main import app as hitl_app

        async with AsyncClient(
            transport=ASGITransport(app=hitl_app),
            base_url="http://test",
        ) as client:
            # Store db_mock on app so tests can wire Firestore chains
            hitl_app.state._test_db_mock = db_mock
            yield client
