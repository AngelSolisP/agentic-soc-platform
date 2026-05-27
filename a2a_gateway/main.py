"""
Agentic SOC — A2A Gateway.

FastAPI application that exposes the SOC orchestrator via the Agent2Agent
protocol. Uses a2a-sdk routes for agent card and JSON-RPC, with FastAPI
health probes and structured logging.

Endpoints:
    /.well-known/agent-card.json  — Public agent card (no auth)
    /                              — A2A JSON-RPC endpoint (auth required)
    /health                        — Basic health check
    /health/ready                  — Deep readiness probe
"""

import logging
import os
from contextlib import asynccontextmanager

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from a2a_gateway.agent_card import build_agent_card
from a2a_gateway.executor import TenantAwareA2aExecutor

logger = logging.getLogger(__name__)

# --- Configuration ---
PARTNER_PROJECT_ID = os.environ.get("PARTNER_PROJECT_ID", "")
MCP_GATEWAY_URL = os.environ.get("MCP_GATEWAY_URL", "")
GTI_GATEWAY_URL = os.environ.get("GTI_GATEWAY_URL", "")
A2A_EXTERNAL_URL = os.environ.get("A2A_EXTERNAL_URL", "")
PORT = int(os.environ.get("PORT", "8080"))


def _create_app() -> FastAPI:
    """Create the FastAPI app with A2A routes mounted at import time.

    The A2A Starlette routes (agent card + JSON-RPC) are mounted during
    app construction so they're available immediately (not deferred to
    lifespan). The orchestrator is created lazily in lifespan.
    """
    from agents.orchestrator.agent import AgenticSOCOrchestrator
    from observability.tracing import init_tracing, shutdown_tracing

    # Build A2A components eagerly (lightweight, no GCP calls)
    rpc_url = A2A_EXTERNAL_URL or f"http://localhost:{PORT}"
    agent_card = build_agent_card(rpc_url)

    # Executor starts with no orchestrator — set in lifespan
    executor = TenantAwareA2aExecutor(orchestrator=None)

    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
    )

    a2a_starlette = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    @asynccontextmanager
    async def lifespan(fastapi_app: FastAPI):
        """Initialize orchestrator and tracing on startup."""
        init_tracing("agentic-soc-a2a-gateway")

        orchestrator = AgenticSOCOrchestrator(
            partner_project_id=PARTNER_PROJECT_ID,
            gateway_url=MCP_GATEWAY_URL,
            gti_url=GTI_GATEWAY_URL,
        )
        fastapi_app.state.orchestrator = orchestrator
        fastapi_app.state.agent_card = agent_card

        # Wire orchestrator into executor (was None at construction)
        executor._orchestrator = orchestrator

        logger.info(
            "A2A Gateway started",
            extra={"rpc_url": rpc_url, "skills": len(agent_card.skills)},
        )

        yield

        shutdown_tracing()
        logger.info("A2A Gateway shutdown")

    fastapi_app = FastAPI(
        title="Agentic SOC — A2A Gateway",
        version="1.0.0",
        description="Agent2Agent protocol endpoint for the MSSP SOC orchestrator",
        lifespan=lifespan,
    )

    # Mount A2A routes (agent card + JSON-RPC) — available immediately
    a2a_starlette.add_routes_to_app(fastapi_app)

    # --- Health Endpoints ---

    @fastapi_app.get("/health")
    async def health():
        """Basic health check."""
        return {"status": "ok", "service": "a2a-gateway"}

    @fastapi_app.get("/health/ready")
    async def health_ready():
        """Deep readiness probe — verifies orchestrator is initialized."""
        checks = {
            "orchestrator": getattr(fastapi_app.state, "orchestrator", None) is not None,
            "agent_card": getattr(fastapi_app.state, "agent_card", None) is not None,
        }
        all_ok = all(checks.values())
        return JSONResponse(
            status_code=200 if all_ok else 503,
            content={"status": "ready" if all_ok else "not_ready", "checks": checks},
        )

    return fastapi_app


app = _create_app()
