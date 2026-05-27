"""Tests for HITL security hardening.

Covers:
- JWT-based analyst_id: decided_by must come from JWT claims, not request body
- Firestore transaction: concurrent decisions get 409 Conflict
- Per-client authorization: analysts only access their assigned clients
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from httpx import AsyncClient, ASGITransport

from ui.hitl_dashboard.backend.main import app
from proxy.mcp_gateway.auth_middleware import require_analyst_auth, require_auth


# ── Helpers ──────────────────────────────────────────────────────────────────

def _mock_pending_doc(client_id="acme", case_id="CASE-1"):
    """Return a mock Firestore document snapshot for a PENDING approval."""
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = {
        "approval_id": "approval-sec-1",
        "client_id": client_id,
        "case_id": case_id,
        "agent_name": "response_agent_acme",
        "session_id": "sess-1",
        "status": "PENDING",
        "proposed_action": {"action": "isolate_endpoint", "target": "host-1"},
        "triage_summary": "Malware detected on host-1",
        "analyst_instructions": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "decided_by": None,
        "decided_at": None,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }
    return doc


def _mock_decided_doc(status="APPROVED"):
    """Return a mock Firestore document snapshot for an already-decided approval."""
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = {
        "status": status,
        "client_id": "acme",
        "case_id": "CASE-1",
        "decided_by": "first-analyst@company.com",
    }
    return doc


def _setup_mock_db(doc, *, with_transaction=True):
    """Create a mock Firestore client that returns the given doc."""
    mock_db = MagicMock()
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = doc
    mock_db.collection.return_value.document.return_value = mock_doc_ref

    if with_transaction:
        mock_tx = MagicMock()
        mock_tx.get = MagicMock(return_value=doc)
        mock_db.transaction.return_value = mock_tx
        # Make doc_ref.get(transaction=tx) also return the doc
        mock_doc_ref.get.return_value = doc

    return mock_db


def _override_auth(email):
    """Set FastAPI dependency override for require_analyst_auth."""
    app.dependency_overrides[require_analyst_auth] = lambda: {
        "email": email,
        "auth_method": "google_id_token",
    }


def _clear_overrides():
    app.dependency_overrides.clear()


async def _decide(client, approval_id, decision="APPROVED", analyst_notes="", analyst_id="ignored@evil.com"):
    """POST a decision to the decide endpoint."""
    return await client.post(
        f"/approvals/{approval_id}/decide",
        json={
            "decision": decision,
            "analyst_id": analyst_id,
            "analyst_notes": analyst_notes,
        },
    )


# ── Test: JWT-based analyst_id ───────────────────────────────────────────────

class TestAnalystIdentityFromJWT:
    """analyst_id must come from JWT claims, not request body."""

    @pytest.mark.asyncio
    async def test_decided_by_uses_jwt_email_not_body(self):
        """The decided_by field should use the caller's JWT email, ignoring body analyst_id."""
        pending_doc = _mock_pending_doc()
        mock_db = _setup_mock_db(pending_doc)

        _override_auth("real-analyst@company.com")
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await _decide(client, "approval-sec-1", analyst_id="fake@evil.com")

                assert resp.status_code == 200

                # Check what was written via transaction
                tx = mock_db.transaction.return_value
                assert tx.update.called
                update_data = tx.update.call_args[0][1]
                assert update_data["decided_by"] == "real-analyst@company.com"
        finally:
            _clear_overrides()

    @pytest.mark.asyncio
    async def test_body_analyst_id_ignored(self):
        """Even if body has analyst_id=evil@attacker.com, decided_by uses JWT email."""
        pending_doc = _mock_pending_doc()
        mock_db = _setup_mock_db(pending_doc)

        _override_auth("legit@company.com")
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await client.post(
                        "/approvals/approval-sec-1/decide",
                        json={
                            "decision": "APPROVED",
                            "analyst_id": "evil@attacker.com",
                            "analyst_notes": "Looks good",
                        },
                    )

                assert resp.status_code == 200
                tx = mock_db.transaction.return_value
                update_data = tx.update.call_args[0][1]
                assert update_data["decided_by"] == "legit@company.com"
                assert update_data["decided_by"] != "evil@attacker.com"
        finally:
            _clear_overrides()


# ── Test: Firestore transaction ──────────────────────────────────────────────

class TestApprovalTransaction:
    """Approval decisions must use Firestore transactions to prevent race conditions."""

    @pytest.mark.asyncio
    async def test_already_decided_returns_409(self):
        """If approval is already decided, return 409 Conflict."""
        decided_doc = _mock_decided_doc("APPROVED")
        mock_db = _setup_mock_db(decided_doc)

        _override_auth("analyst@co.com")
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await _decide(client, "approval-sec-1")

                assert resp.status_code == 409
                assert "already decided" in resp.json()["detail"].lower()
        finally:
            _clear_overrides()

    @pytest.mark.asyncio
    async def test_decide_uses_transaction(self):
        """The decide endpoint must use db.transaction() for atomic read+update."""
        pending_doc = _mock_pending_doc()
        mock_db = _setup_mock_db(pending_doc)

        _override_auth("analyst@co.com")
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await _decide(client, "approval-sec-1")

                assert resp.status_code == 200
                assert mock_db.transaction.called, "decide_approval must use Firestore transactions"
                tx = mock_db.transaction.return_value
                assert tx.update.called, "transaction.update must be called"
        finally:
            _clear_overrides()

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self):
        """Non-existent approval should return 404."""
        missing_doc = MagicMock()
        missing_doc.exists = False
        mock_db = _setup_mock_db(missing_doc)

        _override_auth("analyst@co.com")
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await _decide(client, "does-not-exist")

                assert resp.status_code == 404
        finally:
            _clear_overrides()


# ── Test: Per-client analyst authorization ───────────────────────────────────

class TestPerClientAuth:
    """Analysts must only access approvals for their assigned clients."""

    @pytest.mark.asyncio
    async def test_analyst_can_decide_own_client(self):
        """Analyst assigned to acme CAN decide acme approvals."""
        pending_doc = _mock_pending_doc(client_id="acme")
        mock_db = _setup_mock_db(pending_doc)

        # Mock analyst_assignments lookup
        assignment_doc = MagicMock()
        assignment_doc.exists = True
        assignment_doc.to_dict.return_value = {"allowed_clients": ["acme", "globex"]}

        original_collection = mock_db.collection.return_value
        def collection_side_effect(name):
            if name == "analyst_assignments":
                mock_coll = MagicMock()
                mock_coll.document.return_value.get.return_value = assignment_doc
                return mock_coll
            return original_collection

        mock_db.collection.side_effect = collection_side_effect

        _override_auth("analyst@co.com")
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db), \
                 patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", True):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await _decide(client, "approval-sec-1")

                assert resp.status_code == 200
        finally:
            _clear_overrides()

    @pytest.mark.asyncio
    async def test_analyst_cannot_decide_other_client(self):
        """Analyst assigned to acme CANNOT decide globex approvals."""
        pending_doc = _mock_pending_doc(client_id="globex")
        mock_db = _setup_mock_db(pending_doc)

        # Analyst only assigned to acme
        assignment_doc = MagicMock()
        assignment_doc.exists = True
        assignment_doc.to_dict.return_value = {"allowed_clients": ["acme"]}

        original_collection = mock_db.collection.return_value
        def collection_side_effect(name):
            if name == "analyst_assignments":
                mock_coll = MagicMock()
                mock_coll.document.return_value.get.return_value = assignment_doc
                return mock_coll
            return original_collection

        mock_db.collection.side_effect = collection_side_effect

        _override_auth("analyst@co.com")
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db), \
                 patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", True):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await _decide(client, "approval-sec-1")

                assert resp.status_code == 403
                assert "not authorized" in resp.json()["detail"].lower()
        finally:
            _clear_overrides()

    @pytest.mark.asyncio
    async def test_no_assignment_doc_returns_403(self):
        """If analyst has no assignment doc, deny access when enforcement is on."""
        pending_doc = _mock_pending_doc(client_id="acme")
        mock_db = _setup_mock_db(pending_doc)

        # No assignment doc for this analyst
        missing_assignment = MagicMock()
        missing_assignment.exists = False

        original_collection = mock_db.collection.return_value
        def collection_side_effect(name):
            if name == "analyst_assignments":
                mock_coll = MagicMock()
                mock_coll.document.return_value.get.return_value = missing_assignment
                return mock_coll
            return original_collection

        mock_db.collection.side_effect = collection_side_effect

        _override_auth("unknown@co.com")
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db), \
                 patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", True):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await _decide(client, "approval-sec-1")

                assert resp.status_code == 403
        finally:
            _clear_overrides()

    @pytest.mark.asyncio
    async def test_enforcement_off_allows_all(self):
        """When ENFORCE_CLIENT_AUTH is false, all analysts can decide any client."""
        pending_doc = _mock_pending_doc(client_id="globex")
        mock_db = _setup_mock_db(pending_doc)

        _override_auth("anyone@co.com")
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db), \
                 patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", False):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await _decide(client, "approval-sec-1")

                assert resp.status_code == 200
        finally:
            _clear_overrides()


# ── Test: Read endpoint tenant isolation ─────────────────────────────────────

class TestReadEndpointTenantIsolation:
    """All read endpoints must respect per-client auth when ENFORCE_CLIENT_AUTH=True."""

    @pytest.mark.asyncio
    async def test_list_approvals_filters_by_caller_clients(self):
        """Analyst with [acme] only sees acme approvals."""
        mock_db = MagicMock()
        assignment_doc = MagicMock()
        assignment_doc.exists = True
        assignment_doc.to_dict.return_value = {"allowed_clients": ["acme"]}

        def collection_side_effect(name):
            mock_coll = MagicMock()
            if name == "analyst_assignments":
                mock_coll.document.return_value.get.return_value = assignment_doc
            else:
                q = mock_coll
                q.where.return_value = q
                q.order_by.return_value = q
                q.limit.return_value = q
                q.stream.return_value = []
            return mock_coll

        mock_db.collection.side_effect = collection_side_effect

        app.dependency_overrides[require_auth] = lambda: {"email": "analyst@co.com", "auth_method": "google_id_token"}
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db), \
                 patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", True):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await client.get("/approvals")
                    assert resp.status_code == 200

                    # With wrong client_id — should 403
                    resp = await client.get("/approvals?client_id=globex")
                    assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_approval_checks_client_scope(self):
        """get_approval by ID must verify the doc's client_id is in caller's scope."""
        mock_db = MagicMock()
        approval_doc = MagicMock()
        approval_doc.exists = True
        approval_doc.to_dict.return_value = {
            "approval_id": "test-1", "client_id": "globex", "case_id": "C-1",
            "agent_name": "resp", "session_id": "s", "status": "PENDING",
            "proposed_action": {}, "triage_summary": "", "analyst_instructions": "",
            "created_at": "2026-01-01", "updated_at": "2026-01-01",
            "decided_by": None, "decided_at": None,
        }
        assignment_doc = MagicMock()
        assignment_doc.exists = True
        assignment_doc.to_dict.return_value = {"allowed_clients": ["acme"]}

        def collection_side_effect(name):
            mock_coll = MagicMock()
            if name == "analyst_assignments":
                mock_coll.document.return_value.get.return_value = assignment_doc
            else:
                mock_coll.document.return_value.get.return_value = approval_doc
            return mock_coll

        mock_db.collection.side_effect = collection_side_effect

        app.dependency_overrides[require_auth] = lambda: {"email": "analyst@co.com", "auth_method": "google_id_token"}
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db), \
                 patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", True):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await client.get("/approvals/test-1")
                    assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_stats_filters_by_scope(self):
        """Stats should only count docs from allowed clients."""
        mock_db = MagicMock()
        assignment_doc = MagicMock()
        assignment_doc.exists = True
        assignment_doc.to_dict.return_value = {"allowed_clients": ["acme"]}

        acme_doc = MagicMock()
        acme_doc.to_dict.return_value = {"status": "PENDING", "client_id": "acme"}
        globex_doc = MagicMock()
        globex_doc.to_dict.return_value = {"status": "PENDING", "client_id": "globex"}

        # __stats__ doc does not exist → triggers one-time collection scan fallback
        stats_counter_doc = MagicMock()
        stats_counter_doc.exists = False

        def collection_side_effect(name):
            mock_coll = MagicMock()
            if name == "analyst_assignments":
                mock_coll.document.return_value.get.return_value = assignment_doc
            else:
                mock_coll.document.return_value.get.return_value = stats_counter_doc
                mock_coll.stream.return_value = [acme_doc, globex_doc]
            return mock_coll

        mock_db.collection.side_effect = collection_side_effect

        app.dependency_overrides[require_auth] = lambda: {"email": "analyst@co.com", "auth_method": "google_id_token"}
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db), \
                 patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", True):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await client.get("/stats")
                    assert resp.status_code == 200
                    data = resp.json()
                    # Only acme's PENDING should be counted
                    assert data["stats"]["PENDING"] == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_enforcement_off_returns_all(self):
        """When ENFORCE_CLIENT_AUTH is false, all data is visible."""
        mock_db = MagicMock()

        acme_doc = MagicMock()
        acme_doc.to_dict.return_value = {
            "approval_id": "a-1", "client_id": "acme", "case_id": "C-1",
            "agent_name": "resp", "session_id": "s", "status": "PENDING",
            "proposed_action": {}, "triage_summary": "", "analyst_instructions": "",
            "created_at": "2026-01-01", "updated_at": "2026-01-01",
            "decided_by": None, "decided_at": None,
        }

        q = mock_db.collection.return_value
        q.where.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.stream.return_value = [acme_doc]

        app.dependency_overrides[require_auth] = lambda: {"email": "anyone@co.com", "auth_method": "google_id_token"}
        try:
            with patch("ui.hitl_dashboard.backend.main.get_db", return_value=mock_db), \
                 patch("ui.hitl_dashboard.backend.main.ENFORCE_CLIENT_AUTH", False):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await client.get("/approvals")
                    assert resp.status_code == 200
                    assert len(resp.json()) == 1
        finally:
            app.dependency_overrides.clear()
