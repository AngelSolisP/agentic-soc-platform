"""Admin endpoints — client management, analyst assignment, metrics, audit."""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from workbench.backend.auth import require_admin
from workbench.backend.audit import AuditAction
from workbench.backend.metrics import get_agent_performance

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])

CLIENTS_COLLECTION = "clients"
ANALYSTS_COLLECTION = "analyst_assignments"
HITL_COLLECTION = "hitl_approvals"
AUDIT_COLLECTION = "audit_log"


class CreateClientRequest(BaseModel):
    client_id: str
    display_name: str
    gcp_project_id: str
    chronicle_customer_id: str
    chronicle_region: str = "us"
    service_account_email: str
    enabled: bool = True
    autonomous_mode: bool = False
    gti_enabled: bool = False
    soar_environment_id: str = ""


class UpdateClientRequest(BaseModel):
    display_name: Optional[str] = None
    enabled: Optional[bool] = None
    autonomous_mode: Optional[bool] = None
    gti_enabled: Optional[bool] = None
    soar_environment_id: Optional[str] = None


class UpdateAnalystRequest(BaseModel):
    role: str = "analyst"
    allowed_clients: list[str] = []


@router.get("/dashboard")
async def admin_dashboard(
    request: Request,
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db

    clients = list(db.collection(CLIENTS_COLLECTION).stream())
    enabled_clients = [c for c in clients if c.to_dict().get("enabled", True)]

    pending = list(
        db.collection(HITL_COLLECTION)
        .where("status", "==", "PENDING")
        .stream()
    )

    return {
        "clients": {
            "total": len(clients),
            "enabled": len(enabled_clients),
        },
        "kpis": {
            "pending_approvals": len(pending),
            "total_clients": len(enabled_clients),
        },
    }


@router.get("/clients")
async def list_clients(
    request: Request,
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db
    docs = db.collection(CLIENTS_COLLECTION).stream()
    clients = [{"id": d.id, **d.to_dict()} for d in docs]
    return {"clients": clients}


@router.post("/clients", status_code=201)
async def create_client(
    body: CreateClientRequest,
    request: Request,
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db
    doc_data = body.model_dump()
    doc_data["created_at"] = datetime.now(timezone.utc)
    doc_data["created_by"] = admin["email"]

    db.collection(CLIENTS_COLLECTION).document(body.client_id).set(doc_data)

    request.app.state.audit.log(
        actor=admin["email"],
        actor_type="admin",
        action=AuditAction.CLIENT_CREATED,
        client_id=body.client_id,
        details={"display_name": body.display_name},
    )
    return {"client_id": body.client_id, "status": "created"}


@router.put("/clients/{client_id}")
async def update_client(
    client_id: str,
    body: UpdateClientRequest,
    request: Request,
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = admin["email"]

    db.collection(CLIENTS_COLLECTION).document(client_id).update(update_data)

    request.app.state.audit.log(
        actor=admin["email"],
        actor_type="admin",
        action=AuditAction.CLIENT_UPDATED,
        client_id=client_id,
        details=update_data,
    )
    return {"client_id": client_id, "status": "updated"}


@router.delete("/clients/{client_id}")
async def disable_client(
    client_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db
    db.collection(CLIENTS_COLLECTION).document(client_id).update({
        "enabled": False,
        "disabled_at": datetime.now(timezone.utc),
        "disabled_by": admin["email"],
    })

    request.app.state.audit.log(
        actor=admin["email"],
        actor_type="admin",
        action=AuditAction.CLIENT_DISABLED,
        client_id=client_id,
    )
    return {"client_id": client_id, "status": "disabled"}


@router.get("/analysts")
async def list_analysts(
    request: Request,
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db
    docs = db.collection(ANALYSTS_COLLECTION).stream()
    analysts = [{"email": d.id, **d.to_dict()} for d in docs]
    return {"analysts": analysts}


@router.put("/analysts/{email}")
async def update_analyst(
    email: str,
    body: UpdateAnalystRequest,
    request: Request,
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db
    doc_data = body.model_dump()
    doc_data["email"] = email
    doc_data["updated_at"] = datetime.now(timezone.utc)
    doc_data["updated_by"] = admin["email"]

    db.collection(ANALYSTS_COLLECTION).document(email).set(doc_data, merge=True)

    request.app.state.audit.log(
        actor=admin["email"],
        actor_type="admin",
        action=AuditAction.ANALYST_UPDATED,
        client_id="*",
        details={"target_analyst": email, "role": body.role, "clients": body.allowed_clients},
    )
    return {"email": email, "status": "updated"}


@router.delete("/analysts/{email}")
async def delete_analyst(
    email: str,
    request: Request,
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db
    doc = db.collection(ANALYSTS_COLLECTION).document(email).get()
    if not doc.exists:
        raise HTTPException(404, "Analyst not found")

    db.collection(ANALYSTS_COLLECTION).document(email).delete()

    request.app.state.audit.log(
        actor=admin["email"],
        actor_type="admin",
        action=AuditAction.ANALYST_DELETED,
        client_id="*",
        details={"target_analyst": email},
    )
    return {"email": email, "status": "deleted"}


@router.get("/performance")
async def agent_performance(
    request: Request,
    client_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db
    metrics = get_agent_performance(db, client_id=client_id, days=days)
    return {"metrics": metrics, "period_days": days}


@router.get("/audit")
async def get_audit_log(
    request: Request,
    client_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    admin: dict = Depends(require_admin),
):
    db = request.app.state.db
    query = db.collection(AUDIT_COLLECTION)

    if client_id:
        query = query.where("client_id", "==", client_id)
    if action:
        query = query.where("action", "==", action)

    query = query.order_by("timestamp", direction="DESCENDING").limit(limit)
    docs = query.stream()

    entries = []
    for doc in docs:
        entry = doc.to_dict()
        if hasattr(entry.get("timestamp"), "isoformat"):
            entry["timestamp"] = entry["timestamp"].isoformat()
        entries.append(entry)

    return {"entries": entries, "count": len(entries)}
