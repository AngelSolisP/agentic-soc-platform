"""Agentic SOC Workbench — FastAPI backend."""
import asyncio
from contextlib import asynccontextmanager
import logging
import os
import threading

# Configure root logger so agent INFO logs appear in Cloud Run stdout
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.cloud import firestore
import httpx

from observability.tracing import init_tracing, shutdown_tracing, register_sigterm_handler
from workbench.backend.admin import router as admin_router
from workbench.backend.auth import get_current_analyst
from workbench.backend.audit import AuditLogger
from workbench.backend.cases import router as cases_router
from workbench.backend.chat import router as chat_router
from workbench.backend.detections import router as detections_router
from workbench.backend.investigations import router as investigations_router
from workbench.backend.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    check_dev_mode_safety,
    is_production,
)
from workbench.backend.watchlists import router as watchlists_router
from workbench.backend.ws import router as ws_router


class BackgroundTaskManager:
    """Runs fire-and-forget coroutines in dedicated threads.

    Each task gets its own thread + event loop, fully isolated from the main
    uvicorn event loop. This prevents MCP sessions (anyio cancel scopes) and
    heavy Gemini calls from blocking health check responses.
    """

    def __init__(self) -> None:
        self._threads: dict[str, threading.Thread] = {}

    def create_task(self, coro, *, name: str | None = None) -> None:
        task_name = name or f"bg-{id(coro)}"

        def _run():
            try:
                # Apply anyio cancel scope patch (Python 3.11 workaround)
                from agents.compat import patch_anyio_cancel_scope_for_python311
                patch_anyio_cancel_scope_for_python311()
                asyncio.run(coro)
                logging.getLogger(__name__).info("Background task %s completed", task_name)
            except Exception:
                logging.getLogger(__name__).exception("Background task %s failed", task_name)
            finally:
                self._threads.pop(task_name, None)

        thread = threading.Thread(target=_run, name=task_name, daemon=True)
        self._threads[task_name] = thread
        thread.start()

    @property
    def active_count(self) -> int:
        return len(self._threads)

logger = logging.getLogger(__name__)

PARTNER_PROJECT_ID = os.environ.get("PARTNER_PROJECT_ID", "")
MCP_GATEWAY_URL = os.environ.get("MCP_GATEWAY_URL", "http://localhost:8080")
GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Security: refuse DEV_MODE in production
    check_dev_mode_safety()

    init_tracing("agentic-soc-workbench")
    register_sigterm_handler()

    app.state.db = firestore.Client(
        project=PARTNER_PROJECT_ID or None,
        database=os.environ.get("FIRESTORE_DATABASE", "(default)"),
    )
    app.state.mcp_gateway_url = MCP_GATEWAY_URL
    # Timeout: 60s connect (Cloud Run cold starts), 60s read (Chronicle MCP can be slow)
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(timeout=10.0, connect=60.0, read=60.0, write=10.0),
    )
    app.state.mcp_client = None  # Lazy init — MCPClient created per request
    app.state.audit = AuditLogger(app.state.db)
    app.state.tasks = BackgroundTaskManager()

    logger.info("Workbench started", extra={"project": PARTNER_PROJECT_ID})
    yield

    await app.state.http_client.aclose()
    shutdown_tracing()
    logger.info("Workbench stopped")


# Hide OpenAPI docs in production (OWASP A05)
_docs_url = None if is_production() else "/docs"
_redoc_url = None if is_production() else "/redoc"

app = FastAPI(
    title="Agentic SOC Workbench",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

app.include_router(cases_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(watchlists_router, prefix="/api")
app.include_router(investigations_router, prefix="/api")
app.include_router(detections_router, prefix="/api")
app.include_router(ws_router)
app.include_router(admin_router, prefix="/api/admin")

# Security middleware stack (order matters — outermost runs first)
# 1. Rate limiting (reject before processing)
app.add_middleware(RateLimitMiddleware)
# 2. Request size limit
app.add_middleware(RequestSizeLimitMiddleware)
# 3. Security headers (added to all responses)
app.add_middleware(SecurityHeadersMiddleware)
# 4. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)


@app.get("/api/me")
async def get_me(analyst: dict = Depends(get_current_analyst)):
    """Return current analyst profile (email, role, allowed_clients)."""
    return {
        "email": analyst.get("email", ""),
        "role": analyst.get("role", "analyst"),
        "allowed_clients": analyst.get("allowed_clients", []),
        "auth_method": analyst.get("auth_method", ""),
    }


@app.get("/api/config")
async def get_public_config():
    """Public config for frontend — no auth required."""
    return {"google_client_id": GOOGLE_OAUTH_CLIENT_ID}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agentic-soc-workbench"}


@app.get("/health/ready")
async def health_ready(request: Request):
    try:
        db = request.app.state.db
        list(db.collection("clients").limit(1).stream())
        return {"status": "ready"}
    except Exception as e:
        logger.warning("Readiness probe failed", extra={"error": str(e)})
        # OWASP A09: Don't leak internal error details
        return JSONResponse(
            status_code=503, content={"status": "not_ready", "error": "database_unavailable"}
        )


# Serve React SPA — must be LAST (catch-all route)
from pathlib import Path  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from workbench.backend.security import is_safe_path  # noqa: E402

static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if static_dir.is_dir():
    # Serve static assets (JS, CSS, images) at /assets
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # SPA catch-all: any non-API, non-health route returns index.html
    # so React Router handles client-side routing
    index_file = static_dir / "index.html"

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Serve actual files if they exist (favicon, robots.txt, etc.)
        file_path = static_dir / full_path
        # OWASP A01: Path traversal protection
        if full_path and file_path.is_file() and is_safe_path(static_dir, file_path):
            return FileResponse(file_path)
        return FileResponse(index_file)
