"""Audit log service — immutable append-only Firestore collection."""
import logging
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any, Optional

logger = logging.getLogger(__name__)

AUDIT_COLLECTION = "audit_log"
AUDIT_TTL_DAYS = 90  # Documents auto-expire after 90 days


class AuditAction(StrEnum):
    CASE_APPROVED = "CASE_APPROVED"
    CASE_REJECTED = "CASE_REJECTED"
    CASE_MODIFIED = "CASE_MODIFIED"
    PIPELINE_TRIGGERED = "PIPELINE_TRIGGERED"
    CHAT_MESSAGE = "CHAT_MESSAGE"
    CLIENT_CREATED = "CLIENT_CREATED"
    CLIENT_UPDATED = "CLIENT_UPDATED"
    CLIENT_DISABLED = "CLIENT_DISABLED"
    ANALYST_UPDATED = "ANALYST_UPDATED"
    ANALYST_DELETED = "ANALYST_DELETED"
    CONFIG_CHANGED = "CONFIG_CHANGED"


class AuditLogger:
    def __init__(self, db):
        self._db = db

    def log(
        self,
        actor: str,
        actor_type: str,
        action: AuditAction,
        client_id: str,
        case_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        result: Optional[str] = None,
    ) -> None:
        try:
            doc = {
                "timestamp": datetime.now(timezone.utc),
                "actor": actor,
                "actor_type": actor_type,
                "action": str(action),
                "client_id": client_id,
                "case_id": case_id,
                "details": details or {},
                "result": result,
                "expires_at": datetime.now(timezone.utc) + timedelta(days=AUDIT_TTL_DAYS),
            }
            self._db.collection(AUDIT_COLLECTION).add(doc)
        except Exception:
            logger.exception("Failed to write audit log", extra={"action": str(action)})
