"""
Tenant-aware A2A executor for the Agentic SOC orchestrator.

Extracts client_id from A2A message metadata, validates the tenant,
calls orchestrator.process_alert(), and publishes A2A task lifecycle events.
"""

import json
import logging
from datetime import datetime, timezone

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Artifact,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

from agents.validation import validate_client_id

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _text_part(text: str) -> Part:
    return Part(root=TextPart(text=text))


def _agent_message(text: str) -> Message:
    return Message(
        messageId="",
        role=Role.agent,
        parts=[_text_part(text)],
    )


class TenantAwareA2aExecutor(AgentExecutor):
    """A2A executor that routes requests to per-tenant orchestrator pipelines.

    Extracts client_id from A2A message/request metadata, validates the tenant,
    runs the full SOC pipeline via orchestrator.process_alert(), and publishes
    standard A2A task lifecycle events (submitted → working → completed/failed).
    """

    def __init__(self, orchestrator):
        """Initialize with a shared AgenticSOCOrchestrator instance.

        Args:
            orchestrator: AgenticSOCOrchestrator (agents cached per client internally).
        """
        super().__init__()
        self._orchestrator = orchestrator

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task_id = context.task_id or ""
        context_id = context.context_id

        # Publish submitted event
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                taskId=task_id,
                status=TaskStatus(state=TaskState.submitted, timestamp=_now_iso()),
                contextId=context_id,
                final=False,
            )
        )

        try:
            # Extract and validate client_id
            client_id = self._extract_client_id(context)
            validate_client_id(client_id)

            # Parse alert parameters from message
            alert_params = self._parse_alert_params(context)

            logger.info(
                "A2A request: client=%s case=%s type=%s",
                client_id,
                alert_params.get("case_id"),
                alert_params.get("alert_type"),
            )

            # Publish working event
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=task_id,
                    status=TaskStatus(
                        state=TaskState.working,
                        timestamp=_now_iso(),
                        message=_agent_message(
                            f"Processing alert for client {client_id}"
                        ),
                    ),
                    contextId=context_id,
                    final=False,
                )
            )

            # Run the orchestrator pipeline
            result = await self._orchestrator.process_alert(
                client_id=client_id,
                **alert_params,
            )

            # Publish result as artifact + completed status
            result_text = json.dumps(result, default=str)
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    taskId=task_id,
                    contextId=context_id,
                    lastChunk=True,
                    artifact=Artifact(
                        artifactId="pipeline-result",
                        parts=[_text_part(result_text)],
                    ),
                )
            )
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=task_id,
                    status=TaskStatus(
                        state=TaskState.completed,
                        timestamp=_now_iso(),
                    ),
                    contextId=context_id,
                    final=True,
                )
            )

        except Exception as e:
            logger.error("A2A execution failed: %s", e, exc_info=True)
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=task_id,
                    status=TaskStatus(
                        state=TaskState.failed,
                        timestamp=_now_iso(),
                        message=_agent_message(f"Error: {e}"),
                    ),
                    contextId=context_id,
                    final=True,
                )
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise NotImplementedError("Cancellation not supported")

    def _extract_client_id(self, context: RequestContext) -> str:
        """Extract client_id from A2A request or message metadata.

        Checks request-level metadata first, then message-level metadata.
        Uses context.metadata (request-level) and context.message.metadata.
        """
        # Check request-level metadata (MessageSendParams.metadata)
        req_meta = getattr(context, "metadata", None)
        if req_meta and req_meta.get("client_id"):
            return str(req_meta["client_id"])

        # Check message-level metadata
        message = getattr(context, "message", None)
        if message and message.metadata and message.metadata.get("client_id"):
            return str(message.metadata["client_id"])

        raise ValueError(
            "client_id required in A2A request or message metadata. "
            "Include {'client_id': 'your-client-id'} in the metadata field."
        )

    def _parse_alert_params(self, context: RequestContext) -> dict:
        """Parse alert parameters from the A2A message.

        Supports two formats:
        1. Structured JSON: {"case_id": "...", "alert_type": "...", ...}
        2. Natural language fallback: text passed as case_id with UNKNOWN type
        """
        message_text = self._get_message_text(context)

        # Try structured JSON first
        try:
            params = json.loads(message_text)
            if isinstance(params, dict) and "case_id" in params:
                return {
                    "case_id": str(params["case_id"]),
                    "alert_type": str(params.get("alert_type", "UNKNOWN")),
                    "severity": str(params.get("severity", "MEDIUM")),
                    "autonomous_mode": bool(params.get("autonomous_mode", False)),
                    "gti_enabled": bool(params.get("gti_enabled", False)),
                    "raw_alert": params.get("raw_alert"),
                }
        except (json.JSONDecodeError, TypeError):
            pass

        # Natural language fallback — pass the raw text as context
        return {
            "case_id": f"A2A-{context.task_id or 'unknown'}",
            "alert_type": "UNKNOWN",
            "severity": "MEDIUM",
            "raw_alert": {"a2a_message": message_text},
        }

    def _get_message_text(self, context: RequestContext) -> str:
        """Extract text content from A2A message parts."""
        message = getattr(context, "message", None)
        if not message:
            return ""
        parts = message.parts
        texts = []
        for part in parts:
            # Part is a RootModel; the actual part is in .root
            inner = part.root if hasattr(part, "root") else part
            if hasattr(inner, "text"):
                texts.append(inner.text)
        return "\n".join(texts)
