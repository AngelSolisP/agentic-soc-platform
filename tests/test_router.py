"""
Tests for ClientRouter — client config resolution and caching.
"""

import pytest
from unittest.mock import MagicMock, patch
import time

from proxy.mcp_gateway.router import ClientRouter, ClientConfig, _client_config_cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the module-level cache between tests."""
    _client_config_cache.clear()
    yield
    _client_config_cache.clear()


@pytest.fixture
def mock_firestore_client():
    with patch("proxy.mcp_gateway.router.firestore.Client") as mock_client:
        yield mock_client.return_value


def make_firestore_doc(data: dict):
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = data
    return doc


SAMPLE_CLIENT_DATA = {
    "display_name": "Acme Corp",
    "gcp_project_id": "acme-gcp-project",
    "chronicle_customer_id": "acme-uuid-1234",
    "chronicle_region": "us",
    "service_account_email": "agentic-soc-acme@acme-gcp-project.iam.gserviceaccount.com",
    "enabled": True,
    "autonomous_mode": False,
    "extra": {},
}


def test_load_client_from_firestore(mock_firestore_client):
    """Router should load client config from Firestore."""
    doc = make_firestore_doc(SAMPLE_CLIENT_DATA)
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = doc

    router = ClientRouter(partner_project_id="test-project")
    config = router.get_client("acme-corp")

    assert config.client_id == "acme-corp"
    assert config.gcp_project_id == "acme-gcp-project"
    assert config.chronicle_customer_id == "acme-uuid-1234"
    assert config.enabled is True


def test_mcp_endpoint_format(mock_firestore_client):
    """ClientConfig should generate correct MCP endpoint URL."""
    doc = make_firestore_doc(SAMPLE_CLIENT_DATA)
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = doc

    router = ClientRouter(partner_project_id="test-project")
    config = router.get_client("acme-corp")

    assert "chronicle.us.rep.googleapis.com/mcp" in config.mcp_endpoint
    assert "acme-uuid-1234" in config.mcp_endpoint


def test_client_caching(mock_firestore_client):
    """Second call for same client should use cache, not hit Firestore."""
    doc = make_firestore_doc(SAMPLE_CLIENT_DATA)
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = doc

    router = ClientRouter(partner_project_id="test-project")

    config1 = router.get_client("acme-corp")
    config2 = router.get_client("acme-corp")

    # Firestore should only be called once (second call from cache)
    call_count = mock_firestore_client.collection.return_value.document.return_value.get.call_count
    assert call_count == 1
    assert config1.client_id == config2.client_id


def test_unknown_client_raises_key_error(mock_firestore_client):
    """Unknown client should raise KeyError."""
    doc = MagicMock()
    doc.exists = False
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = doc

    router = ClientRouter(partner_project_id="test-project")

    with pytest.raises(KeyError, match="unknown-client"):
        router.get_client("unknown-client")


def test_cache_invalidation(mock_firestore_client):
    """Invalidating cache should force Firestore re-fetch."""
    doc = make_firestore_doc(SAMPLE_CLIENT_DATA)
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = doc

    router = ClientRouter(partner_project_id="test-project")
    router.get_client("acme-corp")
    router.invalidate_cache("acme-corp")
    router.get_client("acme-corp")

    call_count = mock_firestore_client.collection.return_value.document.return_value.get.call_count
    assert call_count == 2


def test_load_client_from_yaml(tmp_path):
    """Router falls back to YAML config when Firestore unavailable."""
    import yaml

    config_data = {"test-yaml-client": SAMPLE_CLIENT_DATA | {"display_name": "Test YAML Client"}}
    config_file = tmp_path / "clients.yaml"
    config_file.write_text(yaml.dump(config_data))

    with patch("proxy.mcp_gateway.router.firestore.Client", side_effect=Exception("no firestore")):
        router = ClientRouter(
            partner_project_id="test-project",
            local_config_path=str(config_file),
        )
        config = router.get_client("test-yaml-client")

    assert config.display_name == "Test YAML Client"
