import os
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("PARTNER_PROJECT_ID", "test-project")
os.environ.setdefault("DEV_MODE", "true")


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


def _make_admin_profile():
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = {
        "email": "admin@mssp.com",
        "role": "admin",
        "allowed_clients": [],
    }
    return doc


@pytest_asyncio.fixture
async def admin_client(mock_db):
    with patch("workbench.backend.main.firestore"):
        from workbench.backend.main import app

    app.state.db = mock_db
    app.state.http_client = AsyncMock()
    app.state.mcp_gateway_url = "http://gateway:8080"
    app.state.mcp_client = AsyncMock()
    app.state.audit = MagicMock()

    mock_db.collection.return_value.document.return_value.get.return_value = _make_admin_profile()

    from workbench.backend.admin import router

    if not any(getattr(r, "path", "").startswith("/api/admin") for r in app.routes):
        app.include_router(router, prefix="/api/admin")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_admin_dashboard(admin_client, mock_db):
    client_doc = MagicMock()
    client_doc.to_dict.return_value = {"client_id": "client-a", "enabled": True}
    mock_db.collection.return_value.stream.return_value = [client_doc]
    mock_db.collection.return_value.where.return_value.stream.return_value = []

    resp = await admin_client.get(
        "/api/admin/dashboard",
        headers={"Authorization": "Bearer dev-token"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "clients" in data
    assert "kpis" in data


@pytest.mark.asyncio
async def test_list_clients(admin_client, mock_db):
    doc = MagicMock()
    doc.id = "client-a"
    doc.to_dict.return_value = {
        "client_id": "client-a",
        "display_name": "Client A",
        "enabled": True,
    }
    mock_db.collection.return_value.stream.return_value = [doc]

    resp = await admin_client.get(
        "/api/admin/clients",
        headers={"Authorization": "Bearer dev-token"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["clients"]) == 1


@pytest.mark.asyncio
async def test_create_client(admin_client, mock_db):
    resp = await admin_client.post(
        "/api/admin/clients",
        json={
            "client_id": "new-client",
            "display_name": "New Client",
            "gcp_project_id": "new-proj",
            "chronicle_customer_id": "cust-123",
            "chronicle_region": "us",
            "service_account_email": "sa@proj.iam.gserviceaccount.com",
        },
        headers={"Authorization": "Bearer dev-token"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_analysts(admin_client, mock_db):
    doc = MagicMock()
    doc.id = "analyst@mssp.com"
    doc.to_dict.return_value = {
        "email": "analyst@mssp.com",
        "role": "analyst",
        "allowed_clients": ["client-a"],
    }
    mock_db.collection.return_value.stream.return_value = [doc]

    resp = await admin_client.get(
        "/api/admin/analysts",
        headers={"Authorization": "Bearer dev-token"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["analysts"]) == 1


@pytest.mark.asyncio
async def test_update_analyst(admin_client, mock_db):
    resp = await admin_client.put(
        "/api/admin/analysts/analyst@mssp.com",
        json={"role": "analyst", "allowed_clients": ["client-a", "client-b"]},
        headers={"Authorization": "Bearer dev-token"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_audit_log(admin_client, mock_db):
    doc = MagicMock()
    doc.to_dict.return_value = {
        "timestamp": "2026-03-29T00:00:00Z",
        "actor": "analyst@mssp.com",
        "action": "CASE_APPROVED",
        "client_id": "client-a",
    }
    mock_db.collection.return_value.order_by.return_value.limit.return_value.stream.return_value = [doc]

    resp = await admin_client.get(
        "/api/admin/audit",
        headers={"Authorization": "Bearer dev-token"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["entries"]) == 1
