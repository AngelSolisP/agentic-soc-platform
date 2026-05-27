import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("PARTNER_PROJECT_ID", "test-project")
os.environ.setdefault("DEV_MODE", "true")


@pytest.fixture
def mock_db():
    db = MagicMock()
    # In DEV_MODE auth loads analyst profile; return doc.exists=False so the
    # hardcoded admin fallback fires (role=admin, allowed_clients=[])
    no_profile = MagicMock()
    no_profile.exists = False
    db.collection.return_value.document.return_value.get.return_value = no_profile
    return db


@pytest_asyncio.fixture
async def client(mock_db):
    with patch("workbench.backend.main.firestore"):
        from workbench.backend.main import app

    app.state.db = mock_db
    app.state.http_client = AsyncMock()
    app.state.mcp_gateway_url = "http://gateway:8080"
    app.state.mcp_client = AsyncMock()
    app.state.audit = MagicMock()

    from workbench.backend.chat import router

    if not any(getattr(r, "path", "") == "/api/cases/{case_id}/chat" for r in app.routes):
        app.include_router(router, prefix="/api")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_chat_message(client):
    with patch("workbench.backend.chat._query_agent", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = {
            "response": "The IP 1.2.3.4 has been seen in 3 malware campaigns.",
            "tool_calls": [
                {"tool": "search_entity", "args": {"indicator": "1.2.3.4"}, "result": "..."}
            ],
        }
        resp = await client.post(
            "/api/cases/case-123/chat",
            json={"message": "What do we know about IP 1.2.3.4?", "client_id": "client-a"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert len(data["tool_calls"]) == 1


@pytest.mark.asyncio
async def test_chat_requires_message(client):
    resp = await client.post(
        "/api/cases/case-123/chat",
        json={"client_id": "client-a"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_chat_requires_client_id(client):
    resp = await client.post(
        "/api/cases/case-123/chat",
        json={"message": "hello"},
    )
    assert resp.status_code == 422
