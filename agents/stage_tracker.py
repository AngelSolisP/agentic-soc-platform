"""
Stage Tracker — ICM Glass Box Observability

Records intermediate agent outputs as structured JSON in Firestore.
Each workflow run produces a pipeline of stages that analysts can
inspect in the HITL Dashboard to trace agent reasoning step by step.

ICM principle: "every intermediate output is a readable surface."
Instead of opaque logs, the analyst sees exactly what each agent received
and produced, making the system interpretable by default.

Collection: workflow_stages
"""

import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from observability.tracing import get_current_trace_id

logger = logging.getLogger(__name__)

# Stage order constants — pipeline sequence
STAGE_TRIAGE = 1
STAGE_ENRICHMENT = 2
STAGE_CASE_MANAGER = 3
STAGE_RESPONSE = 4

STAGE_NAMES = {
    STAGE_TRIAGE: "triage",
    STAGE_ENRICHMENT: "enrichment",
    STAGE_CASE_MANAGER: "case_manager",
    STAGE_RESPONSE: "response",
}

STAGE_ORDER_BY_KEY = {v: k for k, v in STAGE_NAMES.items()}


def classify_agent(author: str) -> Optional[str]:
    """Map an ADK agent name (e.g. 'triage_agent_client1') to a stage key."""
    if not author:
        return None
    author_lower = author.lower()
    if "triage" in author_lower:
        return "triage"
    if "enrichment" in author_lower:
        return "enrichment"
    if "case_manager" in author_lower:
        return "case_manager"
    if "response" in author_lower:
        return "response"
    return None


def try_extract_json(text: str) -> Optional[dict]:
    """Try to extract a JSON block from agent output text."""
    # Look for ```json ... ``` blocks first
    match = re.search(r"```json\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find a raw JSON object
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


class StageTracker:
    """
    Tracks agent pipeline stages in Firestore.

    Usage:
        tracker = StageTracker(project_id)
        tracker.record_pipeline(session_id, case_id, client_id, agent_outputs)

    Where agent_outputs is built by the orchestrator from the ADK event stream.
    """

    COLLECTION = "workflow_stages"
    TTL_DAYS = 30  # Documents auto-expire after 30 days

    def __init__(self, partner_project_id: str, database: str = "(default)"):
        self._project_id = partner_project_id
        self._database = database
        self._db = None

    def _get_db(self):
        """Lazy Firestore connection — fails gracefully in local dev."""
        if self._db is None:
            try:
                from google.cloud import firestore
                self._db = firestore.Client(
                    project=self._project_id, database=self._database
                )
            except Exception as e:
                logger.warning("Firestore unavailable for stage tracking: %s", e)
                return None
        return self._db

    def record_stage(
        self,
        session_id: str,
        case_id: str,
        client_id: str,
        agent_key: str,
        raw_output: str,
        started_at: float,
        completed_at: float,
        input_summary: Optional[dict] = None,
        error: Optional[str] = None,
        error_severity: Optional[str] = None,
    ) -> Optional[str]:
        """
        Record a single completed stage.

        Args:
            session_id: Orchestrator session ID (links stages together)
            case_id: Chronicle SOAR case ID
            client_id: Client tenant identifier
            agent_key: Stage key (triage, enrichment, case_manager, response)
            raw_output: Full text output from the agent
            started_at: Unix timestamp when agent started
            completed_at: Unix timestamp when agent finished
            input_summary: Optional dict summarizing what the agent received
            error: Optional error message if the stage failed
            error_severity: Optional severity level (LOW, MEDIUM, HIGH, CRITICAL)

        Returns:
            stage_id or None if write failed.
        """
        db = self._get_db()
        if db is None:
            return None

        stage_id = str(uuid.uuid4())
        stage_order = STAGE_ORDER_BY_KEY.get(agent_key, 99)

        # Try to extract structured JSON from the output
        parsed_output = try_extract_json(raw_output)

        duration = round(completed_at - started_at, 2)

        doc = {
            "stage_id": stage_id,
            "session_id": session_id,
            "case_id": case_id,
            "client_id": client_id,
            "agent_name": agent_key,
            "stage_name": STAGE_NAMES.get(stage_order, agent_key),
            "stage_order": stage_order,
            "status": "ERROR" if error else "COMPLETED",
            "input_summary": input_summary or {},
            "output_structured": parsed_output,
            "output_raw": raw_output[:10000],  # Cap at 10K chars
            "started_at": datetime.fromtimestamp(started_at, tz=timezone.utc).isoformat(),
            "completed_at": datetime.fromtimestamp(completed_at, tz=timezone.utc).isoformat(),
            "duration_seconds": duration,
            "error": error,
            "error_severity": error_severity,
            "trace_id": get_current_trace_id(),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=self.TTL_DAYS),
        }

        try:
            db.collection(self.COLLECTION).document(stage_id).set(doc)
            logger.info(
                "Stage recorded",
                extra={
                    "stage_id": stage_id,
                    "agent": agent_key,
                    "case_id": case_id,
                    "duration": duration,
                    "has_structured": parsed_output is not None,
                },
            )
            return stage_id
        except Exception as e:
            logger.error("Failed to write stage: %s", e)
            return None

    def record_stage_incremental(
        self,
        session_id: str,
        case_id: str,
        client_id: str,
        agent_key: str,
        agent_data: dict,
    ) -> Optional[str]:
        """Write/update a stage to Firestore as it progresses.

        Called during the event loop so the UI shows stages in real-time,
        even if the pipeline crashes before reaching record_pipeline().

        Uses a deterministic doc ID (session_id + agent_key) so repeated
        calls UPDATE the same document rather than creating duplicates.
        """
        db = self._get_db()
        if db is None:
            return None

        # Deterministic ID so we upsert, not duplicate
        doc_id = f"{session_id}_{agent_key}"
        stage_order = STAGE_ORDER_BY_KEY.get(agent_key, 99)
        started = agent_data.get("started", 0)
        ended = agent_data.get("ended", 0)
        combined_text = "\n".join(agent_data.get("texts", []))
        parsed_output = try_extract_json(combined_text) if combined_text else None
        duration = round(ended - started, 2) if started and ended else 0

        doc = {
            "stage_id": doc_id,
            "session_id": session_id,
            "case_id": case_id,
            "client_id": client_id,
            "agent_name": agent_key,
            "stage_name": STAGE_NAMES.get(stage_order, agent_key),
            "stage_order": stage_order,
            "status": "COMPLETED" if duration > 0 else "RUNNING",
            "output_structured": parsed_output,
            "output_raw": combined_text[:10000] if combined_text else "",
            "started_at": (
                datetime.fromtimestamp(started, tz=timezone.utc).isoformat()
                if started else None
            ),
            "completed_at": (
                datetime.fromtimestamp(ended, tz=timezone.utc).isoformat()
                if ended else None
            ),
            "duration_seconds": duration,
            "error": None,
            "error_severity": None,
            "trace_id": get_current_trace_id(),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=self.TTL_DAYS),
        }

        try:
            db.collection(self.COLLECTION).document(doc_id).set(doc, merge=True)
            print(
                f"[STAGE] Incremental write: {agent_key} status={doc['status']} "
                f"doc_id={doc_id} case_id={case_id}"
            )
            return doc_id
        except Exception as e:
            print(f"[STAGE] Incremental write FAILED: {agent_key} error={e}")
            logger.warning("Incremental stage write failed: %s", e)
            return None

    def record_pipeline(
        self,
        session_id: str,
        case_id: str,
        client_id: str,
        agent_outputs: dict,
        errors: Optional[dict] = None,
    ) -> list[str]:
        """
        Record all stages from a completed workflow.

        Args:
            agent_outputs: Dict of {agent_key: {"texts": [...], "started": float, "ended": float}}
            errors: Optional dict of {agent_key: {"error": str, "severity": str}}

        Returns:
            List of stage_ids written.
        """
        errors = errors or {}
        stage_ids = []
        print(
            f"[STAGE] record_pipeline called: session={session_id} case={case_id} "
            f"agent_keys={list(agent_outputs.keys())} error_keys={list(errors.keys())}"
        )
        for agent_key in ["triage", "enrichment", "case_manager", "response"]:
            data = agent_outputs.get(agent_key)
            if not data:
                continue

            combined_text = "\n".join(data.get("texts", []))
            if not combined_text.strip() and agent_key not in errors:
                continue

            error_info = errors.get(agent_key, {})
            stage_id = self.record_stage(
                session_id=session_id,
                case_id=case_id,
                client_id=client_id,
                agent_key=agent_key,
                raw_output=combined_text,
                started_at=data.get("started", 0),
                completed_at=data.get("ended", 0),
                error=error_info.get("error"),
                error_severity=error_info.get("severity"),
            )
            if stage_id:
                stage_ids.append(stage_id)

        return stage_ids

    def get_pipeline(self, session_id: str, client_id: Optional[str] = None) -> list[dict]:
        """Get all stages for a workflow session, ordered by stage_order.

        Args:
            session_id: The workflow session to query.
            client_id: If provided, filter stages by client_id (tenant isolation).
        """
        db = self._get_db()
        if db is None:
            return []
        q = db.collection(self.COLLECTION).where("session_id", "==", session_id)
        if client_id:
            q = q.where("client_id", "==", client_id)
        docs = q.order_by("stage_order").stream()
        return [doc.to_dict() for doc in docs]

    def get_case_pipeline(self, case_id: str, client_id: str) -> list[dict]:
        """Get the most recent pipeline for a case."""
        db = self._get_db()
        if db is None:
            return []
        docs = (
            db.collection(self.COLLECTION)
            .where("case_id", "==", case_id)
            .where("client_id", "==", client_id)
            .order_by("started_at", direction="DESCENDING")
            .limit(20)
            .stream()
        )
        stages = [doc.to_dict() for doc in docs]
        if not stages:
            return []
        # Return only the most recent session's stages
        latest_session = stages[0]["session_id"]
        return sorted(
            [s for s in stages if s["session_id"] == latest_session],
            key=lambda s: s["stage_order"],
        )
