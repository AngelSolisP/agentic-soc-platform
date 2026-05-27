import os
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI, Depends, Request

os.environ.setdefault("PARTNER_PROJECT_ID", "test-project")
os.environ["DEV_MODE"] = "false"  # Force false — other test files may set true


@pytest.fixture(autouse=True)
def reset_dev_mode():
    """Ensure DEV_MODE is false for every auth test (other test fixtures may leak true)."""
    original = os.environ.get("DEV_MODE", "false")
    os.environ["DEV_MODE"] = "false"
    yield
    os.environ["DEV_MODE"] = original


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


@pytest.fixture
def analyst_doc():
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = {
        "email": "analyst@mssp.com",
        "role": "analyst",
        "allowed_clients": ["client-a", "client-b"],
    }
    return doc


@pytest.fixture
def admin_doc():
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = {
        "email": "admin@mssp.com",
        "role": "admin",
        "allowed_clients": [],
    }
    return doc


def test_load_analyst_profile_found(mock_db, analyst_doc):
    from workbench.backend.auth import _load_analyst_profile

    mock_db.collection.return_value.document.return_value.get.return_value = analyst_doc
    profile = _load_analyst_profile(mock_db, "analyst@mssp.com")
    assert profile["role"] == "analyst"
    assert "client-a" in profile["allowed_clients"]


def test_load_analyst_profile_not_found(mock_db):
    from workbench.backend.auth import _load_analyst_profile

    doc = MagicMock()
    doc.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = doc
    profile = _load_analyst_profile(mock_db, "unknown@mssp.com")
    assert profile is None


@pytest_asyncio.fixture
async def auth_test_app(mock_db, analyst_doc):
    from workbench.backend.auth import get_current_analyst, require_admin

    test_app = FastAPI()

    @test_app.get("/protected")
    async def protected(analyst=Depends(get_current_analyst)):
        return {"email": analyst["email"], "role": analyst["role"]}

    @test_app.get("/admin-only")
    async def admin_only(analyst=Depends(require_admin)):
        return {"email": analyst["email"]}

    test_app.state.db = mock_db
    mock_db.collection.return_value.document.return_value.get.return_value = analyst_doc

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_oidc_token_auth(auth_test_app):
    with patch("workbench.backend.auth._verify_oidc_token", return_value="analyst@mssp.com"):
        resp = await auth_test_app.get(
            "/protected",
            headers={"Authorization": "Bearer fake-oidc-token"},
        )
    assert resp.status_code == 200
    assert resp.json()["email"] == "analyst@mssp.com"


@pytest.mark.asyncio
async def test_no_auth_returns_401(mock_db):
    from workbench.backend.auth import get_current_analyst

    test_app = FastAPI()

    @test_app.get("/protected")
    async def protected(analyst=Depends(get_current_analyst)):
        return {"ok": True}

    test_app.state.db = mock_db
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as c:
        resp = await c.get("/protected")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dev_mode_bypasses_auth(mock_db, analyst_doc):
    os.environ["DEV_MODE"] = "true"
    try:
        import importlib
        import workbench.backend.auth as auth_mod
        importlib.reload(auth_mod)

        test_app = FastAPI()

        @test_app.get("/protected")
        async def protected(analyst=Depends(auth_mod.get_current_analyst)):
            return {"email": analyst["email"]}

        test_app.state.db = mock_db
        mock_db.collection.return_value.document.return_value.get.return_value = analyst_doc

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as c:
            resp = await c.get("/protected")
        assert resp.status_code == 200
    finally:
        os.environ["DEV_MODE"] = "false"
        importlib.reload(auth_mod)


@pytest.mark.asyncio
async def test_analyst_cannot_access_admin(auth_test_app):
    with patch("workbench.backend.auth._verify_oidc_token", return_value="analyst@mssp.com"):
        resp = await auth_test_app.get(
            "/admin-only",
            headers={"Authorization": "Bearer fake-oidc-token"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_admin(mock_db, admin_doc):
    from workbench.backend.auth import get_current_analyst, require_admin

    test_app = FastAPI()

    @test_app.get("/admin-only")
    async def admin_only(analyst=Depends(require_admin)):
        return {"email": analyst["email"]}

    test_app.state.db = mock_db
    mock_db.collection.return_value.document.return_value.get.return_value = admin_doc

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as c:
        with patch("workbench.backend.auth._verify_oidc_token", return_value="admin@mssp.com"):
            resp = await c.get(
                "/admin-only",
                headers={"Authorization": "Bearer fake-oidc-token"},
            )
    assert resp.status_code == 200
