"""
Agent Engine App Wrapper — Vertex AI Agent Engine entrypoint.

Wraps AgenticSOCOrchestrator for deployment to Vertex AI Agent Engine.
Agent Engine calls set_up() once at instance start, then query() per request.

Multi-tenancy: One deployment serves N clients. client_id is passed per query
and routed to the correct Chronicle tenant via the MCP Gateway.

Sync-to-async bridging:
    Agent Engine calls query() synchronously, but our orchestrator is async.
    We use threading.Thread + asyncio.run() + queue.Queue (matching ADK's
    Runner.run() pattern) to bridge the gap. This avoids anyio cancel scope
    violations that occur with ThreadPoolExecutor in Python 3.11.
    See: google.adk.runners.Runner.run() for the reference pattern.
"""

import asyncio
import logging
import os
import queue
import threading
from typing import Optional

from agents.orchestrator.agent import AgenticSOCOrchestrator
from agents.compat import patch_anyio_cancel_scope_for_python311
from observability.tracing import init_tracing

logger = logging.getLogger(__name__)

# Default timeout for query execution (seconds)
_QUERY_TIMEOUT = int(os.environ.get("AGENT_ENGINE_QUERY_TIMEOUT", "300"))


def _run_async(coro, timeout: int = _QUERY_TIMEOUT):
    """Bridge sync → async using a dedicated thread with its own event loop.

    Matches the pattern used by ADK's Runner.run():
      - Dedicated threading.Thread (not ThreadPoolExecutor)
      - asyncio.run() for a clean, isolated event loop per call
      - queue.Queue for thread-safe result passing

    This ensures MCP's anyio cancel scopes stay within a single task
    and avoids the Python 3.11 asyncio.wait_for() task-boundary bug.
    """
    result_queue: queue.Queue = queue.Queue(maxsize=1)

    def _thread_main():
        try:
            result = asyncio.run(coro)
            result_queue.put(("ok", result))
        except Exception as e:
            result_queue.put(("error", e))

    thread = threading.Thread(target=_thread_main, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    try:
        status, value = result_queue.get_nowait()
    except queue.Empty:
        logger.error("query() timed out after %ds", timeout)
        return {
            "error": f"Request timed out after {timeout}s",
            "status": "TIMEOUT",
        }

    if status == "error":
        raise value
    return value


class AgenticSOCApp:
    """
    Vertex AI Agent Engine application wrapper.

    Lifecycle:
        1. Agent Engine deserializes this class
        2. Calls set_up() once — creates the orchestrator
        3. Calls query() per incoming request
        4. Calls health_check() for readiness probes
    """

    def __init__(self):
        self.orchestrator: AgenticSOCOrchestrator | None = None

    def set_up(self):
        """Called once when Agent Engine starts the instance."""
        logger.warning("AgenticSOCApp.set_up() — initializing orchestrator")
        # Diagnostic: log key env vars so we can debug auth issues
        logger.warning(
            "Environment: AGENT_ENGINE_ID=%s PROJECT=%s LOCATION=%s "
            "GENAI_USE_VERTEXAI=%s MCP_GATEWAY_URL=%s",
            os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID", "<unset>"),
            os.environ.get("GOOGLE_CLOUD_PROJECT", "<unset>"),
            os.environ.get("GOOGLE_CLOUD_LOCATION", "<unset>"),
            os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "<unset>"),
            os.environ.get("MCP_GATEWAY_URL", "<unset>"),
        )
        patch_anyio_cancel_scope_for_python311()
        init_tracing(service_name="agentic-soc-agent-engine")
        self.orchestrator = AgenticSOCOrchestrator(
            partner_project_id=os.environ["PARTNER_PROJECT_ID"],
            gateway_url=os.environ["MCP_GATEWAY_URL"],
            gti_url=os.environ.get("GTI_GATEWAY_URL", ""),
        )
        logger.info("AgenticSOCApp ready")

    def query(
        self,
        *,
        client_id: str,
        case_id: str,
        alert_type: str,
        severity: str = "MEDIUM",
        autonomous_mode: bool = False,
        gti_enabled: bool = False,
        trigger: str = "RULE_DETECTION",
        raw_alert: Optional[dict] = None,
        mode: str = "process_alert",
        approval_id: Optional[str] = None,
    ) -> dict:
        """
        Main entry point invoked by Agent Engine per request.

        autonomous_mode should be set from the server-side client config
        at the calling layer. Containment actions always require HITL
        regardless of autonomous_mode.
        """
        if self.orchestrator is None:
            return {"error": "Service not ready. set_up() has not completed.", "status": "ERROR"}

        if mode == "execute_approval":
            if not approval_id:
                raise ValueError("approval_id required for execute_approval mode")
            return _run_async(
                self.orchestrator.execute_approved_action(approval_id, requesting_client_id=client_id),
                timeout=_QUERY_TIMEOUT,
            )

        return _run_async(
            self.orchestrator.process_alert(
                client_id=client_id,
                case_id=case_id,
                alert_type=alert_type,
                severity=severity,
                trigger=trigger,
                raw_alert=raw_alert,
                autonomous_mode=autonomous_mode,
                gti_enabled=gti_enabled,
            ),
            timeout=_QUERY_TIMEOUT,
        )

    def health_check(self) -> dict:
        """Readiness probe for Agent Engine."""
        initialized = self.orchestrator is not None
        return {
            "status": "healthy" if initialized else "unhealthy",
            "orchestrator_initialized": initialized,
        }
