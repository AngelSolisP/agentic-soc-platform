"""
Orchestrator Agent — Top-level coordinator for the Agentic SOC multi-agent system.

Routes security events through the correct workflow:
  Alert → Triage → Enrichment → Case Management → [Response with HITL]

Uses Gemini 2.5 Pro for complex orchestration decisions.
"""

import asyncio
import os
import logging
import json
import time
from typing import Optional

from opentelemetry import trace
from opentelemetry.trace import StatusCode

from observability.tracing import get_tracer
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai.types import Content, Part

from .prompts import ORCHESTRATOR_SYSTEM_PROMPT, ORCHESTRATOR_TASK_TEMPLATE
from agents.validation import safe_agent_name
from agents.memory_config import create_memory_service
from agents.plugins import ChronicleRetryPlugin, CostGuardPlugin, ContextTrimmerPlugin
from agents.cost_guard import llm_call_guard

logger = logging.getLogger(__name__)

# ── LLM Call Guard ────────────────────────────────────────────────────────────
# Dual protection (call budget + wall-clock timeout) defined in agents/cost_guard.py.
# Applied as before_model_callback on EVERY agent in the pipeline.
# Also registered as CostGuardPlugin on the Runner (belt and suspenders).
MAX_LLM_CALLS_PER_PIPELINE = int(os.environ.get("MAX_LLM_CALLS_PER_PIPELINE", "25"))

# Constant app_name for Memory Bank scope isolation.
# All clients share one app_name; user_id=client_id provides tenant isolation.
APP_NAME = "agentic_soc"


async def _save_pipeline_memories(callback_context) -> None:
    """after_agent_callback: persist session to Memory Bank (best-effort)."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        logger.warning("Memory save failed (non-fatal): %s", e)


def _create_session_service():
    """Create session service: VertexAiSessionService for production, InMemory for local dev."""
    use_vertex = os.environ.get("USE_VERTEX_SESSION_SERVICE", "").lower() in ("true", "1", "yes")
    if use_vertex:
        try:
            from google.adk.sessions import VertexAiSessionService
            project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
            if not project:
                logger.warning("USE_VERTEX_SESSION_SERVICE=true but GOOGLE_CLOUD_PROJECT not set, falling back to InMemory")
                return InMemorySessionService()
            logger.info("Using VertexAiSessionService", extra={"project": project, "location": location})
            return VertexAiSessionService(project=project, location=location)
        except Exception as e:
            logger.warning("VertexAiSessionService init failed, falling back to InMemory: %s", e)
            return InMemorySessionService()
    return InMemorySessionService()
from agents.triage.agent import create_triage_agent, build_triage_task
from agents.enrichment.agent import create_enrichment_agent, build_enrichment_task
from agents.case_manager.agent import create_case_manager_agent, build_case_manager_task
from agents.response.agent import create_response_agent, HITLQueue, build_response_task
from agents.dedup import AlertDeduplicator
from agents.stage_tracker import StageTracker, classify_agent
from agents.validation import validate_client_id, sanitize_alert_payload
from agents.notifications import (
    NotificationService,
    notify_agent_timeout,
    notify_hitl_timeout,
    notify_hitl_submission,
    notify_escalation,
)


class AgenticSOCOrchestrator:
    """
    Top-level orchestrator for the Agentic SOC platform.

    Manages agent lifecycles per client, runs end-to-end SOC workflows,
    and provides the main entry point for alert processing.
    """

    def __init__(
        self,
        partner_project_id: str,
        gateway_url: Optional[str] = None,
        gti_url: Optional[str] = None,
        orchestrator_model: Optional[str] = None,
        notification_service: Optional[NotificationService] = None,
        memory_service=None,
    ):
        self._partner_project_id = partner_project_id
        self._gateway_url = gateway_url or os.environ.get(
            "MCP_GATEWAY_URL", "http://localhost:8080"
        )
        self._gti_url = gti_url or os.environ.get("GTI_GATEWAY_URL", "")
        self._orchestrator_model = orchestrator_model or os.environ.get(
            "GEMINI_PRO_MODEL", "gemini-2.5-pro"
        )
        self._agent_timeout = int(os.environ.get("AGENT_TIMEOUT_SECONDS", "300"))
        self._notifications = notification_service
        # Cache agents per client to avoid re-creating toolsets
        self._agent_cache: dict[str, dict] = {}
        self._session_service = _create_session_service()
        self._memory_service = memory_service if memory_service is not None else create_memory_service()
        self._dedup = AlertDeduplicator(
            partner_project_id=partner_project_id,
            ttl_seconds=int(os.environ.get("DEDUP_TTL_SECONDS", "900")),
            database=os.environ.get("FIRESTORE_DATABASE", "(default)"),
        )
        self._stage_tracker = StageTracker(
            partner_project_id=partner_project_id,
            database=os.environ.get("FIRESTORE_DATABASE", "(default)"),
        )

    def _get_agents(self, client_id: str, gti_enabled: bool = False) -> dict:
        """Get or create agent instances for a client."""
        cache_key = f"{client_id}:gti={gti_enabled}"
        if cache_key not in self._agent_cache:
            logger.info("Creating agent pool", extra={"client_id": client_id, "gti_enabled": gti_enabled})
            agents = {
                "triage": create_triage_agent(
                    client_id, self._gateway_url,
                    before_model_callback=llm_call_guard,
                ),
                "enrichment": create_enrichment_agent(
                    client_id,
                    self._gateway_url,
                    gti_gateway_url=self._gti_url or None,
                    gti_enabled=gti_enabled,
                    before_model_callback=llm_call_guard,
                ),
                "case_manager": create_case_manager_agent(
                    client_id, self._gateway_url,
                    before_model_callback=llm_call_guard,
                ),
                "response": create_response_agent(
                    client_id, self._gateway_url,
                    before_model_callback=llm_call_guard,
                ),
            }
            self._agent_cache[cache_key] = agents
        return self._agent_cache[cache_key]

    @staticmethod
    def _extract_iocs_from_triage(triage_text: str) -> list[dict]:
        """Extract IoCs from triage output text. Best-effort JSON parse."""
        import re
        iocs = []
        try:
            # Try to find iocs_found array in JSON
            match = re.search(r'"iocs_found"\s*:\s*\[(.*?)\]', triage_text, re.DOTALL)
            if match:
                iocs_json = "[" + match.group(1) + "]"
                iocs = json.loads(iocs_json)
        except (json.JSONDecodeError, AttributeError):
            pass
        return iocs

    async def _run_single_agent(
        self,
        agent: LlmAgent,
        agent_key: str,
        task_text: str,
        session_id: str,
        case_id: str,
        client_id: str,
        tracer,
    ) -> str:
        """Run a single agent with its own Runner and return its text output.

        Each agent gets an independent Runner + MCP session lifecycle.
        This avoids ADK's transfer_to_agent (which is a permanent handoff)
        and gives us explicit sequential control.
        """
        print(f"[PIPELINE] === Starting {agent_key} ===")
        # Write RUNNING stage to Firestore immediately
        agent_data = {"texts": [], "started": time.time(), "ended": 0}
        try:
            self._stage_tracker.record_stage_incremental(
                session_id=session_id, case_id=case_id,
                client_id=client_id, agent_key=agent_key,
                agent_data=agent_data,
            )
        except Exception:
            pass

        span = tracer.start_span(f"orchestrator.stage.{agent_key}")
        span.set_attribute("agent.name", agent_key)

        runner = Runner(
            agent=agent,
            app_name=APP_NAME,
            session_service=self._session_service,
            plugins=[ChronicleRetryPlugin(), ContextTrimmerPlugin()],
        )
        session = await self._session_service.create_session(
            app_name=APP_NAME, user_id=client_id,
        )

        result_text = ""
        event_count = 0
        try:
            async for event in runner.run_async(
                user_id=client_id,
                session_id=session.id,
                new_message=Content(parts=[Part(text=task_text)], role="user"),
            ):
                event_count += 1
                # Capture text output
                if event.content and event.content.parts:
                    text = "".join(
                        p.text for p in event.content.parts
                        if hasattr(p, "text") and p.text
                    )
                    if text:
                        agent_data["texts"].append(text)
                        agent_data["ended"] = time.time()

                if event.is_final_response() and event.content:
                    result_text = "".join(
                        p.text for p in event.content.parts
                        if hasattr(p, "text") and p.text
                    )
        finally:
            try:
                await runner.close()
            except Exception:
                pass
            span.set_attribute("duration_seconds", round(time.time() - agent_data["started"], 2))
            span.end()

        # Write COMPLETED stage
        agent_data["ended"] = time.time()
        try:
            self._stage_tracker.record_stage_incremental(
                session_id=session_id, case_id=case_id,
                client_id=client_id, agent_key=agent_key,
                agent_data=agent_data,
            )
        except Exception:
            pass

        duration = round(agent_data["ended"] - agent_data["started"], 2)
        print(f"[PIPELINE] === {agent_key} done: {event_count} events, {duration}s, {len(result_text)} chars ===")
        return result_text, agent_data

    async def process_alert(
        self,
        client_id: str,
        case_id: str,
        alert_type: str,
        severity: str = "MEDIUM",
        trigger: str = "RULE_DETECTION",
        raw_alert: Optional[dict] = None,
        autonomous_mode: bool = False,
        gti_enabled: bool = False,
        chronicle_region: str = "us",
    ) -> dict:
        """
        Main entry point: process a security alert end-to-end.

        Runs agents SEQUENTIALLY — each agent gets its own Runner and MCP session.
        This avoids ADK's transfer_to_agent (permanent handoff) and guarantees
        all pipeline stages execute: Triage → Enrichment → Case Manager → [Response].
        """
        validate_client_id(client_id)

        # Dedup check
        if self._dedup.is_duplicate(client_id, alert_type, case_id):
            previous = self._dedup.get_previous_result(client_id, alert_type, case_id)
            logger.info("Skipping duplicate alert", extra={"client_id": client_id, "case_id": case_id})
            return previous or {
                "case_id": case_id, "client_id": client_id,
                "deduplicated": True, "agent_response": "Alert already processed within dedup window.",
            }

        tracer = get_tracer("agentic_soc.orchestrator")
        with tracer.start_as_current_span("orchestrator.process_alert") as root_span:
            root_span.set_attribute("client.id", client_id)
            root_span.set_attribute("case.id", case_id)
            root_span.set_attribute("alert.type", alert_type)
            root_span.set_attribute("severity", severity)

            start_time = time.time()
            print(f"[PIPELINE] Starting sequential pipeline: client={client_id} case={case_id} type={alert_type}")

            agents = self._get_agents(client_id, gti_enabled=gti_enabled)
            # Shared session_id for stage grouping in Firestore
            pipeline_session_id = f"pipeline-{case_id}-{int(start_time)}"
            agent_outputs: dict[str, dict] = {}
            pipeline_errors: dict[str, dict] = {}
            timed_out = False
            triage_text = ""
            enrichment_text = ""
            cm_text = ""
            recommended_action = "ESCALATE_T2"

            try:
                async with asyncio.timeout(self._agent_timeout):
                    # ── Step 1: Triage (ALWAYS) ──
                    triage_task = build_triage_task(
                        case_id=case_id, client_id=client_id,
                        alert_type=alert_type, severity=severity,
                        autonomous_mode=autonomous_mode,
                    )
                    triage_text, triage_data = await self._run_single_agent(
                        agent=agents["triage"], agent_key="triage",
                        task_text=triage_task, session_id=pipeline_session_id,
                        case_id=case_id, client_id=client_id, tracer=tracer,
                    )
                    agent_outputs["triage"] = triage_data

                    # ── Step 2: Enrichment (ALWAYS) ──
                    # Extract IoCs from triage text for enrichment
                    triage_iocs = self._extract_iocs_from_triage(triage_text)
                    enrichment_task = build_enrichment_task(
                        case_id=case_id, client_id=client_id,
                        iocs=triage_iocs,
                        alert_context=triage_text[:2000],
                    )
                    enrichment_text, enrichment_data = await self._run_single_agent(
                        agent=agents["enrichment"], agent_key="enrichment",
                        task_text=enrichment_task, session_id=pipeline_session_id,
                        case_id=case_id, client_id=client_id, tracer=tracer,
                    )
                    agent_outputs["enrichment"] = enrichment_data

                    # ── Step 3: Case Manager (ALWAYS) ──
                    # Extract recommended_action from triage text
                    recommended_action = "ESCALATE_T2"  # safe default
                    for action in ["CLOSE_FP", "CONTAIN", "MONITOR", "ESCALATE_T2"]:
                        if action in triage_text:
                            recommended_action = action
                            break

                    cm_task = build_case_manager_task(
                        case_id=case_id, client_id=client_id,
                        recommended_action=recommended_action,
                        triage_results=triage_text,
                        enrichment_results=enrichment_text,
                    )
                    cm_text, cm_data = await self._run_single_agent(
                        agent=agents["case_manager"], agent_key="case_manager",
                        task_text=cm_task, session_id=pipeline_session_id,
                        case_id=case_id, client_id=client_id, tracer=tracer,
                    )
                    agent_outputs["case_manager"] = cm_data

                    # ── Step 4: Response (only if CONTAIN) ──
                    response_text = ""
                    if recommended_action == "CONTAIN":
                        resp_task = build_response_task(
                            case_id=case_id, client_id=client_id,
                            approval_id="pending", approval_status="PENDING",
                            triage_results=triage_text,
                            proposed_actions=cm_text,
                        )
                        response_text, resp_data = await self._run_single_agent(
                            agent=agents["response"], agent_key="response",
                            task_text=resp_task, session_id=pipeline_session_id,
                            case_id=case_id, client_id=client_id, tracer=tracer,
                        )
                        agent_outputs["response"] = resp_data

            except TimeoutError:
                timed_out = True
                last_agent = max(agent_outputs.keys(), key=lambda k: agent_outputs[k].get("ended", 0)) if agent_outputs else "unknown"
                pipeline_errors[last_agent] = {"error": f"Timeout after {self._agent_timeout}s", "severity": "HIGH"}
                print(f"[PIPELINE] TIMEOUT — completed stages: {list(agent_outputs.keys())}")
            except Exception as e:
                # Capture which stages completed before the error
                last_agent = max(agent_outputs.keys(), key=lambda k: agent_outputs[k].get("ended", 0)) if agent_outputs else "unknown"
                error_type = type(e).__name__
                pipeline_errors[last_agent] = {
                    "error": f"{error_type}: {str(e)[:200]}",
                    "severity": "CRITICAL",
                }
                print(f"[PIPELINE] ERROR at {last_agent}: {error_type}: {e}")
                logger.error("Pipeline failed", extra={
                    "case_id": case_id, "client_id": client_id,
                    "error_type": error_type, "completed_stages": list(agent_outputs.keys()),
                })

            # Write final pipeline stages to Firestore
            try:
                self._stage_tracker.record_pipeline(
                    session_id=pipeline_session_id,
                    case_id=case_id, client_id=client_id,
                    agent_outputs=agent_outputs, errors=pipeline_errors,
                )
            except Exception as e:
                logger.warning("Stage tracking failed: %s", e)

            elapsed = round(time.time() - start_time, 2)
            result_text = cm_text or triage_text
            print(f"[PIPELINE] Complete: {elapsed}s, stages={list(agent_outputs.keys())}, timed_out={timed_out}")

            result = {
                "case_id": case_id,
                "client_id": client_id,
                "session_id": pipeline_session_id,
                "elapsed_seconds": elapsed,
                "timed_out": timed_out,
                "stages_completed": list(agent_outputs.keys()),
                "errors": pipeline_errors if pipeline_errors else None,
                "agent_response": result_text,
            }

            # IoC Feedback Loop: push confirmed MALICIOUS IoCs to Data Tables
            if triage_text and "MALICIOUS" in triage_text:
                try:
                    from agents.ioc_feedback import extract_confirmed_iocs, push_iocs, format_feedback_summary
                    confirmed_iocs = extract_confirmed_iocs(triage_text)
                    if confirmed_iocs:
                        # Call push_iocs directly (async)
                        results = await push_iocs(
                            client_id=client_id,
                            gateway_url=self._gateway_url,
                            iocs=confirmed_iocs,
                            case_id=case_id,
                        )
                        # We use build_table_rows internally in format_feedback_summary 
                        # but we can also just use the results.
                        from agents.ioc_feedback import build_table_rows
                        tables = build_table_rows(confirmed_iocs, case_id)
                        summary = format_feedback_summary(tables)
                        print(f"[PIPELINE] IoC Feedback: {summary} (results: {results})")
                        logger.info("IoC feedback loop complete", extra={
                            "case_id": case_id, "client_id": client_id,
                            "results": results,
                        })
                except Exception as e:
                    logger.warning("IoC feedback loop failed (non-fatal): %s", e)

            # Post-pipeline notifications
            if self._notifications and result_text:
                await self._send_post_pipeline_notifications(client_id, case_id, result_text)

            self._dedup.record(client_id, alert_type, case_id, result)
            return result

    async def _send_post_pipeline_notifications(
        self, client_id: str, case_id: str, result_text: str,
    ) -> None:
        """Detect HITL submissions and escalations from pipeline output and notify."""
        try:
            lower = result_text.lower()
            # Trigger 1: HITL submission detected in pipeline output
            if "pending_approval" in lower or "hitl" in lower and "pending" in lower:
                await notify_hitl_submission(
                    self._notifications, client_id, case_id,
                    proposed_action="(see case details)",
                    approval_id="(check HITL queue)",
                )
            # Trigger 3: Escalation detected in pipeline output
            if "escalat" in lower and ("t2" in lower or "tier 2" in lower or "tier-2" in lower):
                await notify_escalation(
                    self._notifications, client_id, case_id,
                    reason="Automated triage escalated to Tier 2",
                    priority="HIGH",
                )
        except Exception as e:
            logger.warning("Post-pipeline notification failed (non-fatal): %s", e)

    def invalidate_client_agents(self, client_id: str) -> None:
        """Remove cached agents for a client (use after config changes)."""
        keys_to_remove = [k for k in self._agent_cache if k.startswith(f"{client_id}:")]
        for key in keys_to_remove:
            del self._agent_cache[key]

    async def execute_approved_action(self, approval_id: str, requesting_client_id: Optional[str] = None) -> dict:
        """Execute a previously approved HITL action (two-pass model, pass 2)."""
        tracer = get_tracer("agentic_soc.orchestrator")
        with tracer.start_as_current_span("orchestrator.execute_approved_action") as span:
            span.set_attribute("approval.id", approval_id)

            hitl_queue = HITLQueue(self._partner_project_id)
            approval = hitl_queue.get_approval_status(approval_id)

            status = approval.get("status", "")
            client_id = approval.get("client_id", "")
            case_id = approval.get("case_id", "")

            # Cross-tenant check
            if requesting_client_id:
                validate_client_id(requesting_client_id)
                if client_id != requesting_client_id:
                    raise PermissionError(
                        f"Tenant mismatch: approval belongs to '{client_id}', "
                        f"but requested by '{requesting_client_id}'"
                    )

            span.set_attribute("client.id", client_id)
            span.set_attribute("case.id", case_id)
            span.set_attribute("approval.status", status)

            if status == "REJECTED":
                return {
                    "case_id": case_id,
                    "client_id": client_id,
                    "approval_id": approval_id,
                    "status": "REJECTED",
                    "agent_response": f"Action rejected by analyst. Notes: {approval.get('analyst_instructions', '')}",
                }

            if status == "EXPIRED":
                # Trigger 2: HITL timeout notification (best-effort)
                if self._notifications:
                    try:
                        await notify_hitl_timeout(
                            self._notifications, client_id, case_id, approval_id,
                        )
                    except Exception as notif_err:
                        logger.warning("HITL timeout notification failed: %s", notif_err)
                return {
                    "case_id": case_id,
                    "client_id": client_id,
                    "approval_id": approval_id,
                    "status": "EXPIRED",
                    "agent_response": "Approval expired before analyst decision. Escalate manually.",
                }

            if status not in ("APPROVED", "MODIFIED"):
                return {
                    "case_id": case_id,
                    "client_id": client_id,
                    "approval_id": approval_id,
                    "status": "ERROR",
                    "agent_response": f"Unexpected approval status: {status}",
                }

            # Build task for response agent with approval context
            start_time = time.time()

            # Use Flash for execution (action is pre-defined, no complex reasoning needed)
            flash_model = os.environ.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
            response_agent = create_response_agent(
                client_id, self._gateway_url, model=flash_model
            )
            runner_agent = LlmAgent(
                name=f"approval_executor_{safe_agent_name(client_id)}",
                model=flash_model,
                description="Executes approved HITL actions.",
                instruction="Execute the approved action as described. Report results.",
                sub_agents=[response_agent],
            )

            runner = Runner(
                agent=runner_agent,
                app_name=APP_NAME,
                session_service=self._session_service,
                memory_service=self._memory_service,
                plugins=[
                    CostGuardPlugin(),
                    ChronicleRetryPlugin(),
                ],
            )

            session = await self._session_service.create_session(
                app_name=APP_NAME,
                user_id=client_id,
                state={"approval_status": status},
            )

            proposed_actions = json.dumps(approval.get("proposed_action", {}))
            if status == "MODIFIED":
                proposed_actions = json.dumps(
                    approval.get("modified_parameters", approval.get("proposed_action", {}))
                )

            task_text = build_response_task(
                case_id=case_id,
                client_id=client_id,
                approval_id=approval_id,
                approval_status=status,
                triage_results=approval.get("triage_summary", ""),
                proposed_actions=proposed_actions,
                analyst_instructions=approval.get("analyst_instructions", ""),
            )

            result_text = ""
            try:
                async with asyncio.timeout(self._agent_timeout):
                    async for event in runner.run_async(
                        user_id=client_id,
                        session_id=session.id,
                        new_message=Content(parts=[Part(text=task_text)], role="user"),
                    ):
                        if event.is_final_response() and event.content:
                            result_text = "".join(
                                part.text for part in event.content.parts if hasattr(part, "text")
                            )
            except TimeoutError as te:
                result_text = f"TIMEOUT: Approval execution exceeded {self._agent_timeout}s."
                span.record_exception(te)
                span.set_status(StatusCode.ERROR, "timeout")

            elapsed = round(time.time() - start_time, 2)
            execution_status = "TIMEOUT" if "TIMEOUT" in result_text else "EXECUTED"

            return {
                "case_id": case_id,
                "client_id": client_id,
                "approval_id": approval_id,
                "session_id": session.id,
                "status": execution_status,
                "elapsed_seconds": elapsed,
                "agent_response": result_text,
            }
