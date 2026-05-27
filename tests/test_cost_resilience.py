"""Tests for cost and resilience improvements."""

import threading
from unittest.mock import patch, MagicMock
import pytest


class TestModelArmorCredentialCaching:
    """Model Armor should cache ADC credentials, not refresh on every call."""

    def test_second_call_does_not_refresh(self):
        with patch("proxy.mcp_gateway.model_armor.google.auth.default") as mock_default:
            mock_creds = MagicMock()
            mock_creds.token = "cached-token"
            mock_creds.expired = False
            mock_creds.valid = True
            mock_default.return_value = (mock_creds, "project")

            from proxy.mcp_gateway.model_armor import ModelArmorClient
            client = ModelArmorClient(project_id="test", enabled=True)

            token1 = client._get_auth_token()
            token2 = client._get_auth_token()

            # google.auth.default should be called once (first call)
            assert mock_default.call_count == 1
            # credentials.refresh should be called once
            assert mock_creds.refresh.call_count == 1

    def test_refresh_when_expired(self):
        with patch("proxy.mcp_gateway.model_armor.google.auth.default") as mock_default:
            mock_creds = MagicMock()
            mock_creds.token = "new-token"
            mock_creds.valid = True
            mock_default.return_value = (mock_creds, "project")

            from proxy.mcp_gateway.model_armor import ModelArmorClient
            client = ModelArmorClient(project_id="test", enabled=True)

            # First call
            mock_creds.expired = False
            client._get_auth_token()

            # Second call — credentials expired
            mock_creds.expired = True
            client._get_auth_token()

            # Should refresh twice (once initial, once on expiry)
            assert mock_creds.refresh.call_count == 2


class TestTokenRefreshLock:
    """Token refresh should use per-client locks to prevent thundering herd."""

    def setup_method(self):
        from proxy.mcp_gateway.auth import _token_cache, _token_locks
        _token_cache.clear()
        _token_locks.clear()

    @patch("proxy.mcp_gateway.auth.google.auth.default")
    @patch("proxy.mcp_gateway.auth.impersonated_credentials.Credentials")
    def test_concurrent_calls_only_refresh_once(self, mock_imp_creds, mock_default):
        """Two sequential calls for the same client should only trigger one refresh."""
        mock_source = MagicMock()
        mock_default.return_value = (mock_source, "project")

        mock_target = MagicMock()
        mock_target.token = "test-token"
        mock_target.expiry = None
        mock_imp_creds.return_value = mock_target

        from proxy.mcp_gateway.auth import get_impersonated_token

        # First call fills cache
        t1 = get_impersonated_token("client-a", "sa@proj.iam.gserviceaccount.com", "proj")
        # Second call should hit cache
        t2 = get_impersonated_token("client-a", "sa@proj.iam.gserviceaccount.com", "proj")

        assert t1 == t2
        # impersonated_credentials.Credentials called only once
        assert mock_imp_creds.call_count == 1

    @patch("proxy.mcp_gateway.auth.google.auth.default")
    @patch("proxy.mcp_gateway.auth.impersonated_credentials.Credentials")
    def test_different_clients_get_separate_locks(self, mock_imp_creds, mock_default):
        """Different clients should have independent locks and caches."""
        mock_source = MagicMock()
        mock_default.return_value = (mock_source, "project")

        mock_target = MagicMock()
        mock_target.token = "token-a"
        mock_target.expiry = None
        mock_imp_creds.return_value = mock_target

        from proxy.mcp_gateway.auth import get_impersonated_token, _token_locks

        get_impersonated_token("client-a", "sa-a@proj.iam.gserviceaccount.com", "proj")
        get_impersonated_token("client-b", "sa-b@proj.iam.gserviceaccount.com", "proj")

        # Each client should get its own lock
        assert "client-a" in _token_locks
        assert "client-b" in _token_locks
        assert _token_locks["client-a"] is not _token_locks["client-b"]
