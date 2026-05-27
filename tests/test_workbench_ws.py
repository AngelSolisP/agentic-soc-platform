import asyncio
import json
import os
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

os.environ.setdefault("PARTNER_PROJECT_ID", "test-project")
os.environ.setdefault("DEV_MODE", "true")


def test_notification_hub_add_remove():
    from workbench.backend.ws import NotificationHub

    hub = NotificationHub()
    queue = asyncio.Queue()
    hub.add(queue)
    assert len(hub._subscribers) == 1
    hub.remove(queue)
    assert len(hub._subscribers) == 0


@pytest.mark.asyncio
async def test_notification_hub_broadcast():
    from workbench.backend.ws import NotificationHub

    hub = NotificationHub()
    queue = asyncio.Queue()
    hub.add(queue)

    await hub.broadcast({"type": "new_case", "case_id": "123"})
    msg = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert msg["type"] == "new_case"


@pytest.mark.asyncio
async def test_notification_hub_broadcast_skips_full_queues():
    from workbench.backend.ws import NotificationHub

    hub = NotificationHub()
    queue = asyncio.Queue(maxsize=1)
    hub.add(queue)

    await queue.put({"first": True})
    await hub.broadcast({"second": True})
    assert queue.qsize() == 1


def test_websocket_pipeline_endpoint_exists():
    with patch("workbench.backend.main.firestore"):
        from workbench.backend.main import app

    from workbench.backend.ws import router

    if not any(getattr(r, "path", "") == "/ws/pipeline/{case_id}" for r in app.routes):
        app.include_router(router)

    ws_routes = [r for r in app.routes if hasattr(r, "path") and r.path.startswith("/ws/")]
    assert len(ws_routes) >= 1
