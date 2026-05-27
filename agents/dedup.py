"""
Alert deduplication for the Agentic SOC orchestrator.

Uses Firestore collection `alert_dedup` for multi-instance safety.
Dedup key = hash(client_id + alert_type + case_id).
Fail-open: if Firestore is unavailable, alert is processed (not deduplicated).
"""

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from google.cloud import firestore

logger = logging.getLogger(__name__)

DEDUP_COLLECTION = "alert_dedup"


class AlertDeduplicator:
    """Firestore-backed alert deduplication with TTL-based expiry."""

    def __init__(self, partner_project_id: str, ttl_seconds: int = 900, database: str = "(default)"):
        self._ttl = ttl_seconds
        try:
            self._db = firestore.Client(project=partner_project_id, database=database)
        except Exception:
            logger.warning("Firestore unavailable for dedup — will fail-open")
            self._db = None

    @staticmethod
    def _make_key(client_id: str, alert_type: str, case_id: str) -> str:
        raw = f"{client_id}:{alert_type}:{case_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def is_duplicate(self, client_id: str, alert_type: str, case_id: str) -> bool:
        """Check if this alert was already processed recently. Fail-open on errors."""
        if self._db is None:
            return False
        try:
            key = self._make_key(client_id, alert_type, case_id)
            doc = self._db.collection(DEDUP_COLLECTION).document(key).get()
            if not doc.exists:
                return False
            data = doc.to_dict()
            raw_expires = data.get("expires_at")
            if isinstance(raw_expires, datetime):
                expires_at = raw_expires
            else:
                expires_at = datetime.fromisoformat(str(raw_expires or "2000-01-01T00:00:00+00:00"))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                return False
            logger.info("Duplicate alert detected", extra={
                "client_id": client_id, "alert_type": alert_type, "case_id": case_id,
            })
            return True
        except Exception:
            logger.warning("Dedup check failed — fail-open", exc_info=True)
            return False

    def record(self, client_id: str, alert_type: str, case_id: str, result: Optional[dict] = None) -> None:
        """Record that this alert has been processed."""
        if self._db is None:
            return
        try:
            key = self._make_key(client_id, alert_type, case_id)
            now = datetime.now(timezone.utc)
            self._db.collection(DEDUP_COLLECTION).document(key).set({
                "client_id": client_id,
                "alert_type": alert_type,
                "case_id": case_id,
                "result": result,
                "created_at": now,
                "expires_at": now + timedelta(seconds=self._ttl),
            })
        except Exception:
            logger.warning("Dedup record failed — non-fatal", exc_info=True)

    def get_previous_result(self, client_id: str, alert_type: str, case_id: str) -> Optional[dict]:
        if self._db is None:
            return None
        try:
            key = self._make_key(client_id, alert_type, case_id)
            doc = self._db.collection(DEDUP_COLLECTION).document(key).get()
            if not doc.exists:
                return None
            data = doc.to_dict()
            raw_expires = data.get("expires_at")
            if isinstance(raw_expires, datetime):
                expires_at = raw_expires
            else:
                expires_at = datetime.fromisoformat(str(raw_expires or "2000-01-01T00:00:00+00:00"))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                return None
            return data.get("result")
        except Exception:
            return None
