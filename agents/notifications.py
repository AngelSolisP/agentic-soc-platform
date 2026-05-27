"""
Notification Service — Slack, PagerDuty, and email alerts for SOC events.

Sends notifications at key workflow trigger points:
1. HITL submission (new approval request)
2. HITL timeout (approval expired)
3. Case escalation (T2 escalation by Case Manager)
4. Agent timeout (pipeline exceeded timeout)

All notification calls are async and best-effort (failures are logged, not raised).
"""

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Shared async client — reuse across notifications
_http_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=10)
    return _http_client


@dataclass
class NotificationEvent:
    """Structured notification payload."""
    event_type: str  # hitl_submission | hitl_timeout | escalation | agent_timeout
    client_id: str
    case_id: str
    severity: str  # INFORMATIVE | LOW | MEDIUM | HIGH | CRITICAL
    summary: str
    details: dict


class NotificationService:
    """
    Sends notifications to configured channels for a client.

    Channels are configured per-client in ClientConfig.notifications.
    Missing/empty channels are silently skipped.
    """

    def __init__(
        self,
        slack_webhook: str = "",
        escalation_email: str = "",
        pagerduty_key: str = "",
    ):
        self._slack_webhook = slack_webhook
        self._escalation_email = escalation_email
        self._pagerduty_key = pagerduty_key

    @classmethod
    def from_notification_config(cls, config) -> "NotificationService":
        """Create from a NotificationConfig dataclass."""
        return cls(
            slack_webhook=config.slack_webhook,
            escalation_email=config.escalation_email,
            pagerduty_key=config.pagerduty_key,
        )

    async def notify(self, event: NotificationEvent) -> None:
        """Send notification to all configured channels (best-effort)."""
        if self._slack_webhook:
            await self._send_slack(event)
        if self._pagerduty_key and event.severity in ("HIGH", "CRITICAL"):
            await self._send_pagerduty(event)
        # Email notifications would require a mail service (SendGrid, SES, etc.)
        # For now, log the escalation email target for pickup by external systems
        if self._escalation_email and event.severity in ("HIGH", "CRITICAL"):
            logger.info(
                "Email notification target",
                extra={
                    "escalation_email": self._escalation_email,
                    "event_type": event.event_type,
                    "case_id": event.case_id,
                    "client_id": event.client_id,
                },
            )

    async def _send_slack(self, event: NotificationEvent) -> None:
        """Post a formatted message to Slack via incoming webhook."""
        severity_emoji = {
            "CRITICAL": ":rotating_light:",
            "HIGH": ":warning:",
            "MEDIUM": ":large_blue_circle:",
            "LOW": ":white_circle:",
            "INFORMATIVE": ":information_source:",
        }
        emoji = severity_emoji.get(event.severity, ":bell:")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {event.event_type.upper().replace('_', ' ')}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Client:* `{event.client_id}`"},
                    {"type": "mrkdwn", "text": f"*Case:* `{event.case_id}`"},
                    {"type": "mrkdwn", "text": f"*Severity:* {event.severity}"},
                    {"type": "mrkdwn", "text": f"*Summary:* {event.summary}"},
                ],
            },
        ]

        try:
            client = _get_client()
            resp = await client.post(
                self._slack_webhook,
                json={"blocks": blocks, "text": f"{event.event_type}: {event.summary}"},
            )
            if resp.status_code != 200:
                logger.warning(
                    "Slack notification failed",
                    extra={"status": resp.status_code, "case_id": event.case_id},
                )
        except Exception as e:
            logger.warning("Slack notification error: %s", e)

    async def _send_pagerduty(self, event: NotificationEvent) -> None:
        """Create a PagerDuty incident via Events API v2."""
        pd_severity = "critical" if event.severity == "CRITICAL" else "error"

        payload = {
            "routing_key": self._pagerduty_key,
            "event_action": "trigger",
            "payload": {
                "summary": f"[{event.client_id}] {event.event_type}: {event.summary}",
                "severity": pd_severity,
                "source": "agentic-soc",
                "component": event.event_type,
                "custom_details": {
                    "case_id": event.case_id,
                    "client_id": event.client_id,
                    **event.details,
                },
            },
        }

        try:
            client = _get_client()
            resp = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
            )
            if resp.status_code not in (200, 202):
                logger.warning(
                    "PagerDuty notification failed",
                    extra={"status": resp.status_code, "case_id": event.case_id},
                )
        except Exception as e:
            logger.warning("PagerDuty notification error: %s", e)


# Convenience functions for the 4 trigger points

async def notify_hitl_submission(
    service: NotificationService,
    client_id: str,
    case_id: str,
    proposed_action: str,
    approval_id: str,
) -> None:
    """Trigger 1: New HITL approval request submitted."""
    await service.notify(NotificationEvent(
        event_type="hitl_submission",
        client_id=client_id,
        case_id=case_id,
        severity="HIGH",
        summary=f"Action '{proposed_action}' requires analyst approval",
        details={"approval_id": approval_id, "proposed_action": proposed_action},
    ))


async def notify_hitl_timeout(
    service: NotificationService,
    client_id: str,
    case_id: str,
    approval_id: str,
) -> None:
    """Trigger 2: HITL approval expired without analyst decision."""
    await service.notify(NotificationEvent(
        event_type="hitl_timeout",
        client_id=client_id,
        case_id=case_id,
        severity="CRITICAL",
        summary=f"Approval {approval_id} expired — manual review required",
        details={"approval_id": approval_id},
    ))


async def notify_escalation(
    service: NotificationService,
    client_id: str,
    case_id: str,
    reason: str,
    priority: str = "HIGH",
) -> None:
    """Trigger 3: Case escalated to T2 by Case Manager."""
    await service.notify(NotificationEvent(
        event_type="escalation",
        client_id=client_id,
        case_id=case_id,
        severity=priority,
        summary=f"Case escalated to T2: {reason}",
        details={"reason": reason},
    ))


async def notify_agent_timeout(
    service: NotificationService,
    client_id: str,
    case_id: str,
    last_agent: str,
    timeout_seconds: int,
) -> None:
    """Trigger 4: Agent pipeline exceeded timeout."""
    await service.notify(NotificationEvent(
        event_type="agent_timeout",
        client_id=client_id,
        case_id=case_id,
        severity="HIGH",
        summary=f"Pipeline timeout after {timeout_seconds}s (last agent: {last_agent})",
        details={"last_agent": last_agent, "timeout_seconds": timeout_seconds},
    ))
