import json
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("PARTNER_PROJECT_ID", "test-project")
os.environ.setdefault("DEV_MODE", "true")


def _mock_mcp_client():
    client = AsyncMock()
    return client


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


@pytest.fixture
def mock_mcp():
    return _mock_mcp_client()


_ADMIN_ANALYST = {
    "email": "dev@local",
    "role": "admin",
    "allowed_clients": ["client-a"],
    "auth_method": "dev_mode",
}


@pytest_asyncio.fixture
async def client(mock_db, mock_mcp):
    with patch("workbench.backend.main.firestore"):
        from workbench.backend.main import app

    app.state.db = mock_db
    app.state.mcp_client = mock_mcp
    app.state.http_client = AsyncMock()
    app.state.mcp_gateway_url = "http://gateway:8080"
    app.state.audit = MagicMock()

    from workbench.backend.main import BackgroundTaskManager
    app.state.tasks = BackgroundTaskManager()

    from workbench.backend.cases import router
    if not any(r.path == "/api/cases" for r in app.routes):
        app.include_router(router, prefix="/api")

    # Override auth dependency so all tests get a consistent admin analyst
    # without depending on the Firestore mock chain for analyst_assignments.
    # Use the reference that cases.py captured at import time (survives auth module reloads).
    from workbench.backend import cases as cases_mod

    async def _override_analyst():
        return _ADMIN_ANALYST

    auth_dep = cases_mod.get_current_analyst
    app.dependency_overrides[auth_dep] = _override_analyst

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(auth_dep, None)


# ---------------------------------------------------------------------------
# Task 5: List + Detail tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_cases(client, mock_mcp):
    mock_mcp.call_tool.return_value = {
        "cases": [
            {"id": "1", "name": "Phishing Alert", "priority": "HIGH", "status": "OPENED"},
            {"id": "2", "name": "Malware Alert", "priority": "MEDIUM", "status": "OPENED"},
        ]
    }

    resp = await client.get("/api/cases")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["cases"]) == 2
    assert data["cases"][0]["id"] == "1"


@pytest.mark.asyncio
async def test_list_cases_with_status_filter(client, mock_mcp):
    mock_mcp.call_tool.return_value = {"cases": []}

    resp = await client.get("/api/cases?status=CLOSED")
    assert resp.status_code == 200
    call_args = mock_mcp.call_tool.call_args
    assert "CLOSED" in str(call_args)


@pytest.mark.asyncio
async def test_get_case_detail(client, mock_mcp, mock_db):
    mock_mcp.call_tool.side_effect = [
        {"id": "123", "name": "Phishing", "priority": "HIGH", "status": "OPENED"},
        {"alerts": [{"id": "alert-1", "name": "Suspicious Email"}]},
    ]

    stage_doc = MagicMock()
    stage_doc.to_dict.return_value = {
        "stage_id": "s1",
        "stage_name": "triage",
        "status": "COMPLETED",
        "output_structured": {"verdict": "SUSPICIOUS"},
    }
    mock_db.collection.return_value.where.return_value.order_by.return_value.stream.return_value = [
        stage_doc
    ]
    mock_db.collection.return_value.where.return_value.where.return_value.order_by.return_value.stream.return_value = [
        stage_doc
    ]
    mock_db.collection.return_value.where.return_value.where.return_value.stream.return_value = []

    resp = await client.get("/api/cases/123?client_id=client-a")
    assert resp.status_code == 200
    data = resp.json()
    assert data["case"]["id"] == "123"
    assert len(data["alerts"]) == 1


@pytest.mark.asyncio
async def test_get_case_requires_client_id(client):
    resp = await client.get("/api/cases/123")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Task 6: Action tests
# ---------------------------------------------------------------------------

class TestCaseActions:
    @pytest.fixture(autouse=True)
    def setup_approval(self, mock_db):
        doc = MagicMock()
        doc.exists = True
        doc.to_dict.return_value = {
            "approval_id": "appr-1",
            "client_id": "client-a",
            "case_id": "case-123",
            "status": "PENDING",
            "proposed_action": {"action": "isolate_host", "target": "host-1"},
            "triage_summary": "Malicious phishing detected",
            "created_at": "2026-03-29T00:00:00Z",
        }
        mock_db.collection.return_value.document.return_value.get.return_value = doc
        self.approval_doc = doc

    @pytest.mark.asyncio
    async def test_approve_case(self, client, mock_db):
        resp = await client.post(
            "/api/cases/case-123/approve",
            json={
                "approval_id": "appr-1",
                "analyst_notes": "Confirmed malicious",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_reject_case(self, client, mock_db):
        resp = await client.post(
            "/api/cases/case-123/reject",
            json={
                "approval_id": "appr-1",
                "analyst_notes": "False positive",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_approve_already_decided(self, client, mock_db):
        doc = mock_db.collection.return_value.document.return_value.get.return_value
        doc.to_dict.return_value["status"] = "APPROVED"
        resp = await client.post(
            "/api/cases/case-123/approve",
            json={"approval_id": "appr-1"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_approve_not_found(self, client, mock_db):
        doc = mock_db.collection.return_value.document.return_value.get.return_value
        doc.exists = False
        resp = await client.post(
            "/api/cases/case-123/approve",
            json={"approval_id": "appr-not-exist"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_trigger_pipeline(self, client, mock_mcp):
        with patch("workbench.backend.cases._trigger_pipeline", new_callable=AsyncMock) as mock_trigger:
            mock_trigger.return_value = {"status": "STARTED", "session_id": "sess-1"}
            resp = await client.post(
                "/api/cases/case-123/trigger",
                json={"client_id": "client-a", "alert_type": "PHISHING"},
            )
        assert resp.status_code == 200
        data = resp.json()
        # Pipeline now runs as background task, returns ACCEPTED immediately
        assert data["status"] == "ACCEPTED"
        assert data["case_id"] == "case-123"
