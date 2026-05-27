"""
Client routing: maps client_id → Chronicle MCP endpoint + project metadata.

Client configs are loaded from Firestore (primary) with a local YAML fallback
for development. Configs are cached in memory with a 5-minute TTL to avoid
Firestore reads on every request.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import yaml
from google.cloud import firestore

logger = logging.getLogger(__name__)

# Cache TTL in seconds
_CACHE_TTL = 300
_client_config_cache: dict[str, tuple["ClientConfig", float]] = {}


@dataclass
class NotificationConfig:
    """Per-client notification channels."""
    slack_webhook: str = ""
    escalation_email: str = ""
    pagerduty_key: str = ""


@dataclass
class ClientConfig:
    client_id: str
    display_name: str
    gcp_project_id: str          # Client's GCP project
    chronicle_customer_id: str   # Chronicle tenant UUID
    chronicle_region: str        # us | eu | asia
    service_account_email: str   # SA to impersonate for this client
    enabled: bool = True
    autonomous_mode: bool = False  # If False, all actions require HITL approval
    gti_enabled: bool = False      # If True, GTI enrichment tools are available
    soar_environment_id: str = ""  # SOAR Environment ID for multi-tenant SOAR isolation
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    extra: dict = field(default_factory=dict)

    @property
    def mcp_endpoint(self) -> str:
        """Remote Managed MCP Server URL for this client's Chronicle instance."""
        return (
            f"https://chronicle.{self.chronicle_region}.rep.googleapis.com/mcp"
            f"?customer_id={self.chronicle_customer_id}"
        )


class ClientRouter:
    """Resolves client_id to ClientConfig, with Firestore backing + memory cache."""

    def __init__(
        self,
        partner_project_id: str,
        firestore_database: str = "(default)",
        local_config_path: Optional[str] = None,
    ):
        self._partner_project_id = partner_project_id
        self._local_config_path = local_config_path
        try:
            self._db = firestore.Client(
                project=partner_project_id, database=firestore_database
            )
            self._firestore_available = True
        except Exception as exc:
            logger.warning(
                "Firestore unavailable, falling back to local config",
                extra={"error": str(exc)},
            )
            self._db = None
            self._firestore_available = False

    def get_client(self, client_id: str) -> ClientConfig:
        """Return ClientConfig for the given client_id. Raises KeyError if not found."""
        now = time.time()

        # Check memory cache
        if client_id in _client_config_cache:
            config, cached_at = _client_config_cache[client_id]
            if now - cached_at < _CACHE_TTL:
                return config

        config = self._load_client(client_id)
        _client_config_cache[client_id] = (config, now)
        return config

    def _load_client(self, client_id: str) -> ClientConfig:
        if self._firestore_available:
            return self._load_from_firestore(client_id)
        return self._load_from_local(client_id)

    def _load_from_firestore(self, client_id: str) -> ClientConfig:
        doc_ref = self._db.collection("clients").document(client_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise KeyError(f"Client '{client_id}' not found in Firestore")
        data = doc.to_dict()
        notif_data = data.get("notifications", {})
        return ClientConfig(
            client_id=client_id,
            display_name=data["display_name"],
            gcp_project_id=data["gcp_project_id"],
            chronicle_customer_id=data["chronicle_customer_id"],
            chronicle_region=data.get("chronicle_region", "us"),
            service_account_email=data["service_account_email"],
            enabled=data.get("enabled", True),
            autonomous_mode=data.get("autonomous_mode", False),
            gti_enabled=data.get("gti_enabled", False),
            soar_environment_id=data.get("soar_environment_id", ""),
            notifications=NotificationConfig(
                slack_webhook=notif_data.get("slack_webhook", ""),
                escalation_email=notif_data.get("escalation_email", ""),
                pagerduty_key=notif_data.get("pagerduty_key", ""),
            ),
            extra=data.get("extra", {}),
        )

    def _load_from_local(self, client_id: str) -> ClientConfig:
        if not self._local_config_path:
            raise KeyError(
                f"Client '{client_id}' not found: Firestore unavailable and no local config path"
            )
        with open(self._local_config_path) as f:
            all_clients = yaml.safe_load(f) or {}
        if client_id not in all_clients:
            raise KeyError(f"Client '{client_id}' not found in local config")
        data = all_clients[client_id]
        notif_data = data.get("notifications", {})
        return ClientConfig(
            client_id=client_id,
            display_name=data["display_name"],
            gcp_project_id=data["gcp_project_id"],
            chronicle_customer_id=data["chronicle_customer_id"],
            chronicle_region=data.get("chronicle_region", "us"),
            service_account_email=data["service_account_email"],
            enabled=data.get("enabled", True),
            autonomous_mode=data.get("autonomous_mode", False),
            gti_enabled=data.get("gti_enabled", False),
            soar_environment_id=data.get("soar_environment_id", ""),
            notifications=NotificationConfig(
                slack_webhook=notif_data.get("slack_webhook", ""),
                escalation_email=notif_data.get("escalation_email", ""),
                pagerduty_key=notif_data.get("pagerduty_key", ""),
            ),
            extra=data.get("extra", {}),
        )

    def invalidate_cache(self, client_id: Optional[str] = None) -> None:
        """Invalidate the cache for a specific client or all clients."""
        if client_id:
            _client_config_cache.pop(client_id, None)
        else:
            _client_config_cache.clear()
        logger.info("Cache invalidated", extra={"client_id": client_id or "ALL"})
