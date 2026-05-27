import os
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("PARTNER_PROJECT_ID", "test-project")
os.environ.setdefault("DEV_MODE", "false")


@pytest.fixture(autouse=True)
def mock_firestore():
    with patch("workbench.backend.main.firestore") as mock_fs:
        db_mock = MagicMock()
        mock_fs.Client.return_value = db_mock
        yield db_mock


@pytest_asyncio.fixture
async def client(mock_firestore):
    from workbench.backend.main import app

    app.state.db = mock_firestore
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "agentic-soc-workbench"


@pytest.mark.asyncio
async def test_health_ready_ok(client, mock_firestore):
    mock_firestore.collection.return_value.limit.return_value.stream.return_value = []
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_health_ready_fail(client, mock_firestore):
    mock_firestore.collection.return_value.limit.return_value.stream.side_effect = (
        Exception("Firestore down")
    )
    resp = await client.get("/health/ready")
    assert resp.status_code == 503
