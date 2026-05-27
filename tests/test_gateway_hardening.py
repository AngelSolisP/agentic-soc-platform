"""Tests for gateway hardening: body size limit + Model Armor fail mode."""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestBodySizeLimit:
    """Gateway should reject oversized request bodies."""

    @pytest.mark.asyncio
    async def test_oversized_body_returns_413(self):
        """Request body exceeding MAX_BODY_SIZE_BYTES should return 413."""
        import os
        from proxy.mcp_gateway.main import app
        from proxy.mcp_gateway.circuit_breaker import CircuitBreaker
        from proxy.mcp_gateway.rate_limiter import RateLimiter
        from httpx import AsyncClient, ASGITransport

        os.environ["DEV_MODE"] = "true"

        # Inject app.state (ASGITransport doesn't trigger lifespan)
        mock_router = MagicMock()
        mock_client_config = MagicMock()
        mock_client_config.enabled = True
        mock_client_config.mcp_endpoint = "https://chronicle.us.rep.googleapis.com/mcp"
        mock_client_config.service_account_email = "sa@test.iam.gserviceaccount.com"
        mock_client_config.gcp_project_id = "test-project"
        mock_router.get_client.return_value = mock_client_config

        app.state.router = mock_router
        app.state.http_client = AsyncMock()
        app.state.model_armor = AsyncMock()
        app.state.model_armor.sanitize_user_prompt.return_value = MagicMock(
            allowed=True, filter_result="SAFE", sanitized_text=None
        )
        app.state.circuit_breaker = CircuitBreaker()
        app.state.rate_limiter = RateLimiter()
        app.state.gti_http_client = AsyncMock()
        app.state.gti_circuit_breaker = CircuitBreaker()

        with patch("proxy.mcp_gateway.main.MAX_BODY_SIZE", 100):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                big_body = '{"x": "' + "a" * 200 + '"}'
                response = await client.post(
                    "/mcp/test-client",
                    content=big_body,
                    headers={"Content-Type": "application/json"},
                )
                assert response.status_code == 413

        os.environ.pop("DEV_MODE", None)


class TestModelArmorFailMode:
    """Model Armor should support both fail-open and fail-closed modes."""

    @pytest.mark.asyncio
    async def test_fail_open_allows_on_api_error(self):
        """Default fail-open: Model Armor API errors allow the request."""
        from proxy.mcp_gateway.model_armor import ModelArmorClient, FilterResult

        client = ModelArmorClient(
            project_id="test", enabled=True, fail_closed=False
        )
        client._http_client = AsyncMock()
        client._http_client.post.side_effect = Exception("API down")

        with patch.object(client, "_get_auth_token", return_value="token"):
            result = await client.sanitize_user_prompt("test input")
            assert result.allowed is True
            assert result.filter_result == FilterResult.ERROR

    @pytest.mark.asyncio
    async def test_fail_closed_blocks_on_api_error(self):
        """fail_closed=True: Model Armor API errors block the request."""
        from proxy.mcp_gateway.model_armor import ModelArmorClient, FilterResult

        client = ModelArmorClient(
            project_id="test", enabled=True, fail_closed=True
        )
        client._http_client = AsyncMock()
        client._http_client.post.side_effect = Exception("API down")

        with patch.object(client, "_get_auth_token", return_value="token"):
            result = await client.sanitize_user_prompt("test input")
            assert result.allowed is False
            assert result.filter_result == FilterResult.ERROR

    @pytest.mark.asyncio
    async def test_fail_closed_blocks_on_non_200(self):
        """fail_closed=True: Non-200 Model Armor response blocks the request."""
        from proxy.mcp_gateway.model_armor import ModelArmorClient, FilterResult

        client = ModelArmorClient(
            project_id="test", enabled=True, fail_closed=True
        )
        client._http_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        client._http_client.post.return_value = mock_response

        with patch.object(client, "_get_auth_token", return_value="token"):
            result = await client.sanitize_user_prompt("test input")
            assert result.allowed is False
            assert result.filter_result == FilterResult.ERROR

    @pytest.mark.asyncio
    async def test_fail_open_allows_on_non_200(self):
        """Default fail-open: Non-200 Model Armor response allows the request."""
        from proxy.mcp_gateway.model_armor import ModelArmorClient, FilterResult

        client = ModelArmorClient(
            project_id="test", enabled=True, fail_closed=False
        )
        client._http_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        client._http_client.post.return_value = mock_response

        with patch.object(client, "_get_auth_token", return_value="token"):
            result = await client.sanitize_user_prompt("test input")
            assert result.allowed is True
            assert result.filter_result == FilterResult.ERROR

    @pytest.mark.asyncio
    async def test_response_sanitize_fail_closed(self):
        """fail_closed also applies to sanitize_model_response."""
        from proxy.mcp_gateway.model_armor import ModelArmorClient, FilterResult

        client = ModelArmorClient(
            project_id="test", enabled=True, fail_closed=True
        )
        client._http_client = AsyncMock()
        client._http_client.post.side_effect = Exception("API down")

        with patch.object(client, "_get_auth_token", return_value="token"):
            result = await client.sanitize_model_response("test output")
            assert result.allowed is False
            assert result.filter_result == FilterResult.ERROR

    def test_create_model_armor_client_reads_fail_mode_env(self):
        """create_model_armor_client should read MODEL_ARMOR_FAIL_MODE env var.

        Default is FAIL_CLOSED per Google official docs.
        Backward compat: reads legacy MODEL_ARMOR_FAIL_CLOSED if new var not set.
        """
        from proxy.mcp_gateway.model_armor import create_model_armor_client

        # Default (no env var) → fail-closed
        with patch.dict("os.environ", {"PARTNER_PROJECT_ID": "test"}, clear=False):
            os.environ.pop("MODEL_ARMOR_FAIL_MODE", None)
            os.environ.pop("MODEL_ARMOR_FAIL_CLOSED", None)
            client = create_model_armor_client()
            assert client._fail_closed is True

        # Explicit FAIL_CLOSED (new var)
        with patch.dict("os.environ", {"MODEL_ARMOR_FAIL_MODE": "FAIL_CLOSED", "PARTNER_PROJECT_ID": "test"}):
            client = create_model_armor_client()
            assert client._fail_closed is True

        # Explicit FAIL_OPEN (new var)
        with patch.dict("os.environ", {"MODEL_ARMOR_FAIL_MODE": "FAIL_OPEN", "PARTNER_PROJECT_ID": "test"}):
            client = create_model_armor_client()
            assert client._fail_closed is False

        # Legacy env var backward compat
        with patch.dict("os.environ", {"MODEL_ARMOR_FAIL_CLOSED": "true", "PARTNER_PROJECT_ID": "test"}, clear=False):
            os.environ.pop("MODEL_ARMOR_FAIL_MODE", None)
            client = create_model_armor_client()
            assert client._fail_closed is True

        with patch.dict("os.environ", {"MODEL_ARMOR_FAIL_CLOSED": "false", "PARTNER_PROJECT_ID": "test"}, clear=False):
            os.environ.pop("MODEL_ARMOR_FAIL_MODE", None)
            client = create_model_armor_client()
            assert client._fail_closed is False
