"""Case list, detail, and action endpoints — reads from Chronicle SOAR via MCP Gateway."""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from google.cloud.firestore_v1 import transactional
from pydantic import BaseModel

from workbench.backend.audit import AuditAction
from workbench.backend.auth import get_current_analyst
from workbench.backend.mcp_client import MCPClient, MCPToolError
from workbench.backend.security import validate_client_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cases"])

STAGES_COLLECTION = "workflow_stages"
HITL_COLLECTION = "hitl_approvals"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_case(case: dict) -> dict:
    """Normalize Chronicle SOAR case fields to frontend-expected format.

    Chronicle returns:
      - name: "projects/.../cases/12345" (resource name)
      - displayName: "phishing_alert_from_user" (human-readable)
      - priority: "PRIORITY_CRITICAL" (prefixed)
    Frontend expects:
      - id: "12345" (numeric case ID)
      - name: "phishing_alert_from_user" (display name)
    """
    resource_name = case.get("name", "")
    # Extract numeric case ID from resource name
    if "/cases/" in resource_name:
        case["id"] = resource_name.rsplit("/cases/", 1)[-1]
    elif not case.get("id"):
        case["id"] = resource_name

    # Use displayName as the human-readable name
    if case.get("displayName"):
        case["resource_name"] = resource_name
        case["name"] = case["displayName"]

    return case


def _get_mcp_client(request: Request) -> MCPClient:
    # Return shared instance (preserves session cache across requests)
    if hasattr(request.app.state, "mcp_client") and request.app.state.mcp_client:
        return request.app.state.mcp_client
    client = MCPClient(
        gateway_url=request.app.state.mcp_gateway_url,
        http_client=request.app.state.http_client,
    )
    request.app.state.mcp_client = client
    return client


def _get_db(request: Request):
    return request.app.state.db


def _get_audit(request: Request):
    return request.app.state.audit


def _filter_by_scope(analyst: dict, client_id: Optional[str], db=None) -> list[str]:
    """Return the list of client IDs this analyst may query.

    Admin with no client_id → all registered clients (queried from Firestore).
    Admin with client_id   → only that client.
    Analyst with client_id → that client if in allowed_clients.
    Analyst with no client_id → all allowed_clients.
    """
    allowed = analyst.get("allowed_clients", [])
    if analyst.get("role") == "admin":
        if client_id:
            return [client_id]
        # Admin with no filter — fetch all clients from Firestore
        if db is not None:
            try:
                docs = db.collection("clients").stream()
                all_clients = [d.id for d in docs]
                if all_clients:
                    return all_clients
            except Exception:
                pass
        return allowed  # fallback to allowed_clients (may be empty)
    if client_id:
        if client_id not in allowed:
            raise HTTPException(403, "Not authorized for this client")
        return [client_id]
    return allowed


# ---------------------------------------------------------------------------
# Firestore helpers
# ---------------------------------------------------------------------------

def _load_pipeline_summaries(db, case_ids: list[str]) -> dict:
    """Load terse pipeline summaries keyed by case_id (for list view)."""
    if not case_ids:
        return {}
    result: dict = {}
    for case_id in case_ids[:50]:
        try:
            stages = (
                db.collection(STAGES_COLLECTION)
                .where("case_id", "==", case_id)
                .order_by("stage_order")
                .stream()
            )
            stage_list = [s.to_dict() for s in stages]
            if stage_list:
                result[case_id] = {
                    "stages_completed": len(
                        [s for s in stage_list if s.get("status") == "COMPLETED"]
                    ),
                    "total_stages": len(stage_list),
                    "latest_stage": stage_list[-1].get("stage_name"),
                    "verdict": _extract_verdict(stage_list),
                }
        except Exception as e:
            logger.warning("Failed to load pipeline for case %s: %s", case_id, e)
    return result


def _load_pipeline_stages(db, case_id: str, client_id: str) -> list[dict]:
    """Load full pipeline stage list for a single case."""
    try:
        stages = (
            db.collection(STAGES_COLLECTION)
            .where("case_id", "==", case_id)
            .where("client_id", "==", client_id)
            .order_by("stage_order")
            .stream()
        )
        return [s.to_dict() for s in stages]
    except Exception as e:
        logger.warning("Failed to load pipeline stages for case %s: %s", case_id, e)
        return []


def _load_approvals(db, case_id: str, client_id: str) -> list[dict]:
    """Load HITL approvals for a single case."""
    approvals = (
        db.collection(HITL_COLLECTION)
        .where("case_id", "==", case_id)
        .where("client_id", "==", client_id)
        .stream()
    )
    return [a.to_dict() for a in approvals]


def _extract_verdict(stages: list[dict]) -> Optional[str]:
    for stage in stages:
        if stage.get("stage_name") == "triage":
            output = stage.get("output_structured", {})
            if isinstance(output, dict):
                return output.get("verdict")
    return None


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ApprovalRequest(BaseModel):
    approval_id: str
    analyst_notes: str = ""
    modified_parameters: Optional[dict] = None


class TriggerRequest(BaseModel):
    client_id: str
    alert_type: str = "GENERIC"
    severity: str = "MEDIUM"
    raw_alert: Optional[dict] = None


# ---------------------------------------------------------------------------
# Case list endpoint
# ---------------------------------------------------------------------------

@router.get("/cases")
async def list_cases(
    request: Request,
    client_id: Optional[str] = Query(None),
    status: str = Query("OPENED"),
    analyst: dict = Depends(get_current_analyst),
):
    mcp = _get_mcp_client(request)
    db = _get_db(request)
    clients_to_query = _filter_by_scope(analyst, client_id, db)

    if not clients_to_query:
        return {"cases": [], "total": 0}

    all_cases: list[dict] = []
    for cid in clients_to_query:
        try:
            filter_str = f"Status='{status}'" if status else ""
            result = await mcp.call_tool(cid, "list_cases", {"filter": filter_str})
            cases = result.get("cases", [])
            # If the MCP client returned raw text, treat as empty
            if isinstance(result, dict) and "text" in result and "cases" not in result:
                cases = []
            for case in cases:
                _normalize_case(case)
                case["client_id"] = cid
            all_cases.extend(cases)
        except MCPToolError as e:
            logger.warning("Failed to list cases for %s: %s", cid, e)
        except Exception as e:
            logger.warning("Error listing cases for %s: %s", cid, e)

    case_ids = [c.get("id") for c in all_cases if c.get("id")]
    pipeline_map = _load_pipeline_summaries(db, case_ids)

    for case in all_cases:
        case["pipeline"] = pipeline_map.get(case.get("id"))

    return {"cases": all_cases, "total": len(all_cases)}


# ---------------------------------------------------------------------------
# Case detail endpoint
# ---------------------------------------------------------------------------

@router.get("/cases/{case_id}")
async def get_case_detail(
    case_id: str,
    request: Request,
    client_id: str = Query(..., description="Client ID (required for routing)"),
    analyst: dict = Depends(get_current_analyst),
):
    allowed = analyst.get("allowed_clients", [])
    if analyst.get("role") != "admin" and client_id not in allowed:
        raise HTTPException(403, "Not authorized for this client")

    validate_client_id(client_id)
    mcp = _get_mcp_client(request)
    db = _get_db(request)

    try:
        case_data = await mcp.call_tool(client_id, "get_case", {"caseId": case_id})
        _normalize_case(case_data)
    except MCPToolError as e:
        logger.warning("MCP error loading case", extra={"case_id": case_id, "error": str(e)})
        raise HTTPException(404, "Case not found")

    try:
        alerts_data = await mcp.call_tool(
            client_id, "list_case_alerts", {"caseId": case_id}
        )
        # Chronicle uses "caseAlerts" not "alerts"
        alerts = alerts_data.get("caseAlerts", alerts_data.get("alerts", []))
        if isinstance(alerts_data, dict) and "text" in alerts_data and "caseAlerts" not in alerts_data and "alerts" not in alerts_data:
            alerts = []
    except MCPToolError:
        alerts = []

    stages = _load_pipeline_stages(db, case_id, client_id)
    approvals = _load_approvals(db, case_id, client_id)

    return {
        "case": case_data,
        "alerts": alerts,
        "pipeline_stages": stages,
        "approvals": approvals,
        "client_id": client_id,
    }


# ---------------------------------------------------------------------------
# Action endpoints
# ---------------------------------------------------------------------------

@router.post("/cases/{case_id}/approve")
async def approve_case(
    case_id: str,
    body: ApprovalRequest,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
):
    return await _decide(request, case_id, body, "APPROVED", analyst)


@router.post("/cases/{case_id}/reject")
async def reject_case(
    case_id: str,
    body: ApprovalRequest,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
):
    return await _decide(request, case_id, body, "REJECTED", analyst)


@router.post("/cases/{case_id}/trigger")
async def trigger_pipeline(
    case_id: str,
    body: TriggerRequest,
    request: Request,
    analyst: dict = Depends(get_current_analyst),
):
    validate_client_id(body.client_id)
    allowed = analyst.get("allowed_clients", [])
    if analyst.get("role") != "admin" and body.client_id not in allowed:
        raise HTTPException(403, "Not authorized for this client")

    # Fire-and-forget: run pipeline as background task to avoid blocking the
    # event loop (which kills liveness probes on Cloud Run).
    tasks = request.app.state.tasks
    tasks.create_task(
        _trigger_pipeline(
            client_id=body.client_id,
            case_id=case_id,
            alert_type=body.alert_type,
            severity=body.severity,
            raw_alert=body.raw_alert,
        ),
        name=f"pipeline-{body.client_id}-{case_id}",
    )

    audit = _get_audit(request)
    audit.log(
        actor=analyst["email"],
        actor_type=analyst.get("role", "analyst"),
        action=AuditAction.PIPELINE_TRIGGERED,
        client_id=body.client_id,
        case_id=case_id,
        details={"alert_type": body.alert_type, "severity": body.severity},
    )

    return {"status": "ACCEPTED", "case_id": case_id, "message": "Pipeline started"}


# ---------------------------------------------------------------------------
# Internal decision helper
# ---------------------------------------------------------------------------

async def _decide(
    request: Request,
    case_id: str,
    body: ApprovalRequest,
    decision: str,
    analyst: dict,
) -> dict:
    db = _get_db(request)
    doc_ref = db.collection(HITL_COLLECTION).document(body.approval_id)

    # OWASP A01: Use Firestore transaction to prevent TOCTOU race condition
    # (two analysts approving simultaneously). Same pattern as HITL dashboard (Phase 7.5 C1).
    transaction = db.transaction()

    @transactional
    def decide_in_transaction(txn, ref):
        doc = ref.get(transaction=txn)

        if not doc.exists:
            raise HTTPException(404, "Approval not found")

        data = doc.to_dict()

        if data.get("case_id") != case_id:
            raise HTTPException(400, "Approval does not belong to this case")

        # Auth check INSIDE transaction (prevents TOCTOU — Phase 7.5 C1)
        approval_client = data.get("client_id", "")
        allowed = analyst.get("allowed_clients", [])
        if analyst.get("role") != "admin" and approval_client not in allowed:
            raise HTTPException(403, "Not authorized for this client")

        if data.get("status") != "PENDING":
            raise HTTPException(409, f"Approval already decided: {data.get('status')}")

        update_data: dict = {
            "status": decision,
            "decided_by": analyst["email"],
            "decided_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "analyst_notes": body.analyst_notes,
        }
        if decision == "MODIFIED" and body.modified_parameters:
            update_data["modified_parameters"] = body.modified_parameters

        txn.update(ref, update_data)
        return approval_client

    approval_client = decide_in_transaction(transaction, doc_ref)

    audit = _get_audit(request)
    audit_action = (
        AuditAction.CASE_APPROVED if decision == "APPROVED" else AuditAction.CASE_REJECTED
    )
    audit.log(
        actor=analyst["email"],
        actor_type=analyst.get("role", "analyst"),
        action=audit_action,
        client_id=approval_client,
        case_id=case_id,
        details={"approval_id": body.approval_id, "notes": body.analyst_notes},
    )

    return {"status": decision, "approval_id": body.approval_id}


# ---------------------------------------------------------------------------
# Pipeline trigger helper
# ---------------------------------------------------------------------------

async def _trigger_pipeline(
    client_id: str,
    case_id: str,
    alert_type: str,
    severity: str,
    raw_alert: Optional[dict] = None,
) -> dict:
    try:
        # Load per-client config from Firestore (gti_enabled, autonomous_mode)
        gti_enabled = False
        try:
            from google.cloud import firestore as _fs
            _db = _fs.Client(
                project=os.environ.get("PARTNER_PROJECT_ID", ""),
                database=os.environ.get("FIRESTORE_DATABASE", "(default)"),
            )
            client_doc = _db.collection("clients").document(client_id).get()
            if client_doc.exists:
                client_cfg = client_doc.to_dict()
                gti_enabled = client_cfg.get("gti_enabled", False)
        except Exception:
            logger.warning("Failed to load client config for %s — defaulting gti_enabled=False", client_id)

        # Write initial "running" stage so the UI shows progress immediately
        _write_running_stage(client_id, case_id)

        agent_engine_id = os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")

        if agent_engine_id:
            import vertexai  # type: ignore
            from vertexai import agent_engines  # type: ignore

            project = os.environ.get("PARTNER_PROJECT_ID", "")
            region = os.environ.get("PARTNER_REGION", "us-central1")
            vertexai.init(project=project, location=region)

            engine = agent_engines.get(agent_engine_id)
            result = engine.query(
                client_id=client_id,
                case_id=case_id,
                alert_type=alert_type,
                severity=severity,
                trigger="manual_workbench",
                raw_alert=raw_alert or {},
                gti_enabled=gti_enabled,
            )
            return result

        from agents.orchestrator.agent import AgenticSOCOrchestrator  # type: ignore

        orchestrator = AgenticSOCOrchestrator(
            partner_project_id=os.environ.get("PARTNER_PROJECT_ID", ""),
            gateway_url=os.environ.get("MCP_GATEWAY_URL", "http://localhost:8080"),
        )
        result = await orchestrator.process_alert(
            client_id=client_id,
            case_id=case_id,
            alert_type=alert_type,
            severity=severity,
            raw_alert=raw_alert,
            trigger="manual_workbench",
            gti_enabled=gti_enabled,
        )
        return result

    except Exception as e:
        logger.exception("Pipeline failed for case %s", case_id)
        # Write error stage to Firestore so the UI can display it
        _write_error_stage(client_id, case_id, str(e))
        raise


def _write_running_stage(client_id: str, case_id: str) -> None:
    """Write an initial 'RUNNING' stage so the frontend shows progress immediately."""
    try:
        import uuid
        from google.cloud import firestore as fs
        from datetime import timedelta

        db = fs.Client(
            project=os.environ.get("PARTNER_PROJECT_ID", ""),
            database=os.environ.get("FIRESTORE_DATABASE", "(default)"),
        )
        stage_id = str(uuid.uuid4())
        db.collection(STAGES_COLLECTION).document(stage_id).set({
            "stage_id": stage_id,
            "session_id": f"pipeline-{case_id}",
            "case_id": case_id,
            "client_id": client_id,
            "agent_name": "orchestrator",
            "stage_name": "pipeline_started",
            "stage_order": 0,
            "status": "RUNNING",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "duration_seconds": 0,
            "output_structured": None,
            "output_raw": "Pipeline started — agents are analyzing the case...",
            "error": None,
            "error_severity": None,
            "trace_id": "",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        })
    except Exception:
        logger.warning("Failed to write running stage — non-fatal")


def _write_error_stage(client_id: str, case_id: str, error_msg: str) -> None:
    """Write a pipeline error to Firestore so the frontend can display it."""
    try:
        import uuid
        from google.cloud import firestore as fs

        db = fs.Client(
            project=os.environ.get("PARTNER_PROJECT_ID", ""),
            database=os.environ.get("FIRESTORE_DATABASE", "(default)"),
        )
        from datetime import timedelta
        stage_id = str(uuid.uuid4())
        db.collection(STAGES_COLLECTION).document(stage_id).set({
            "stage_id": stage_id,
            "session_id": f"error-{case_id}",
            "case_id": case_id,
            "client_id": client_id,
            "agent_name": "pipeline",
            "stage_name": "pipeline_error",
            "stage_order": 0,
            "status": "ERROR",
            "error": error_msg[:2000],
            "error_severity": "CRITICAL",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": 0,
            "output_structured": None,
            "output_raw": f"Pipeline failed: {error_msg[:2000]}",
            "trace_id": "",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        })
    except Exception:
        logger.exception("Failed to write error stage to Firestore")


# ---------------------------------------------------------------------------
# Pub/Sub push receiver — processes new cases from poller
# ---------------------------------------------------------------------------

@router.post("/trigger")
async def pubsub_trigger(request: Request):
    """Pub/Sub push receiver — processes new cases from poller."""
    import base64
    import json
    from workbench.backend.security import verify_pubsub_token, validate_client_id

    # OWASP A01: Verify Pub/Sub OIDC token before processing
    if not await verify_pubsub_token(request):
        raise HTTPException(403, "Invalid or missing Pub/Sub authentication")

    body = await request.json()

    # Pub/Sub push message format
    message = body.get("message", {})
    data_b64 = message.get("data", "")
    try:
        data = json.loads(base64.b64decode(data_b64))
    except Exception:
        raise HTTPException(400, "Invalid Pub/Sub message")

    client_id = data.get("client_id")
    case_id = data.get("case_id")
    alert_type = data.get("alert_type", "GENERIC")

    if not client_id or not case_id:
        raise HTTPException(400, "Missing client_id or case_id")

    # OWASP A03: Validate client_id format
    validate_client_id(client_id)

    # Dedup check
    from agents.dedup import AlertDeduplicator  # type: ignore

    dedup = AlertDeduplicator(
        partner_project_id=os.environ.get("PARTNER_PROJECT_ID", "")
    )
    if dedup.is_duplicate(client_id, alert_type, case_id):
        return {"status": "DUPLICATE", "case_id": case_id}

    # Start pipeline
    result = await _trigger_pipeline(
        client_id=client_id,
        case_id=case_id,
        alert_type=alert_type,
        severity="MEDIUM",
    )

    # Record for dedup
    dedup.record(client_id, alert_type, case_id, result={"status": result.get("status", "")})

    # Notify connected analysts
    from workbench.backend.ws import notification_hub

    await notification_hub.broadcast({
        "type": "new_case",
        "client_id": client_id,
        "case_id": case_id,
        "alert_type": alert_type,
    })

    return {"status": "PROCESSED", "case_id": case_id}
