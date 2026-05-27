"""
HITL Dashboard Backend — FastAPI

Provides the API for analysts to review and approve/reject/modify
agent-proposed actions. Reads/writes to the Firestore HITL approval queue.
"""

import os
import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import httpx
from google.cloud import firestore
import google.auth.transport.requests
import google.oauth2.id_token
from observability.tracing import init_tracing, get_tracer, shutdown_tracing, register_sigterm_handler
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import propagate

from proxy.mcp_gateway.auth_middleware import require_auth, require_analyst_auth

logger = logging.getLogger(__name__)

PARTNER_PROJECT_ID = os.environ.get("PARTNER_PROJECT_ID", "")
FIRESTORE_DATABASE = os.environ.get("FIRESTORE_DATABASE", "(default)")
HITL_COLLECTION = "hitl_approvals"
STAGES_COLLECTION = "workflow_stages"
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
APPROVAL_CALLBACK_URL = os.environ.get("APPROVAL_CALLBACK_URL", "")
ENFORCE_CLIENT_AUTH = os.environ.get("ENFORCE_CLIENT_AUTH", "true").lower() == "true"
ANALYST_ASSIGNMENTS_COLLECTION = "analyst_assignments"

app = FastAPI(
    title="Agentic SOC — HITL Dashboard API",
    version="1.0.0",
    description="Human-in-the-Loop approval queue for AI agent actions",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["http://localhost:8501", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "traceparent", "tracestate"],
    allow_credentials=True,
)

init_tracing("agentic-soc-hitl")
register_sigterm_handler()
FastAPIInstrumentor.instrument_app(app)


@lru_cache(maxsize=1)
def get_db() -> firestore.Client:
    return firestore.Client(
        project=PARTNER_PROJECT_ID, database=FIRESTORE_DATABASE
    )


# ── Models ────────────────────────────────────────────────────────────────────

# Allowed keys in modified_parameters — matches execute_manual_action schema
_ALLOWED_MODIFIED_KEYS = frozenset({
    "action_provider", "action_name", "target_entities", "scope",
    "alert_group_identifiers", "is_predefined_scope", "parameters",
})


def _validate_modified_parameters(params: dict) -> dict:
    """Validate modified_parameters against known action schema.

    Rejects unknown keys to prevent prompt injection via analyst input.
    """
    unknown = set(params.keys()) - _ALLOWED_MODIFIED_KEYS
    if unknown:
        raise ValueError(
            f"Unknown keys in modified_parameters: {unknown}. "
            f"Allowed: {sorted(_ALLOWED_MODIFIED_KEYS)}"
        )
    return params


class ApprovalDecision(BaseModel):
    decision: str  # APPROVED | REJECTED | MODIFIED
    analyst_id: Optional[str] = Field(default=None, max_length=200)  # Ignored; decided_by comes from JWT
    analyst_notes: str = Field(default="", max_length=5000)
    modified_parameters: Optional[dict] = None  # Only for MODIFIED


class ApprovalResponse(BaseModel):
    approval_id: str
    client_id: str
    case_id: str
    agent_name: str
    session_id: Optional[str]
    status: str
    proposed_action: dict
    triage_summary: str
    analyst_instructions: str
    created_at: str
    updated_at: str
    decided_by: Optional[str]
    decided_at: Optional[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "project": PARTNER_PROJECT_ID}


@app.get("/approvals", response_model=list[ApprovalResponse])
async def list_approvals(
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    limit: int = 50,
    caller: dict = Depends(require_auth),
):
    """List approval requests, optionally filtered by status and client."""
    db = get_db()
    caller_email = caller.get("email", "")
    scope = get_caller_client_scope(db, caller_email)
    _enforce_scope(scope, client_id)

    q = db.collection(HITL_COLLECTION)

    if status:
        q = q.where("status", "==", status.upper())

    # If enforcement is on and no client_id provided, filter by all allowed clients
    if scope is not None and not client_id:
        # When scope is active, always filter. Use first allowed client if only one.
        if len(scope) == 1:
            q = q.where("client_id", "==", scope[0])
        # For multiple clients, we can't use IN with other .where filters easily,
        # so we'll filter in-memory after fetching
    elif client_id:
        q = q.where("client_id", "==", client_id)

    docs = q.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
    results = [doc.to_dict() for doc in docs]

    # In-memory filter for multi-client scopes
    if scope is not None and not client_id and len(scope) > 1:
        results = [r for r in results if r.get("client_id") in scope]

    return results


@app.get("/approvals/pending", response_model=list[ApprovalResponse])
async def list_pending_approvals(
    client_id: Optional[str] = None,
    caller: dict = Depends(require_auth),
):
    """List all PENDING approvals — primary analyst view."""
    return await list_approvals(status="PENDING", client_id=client_id, caller=caller)


@app.get("/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str, caller: dict = Depends(require_auth)):
    """Get a specific approval request."""
    db = get_db()
    caller_email = caller.get("email", "")
    scope = get_caller_client_scope(db, caller_email)

    doc = db.collection(HITL_COLLECTION).document(approval_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found")
    data = doc.to_dict()

    # Check doc's client_id is in caller's scope
    _enforce_scope(scope, data.get("client_id"))
    return data


def _check_client_authorization(db, caller_email: str, client_id: str):
    """Check if the analyst is authorized for this client.

    Reads from Firestore `analyst_assignments` collection.
    Only enforced when ENFORCE_CLIENT_AUTH is True.
    """
    if not ENFORCE_CLIENT_AUTH:
        return

    assignment_doc = (
        db.collection(ANALYST_ASSIGNMENTS_COLLECTION)
        .document(caller_email)
        .get()
    )
    if not assignment_doc.exists:
        raise HTTPException(
            status_code=403,
            detail=f"Analyst '{caller_email}' not authorized — no assignment record found",
        )

    allowed = assignment_doc.to_dict().get("allowed_clients", [])
    if client_id not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Analyst '{caller_email}' not authorized for client '{client_id}'",
        )


def get_caller_client_scope(db, caller_email: str) -> list[str] | None:
    """Return the list of client_ids the caller can access, or None (allow all).

    Returns None when ENFORCE_CLIENT_AUTH is False.
    Returns the allowed_clients list when enabled.
    Raises 403 if enforcement is on but no assignment exists.
    """
    if not ENFORCE_CLIENT_AUTH:
        return None

    assignment_doc = (
        db.collection(ANALYST_ASSIGNMENTS_COLLECTION)
        .document(caller_email)
        .get()
    )
    if not assignment_doc.exists:
        raise HTTPException(
            status_code=403,
            detail=f"Analyst '{caller_email}' not authorized — no assignment record found",
        )
    return assignment_doc.to_dict().get("allowed_clients", [])


def _enforce_scope(scope: list[str] | None, client_id: str | None, context: str = ""):
    """Check that client_id is within scope. Raises 403 if not."""
    if scope is None:
        return  # No enforcement
    if client_id and client_id not in scope:
        raise HTTPException(
            status_code=403,
            detail=f"Not authorized for client '{client_id}'",
        )


@app.post("/approvals/{approval_id}/decide")
async def decide_approval(
    approval_id: str,
    decision: ApprovalDecision,
    caller: dict = Depends(require_analyst_auth),
):
    """
    Approve, reject, or modify a pending agent action.

    Security:
    - decided_by is extracted from the caller's JWT email (body analyst_id is ignored)
    - Uses Firestore transaction for atomic read+update (prevents race conditions)
    - Per-client authorization when ENFORCE_CLIENT_AUTH=true

    Decision options:
    - APPROVED: Execute the action as proposed
    - REJECTED: Do not execute; agent will document the rejection
    - MODIFIED: Execute with analyst-provided modified_parameters
    """
    tracer = get_tracer("agentic_soc.hitl")
    with tracer.start_as_current_span("hitl.decide_approval") as span:
        span.set_attribute("approval.id", approval_id)
        span.set_attribute("decision.type", decision.decision)

        valid_decisions = {"APPROVED", "REJECTED", "MODIFIED"}
        if decision.decision.upper() not in valid_decisions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid decision. Must be one of: {valid_decisions}",
            )

        if decision.decision.upper() == "MODIFIED" and not decision.modified_parameters:
            raise HTTPException(
                status_code=400,
                detail="modified_parameters required when decision is MODIFIED",
            )

        if decision.modified_parameters:
            try:
                _validate_modified_parameters(decision.modified_parameters)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))

        # Extract analyst identity from JWT — never trust the body
        caller_email = caller.get("email", "unknown")

        db = get_db()
        doc_ref = db.collection(HITL_COLLECTION).document(approval_id)

        @firestore.transactional
        def _decide_in_transaction(transaction, doc_ref, update_data, caller_email_tx):
            doc = doc_ref.get(transaction=transaction)
            if not doc.exists:
                raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found")
            current = doc.to_dict()
            if current["status"] != "PENDING":
                raise HTTPException(
                    status_code=409,
                    detail=f"Approval already decided: status={current['status']}",
                )
            # Authorization check INSIDE transaction — prevents TOCTOU race
            _check_client_authorization(db, caller_email_tx, current.get("client_id", ""))
            transaction.update(doc_ref, update_data)
            return current

        now = datetime.now(timezone.utc).isoformat()
        update = {
            "status": decision.decision.upper(),
            "decided_by": caller_email,
            "decided_at": now,
            "updated_at": now,
            "analyst_instructions": decision.analyst_notes,
        }
        if decision.modified_parameters:
            update["modified_parameters"] = decision.modified_parameters

        transaction = db.transaction()
        current = _decide_in_transaction(transaction, doc_ref, update, caller_email)

        # Update stats counter atomically
        stats_ref = db.collection(HITL_COLLECTION).document("__stats__")
        stats_ref.update({
            "PENDING": firestore.Increment(-1),
            decision.decision.upper(): firestore.Increment(1),
        })

        span.set_attribute("approval.client_id", current.get("client_id", ""))
        span.set_attribute("approval.case_id", current.get("case_id", ""))

        logger.info(
            "Approval decision recorded",
            extra={
                "approval_id": approval_id,
                "decision": decision.decision.upper(),
                "analyst": caller_email,
                "case_id": current.get("case_id"),
                "client_id": current.get("client_id"),
            },
        )

        # Fire callback for approved/modified actions
        if APPROVAL_CALLBACK_URL and decision.decision.upper() in ("APPROVED", "MODIFIED"):
            try:
                # Cloud Run service-to-service auth: obtain identity token
                callback_headers = {"Content-Type": "application/json"}
                # OTel: propagate W3C traceparent for end-to-end tracing
                propagate.inject(callback_headers)
                try:
                    auth_req = google.auth.transport.requests.Request()
                    id_token = google.oauth2.id_token.fetch_id_token(
                        auth_req, APPROVAL_CALLBACK_URL
                    )
                    callback_headers["Authorization"] = f"Bearer {id_token}"
                except Exception as token_exc:
                    logger.warning(
                        "Could not obtain identity token for callback (local dev?)",
                        extra={"error": str(token_exc)},
                    )

                async with httpx.AsyncClient(timeout=10) as callback_client:
                    await callback_client.post(
                        APPROVAL_CALLBACK_URL,
                        json={
                            "approval_id": approval_id,
                            "decision": decision.decision.upper(),
                            "client_id": current.get("client_id"),
                            "case_id": current.get("case_id"),
                        },
                        headers=callback_headers,
                    )
                logger.info(
                    "Approval callback sent",
                    extra={"approval_id": approval_id, "url": APPROVAL_CALLBACK_URL},
                )
            except Exception as exc:
                logger.warning(
                    "Approval callback failed (non-fatal)",
                    extra={"error": str(exc), "approval_id": approval_id},
                )

        return {
            "approval_id": approval_id,
            "status": decision.decision.upper(),
            "message": "Decision recorded. Agent will be notified on next poll.",
        }


# ── Pipeline Stages (ICM Glass Box) ──────────────────────────────────────────

class StageResponse(BaseModel):
    stage_id: str
    session_id: str
    case_id: str
    client_id: str
    agent_name: str
    stage_name: str
    stage_order: int
    status: str
    input_summary: dict
    output_structured: Optional[dict]
    output_raw: str
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    error: Optional[str]


@app.get("/pipeline/session/{session_id}", response_model=list[StageResponse])
async def get_pipeline_by_session(
    session_id: str,
    caller: dict = Depends(require_auth),
):
    """Get all pipeline stages for a workflow session, ordered by stage."""
    db = get_db()
    caller_email = caller.get("email", "")
    scope = get_caller_client_scope(db, caller_email)

    docs = (
        db.collection(STAGES_COLLECTION)
        .where("session_id", "==", session_id)
        .order_by("stage_order")
        .stream()
    )
    stages = [doc.to_dict() for doc in docs]

    # Filter by scope
    if scope is not None:
        stages = [s for s in stages if s.get("client_id") in scope]

    return stages


@app.get("/pipeline/case/{case_id}", response_model=list[StageResponse])
async def get_pipeline_by_case(
    case_id: str,
    client_id: Optional[str] = None,
    caller: dict = Depends(require_auth),
):
    """Get the most recent pipeline stages for a case."""
    db = get_db()
    caller_email = caller.get("email", "")
    scope = get_caller_client_scope(db, caller_email)
    _enforce_scope(scope, client_id)

    q = db.collection(STAGES_COLLECTION).where("case_id", "==", case_id)
    if client_id:
        q = q.where("client_id", "==", client_id)
    docs = q.order_by("started_at", direction=firestore.Query.DESCENDING).limit(20).stream()

    stages = [doc.to_dict() for doc in docs]

    # Filter by scope
    if scope is not None:
        stages = [s for s in stages if s.get("client_id") in scope]

    if not stages:
        return []
    latest_session = stages[0]["session_id"]
    return sorted(
        [s for s in stages if s["session_id"] == latest_session],
        key=lambda s: s["stage_order"],
    )


@app.get("/pipeline/recent", response_model=list[StageResponse])
async def get_recent_pipelines(
    client_id: Optional[str] = None,
    limit: int = 50,
    caller: dict = Depends(require_auth),
):
    """Get recent pipeline stages across all cases."""
    db = get_db()
    caller_email = caller.get("email", "")
    scope = get_caller_client_scope(db, caller_email)
    _enforce_scope(scope, client_id)

    q = db.collection(STAGES_COLLECTION)
    if client_id:
        q = q.where("client_id", "==", client_id)
    docs = q.order_by("started_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
    results = [doc.to_dict() for doc in docs]

    # Filter by scope
    if scope is not None and not client_id:
        results = [r for r in results if r.get("client_id") in scope]

    return results


@app.get("/stats")
async def get_stats(client_id: Optional[str] = None, caller: dict = Depends(require_auth)):
    """Dashboard statistics using counter document for efficiency."""
    db = get_db()
    caller_email = caller.get("email", "")
    scope = get_caller_client_scope(db, caller_email)
    _enforce_scope(scope, client_id)

    stats_doc = db.collection(HITL_COLLECTION).document("__stats__").get()
    if stats_doc.exists:
        stats = stats_doc.to_dict()
    else:
        # Initialize from collection scan (one-time migration)
        stats = {"PENDING": 0, "APPROVED": 0, "REJECTED": 0, "MODIFIED": 0}
        for doc in db.collection(HITL_COLLECTION).stream():
            data = doc.to_dict()
            if scope is not None and data.get("client_id") not in scope:
                continue
            s = data.get("status", "UNKNOWN")
            if s in stats:
                stats[s] += 1
        db.collection(HITL_COLLECTION).document("__stats__").set(stats)

    return {"stats": stats, "client_id": client_id or "all"}
