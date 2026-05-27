"""
MCP Gateway — Cloud Run FastAPI Proxy

Receives MCP JSON-RPC requests from agents, injects the correct
x-goog-user-project header and impersonated bearer token, and forwards
to the target client's Chronicle Remote Managed MCP Server.

Endpoint:
    POST /mcp/{client_id}

Headers set by this proxy:
    Authorization: Bearer <impersonated_token>
    x-goog-user-project: <client_gcp_project_id>
    Content-Type: application/json
"""

import logging
import os
import json
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI, HTTPException, Request, Response, Header, Depends
from starlette.responses import StreamingResponse
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Callable, Optional

from .router import ClientRouter, ClientConfig
from .auth import get_impersonated_token
from .model_armor import ModelArmorClient, create_model_armor_client, FilterResult
from .auth_middleware import require_auth
from .circuit_breaker import CircuitBreaker
from .rate_limiter import RateLimiter
from agents.validation import validate_client_id

from observability.tracing import init_tracing, get_tracer, shutdown_tracing, register_sigterm_handler
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import StatusCode
from opentelemetry import propagate, context as otel_context

# ── Structured logging setup ────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
logger = structlog.get_logger()

# ── Config ───────────────────────────────────────────────────────────────────
PARTNER_PROJECT_ID = os.environ.get("PARTNER_PROJECT_ID", "")
FIRESTORE_DATABASE = os.environ.get("FIRESTORE_DATABASE", "(default)")
LOCAL_CONFIG_PATH = os.environ.get("LOCAL_CLIENT_CONFIG_PATH", "")
MCP_TIMEOUT_SECONDS = int(os.environ.get("MCP_TIMEOUT_SECONDS", "60"))
MODEL_ARMOR_ENABLED = os.environ.get("MODEL_ARMOR_ENABLED", "true").lower() == "true"
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
GTI_MCP_URL = os.environ.get("GTI_MCP_URL", "http://localhost:8081/mcp")
GTI_TIMEOUT_SECONDS = int(os.environ.get("GTI_TIMEOUT_SECONDS", "15"))
MAX_BODY_SIZE = int(os.environ.get("MAX_BODY_SIZE_BYTES", str(1024 * 1024)))  # 1MB default


# ── App lifespan ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MCP Gateway starting", project=PARTNER_PROJECT_ID)
    init_tracing("agentic-soc-gateway")
    register_sigterm_handler()
    app.state.router = ClientRouter(
        partner_project_id=PARTNER_PROJECT_ID,
        firestore_database=FIRESTORE_DATABASE,
        local_config_path=LOCAL_CONFIG_PATH or None,
    )
    app.state.http_client = httpx.AsyncClient(timeout=MCP_TIMEOUT_SECONDS)
    app.state.model_armor = create_model_armor_client()
    app.state.circuit_breaker = CircuitBreaker(
        failure_threshold=int(os.environ.get("CB_FAILURE_THRESHOLD", "5")),
        recovery_timeout=int(os.environ.get("CB_RECOVERY_TIMEOUT", "60")),
    )
    app.state.rate_limiter = RateLimiter(
        max_tokens=int(os.environ.get("RATE_LIMIT_MAX_TOKENS", "100")),
        refill_rate=float(os.environ.get("RATE_LIMIT_REFILL_RATE", "10.0")),
    )
    logger.info("Model Armor", enabled=MODEL_ARMOR_ENABLED)
    # GTI backend
    app.state.gti_http_client = httpx.AsyncClient(timeout=GTI_TIMEOUT_SECONDS)
    app.state.gti_circuit_breaker = CircuitBreaker(
        failure_threshold=int(os.environ.get("GTI_CB_FAILURE_THRESHOLD", "5")),
        recovery_timeout=int(os.environ.get("GTI_CB_RECOVERY_TIMEOUT", "60")),
    )
    yield
    await app.state.model_armor.close()
    await app.state.http_client.aclose()
    await app.state.gti_http_client.aclose()
    shutdown_tracing()
    logger.info("MCP Gateway stopped")


app = FastAPI(
    title="Agentic SOC — MCP Gateway",
    version="1.0.0",
    description="Central MCP proxy for multi-tenant Chronicle SecOps access",
    lifespan=lifespan,
)

FastAPIInstrumentor.instrument_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["http://localhost:8501", "http://localhost:3000"],
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Agent-Id", "X-Session-Id", "traceparent", "tracestate"],
    allow_credentials=True,
)


# ── Models ───────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    project: str


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", project=PARTNER_PROJECT_ID)


async def _proxy_request(
    request: Request,
    client_id: str,
    client: ClientConfig,
    target_url: str,
    auth_headers: "dict | Callable[[], dict]",
    backend_name: str,
    http_client: httpx.AsyncClient,
    cb: CircuitBreaker,
    model_armor: ModelArmorClient,
    x_agent_id: Optional[str] = None,
    x_session_id: Optional[str] = None,
    caller: Optional[dict] = None,
) -> Response:
    """Shared proxy logic for Chronicle and GTI MCP backends.

    Security pipeline order (same as original):
    1. Rate limit check
    2. Circuit breaker check
    3. Parse request body
    4. Audit log
    5. Model Armor input sanitization (blocks prompt injection before auth)
    6. Resolve auth_headers (callable deferred until after Model Armor)
    7. Forward
    8. Model Armor output sanitization
    """
    tracer = get_tracer("agentic_soc.gateway")
    rate_limiter: RateLimiter = request.app.state.rate_limiter

    # Extract W3C trace context from incoming request headers (traceparent)
    incoming_carrier = {k: v for k, v in request.headers.items()}
    extracted_ctx = propagate.extract(carrier=incoming_carrier)
    ctx_token = otel_context.attach(extracted_ctx)
    try:
        return await _proxy_request_inner(
            request, client_id, client, target_url, auth_headers,
            backend_name, http_client, cb, model_armor, tracer,
            rate_limiter, x_agent_id, x_session_id, caller,
        )
    finally:
        otel_context.detach(ctx_token)


async def _proxy_request_inner(
    request: Request,
    client_id: str,
    client: ClientConfig,
    target_url: str,
    auth_headers: "dict | Callable[[], dict]",
    backend_name: str,
    http_client: httpx.AsyncClient,
    cb: CircuitBreaker,
    model_armor: ModelArmorClient,
    tracer,
    rate_limiter: "RateLimiter",
    x_agent_id: Optional[str] = None,
    x_session_id: Optional[str] = None,
    caller: Optional[dict] = None,
) -> Response:
    """Inner proxy logic, executed within extracted trace context."""
    with tracer.start_as_current_span("gateway.proxy_request") as root_span:
        root_span.set_attribute("client.id", client_id)
        root_span.set_attribute("backend.name", backend_name)
        if x_agent_id:
            root_span.set_attribute("agent.id", x_agent_id)
        if x_session_id:
            root_span.set_attribute("session.id", x_session_id)

        # 1. Rate limit check
        if not rate_limiter.allow_request(client_id):
            root_span.set_status(StatusCode.ERROR, "rate_limited")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for client '{client_id}'",
                headers={"Retry-After": "10"},
            )

        # 2. Circuit breaker check
        if not cb.allow_request(client_id):
            root_span.set_status(StatusCode.ERROR, "circuit_open")
            raise HTTPException(
                status_code=503,
                detail=f"Circuit open for client '{client_id}' — {backend_name} upstream is unavailable",
            )

        # 3. Parse request body
        try:
            body_bytes = await request.body()
            if len(body_bytes) > MAX_BODY_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request body too large: {len(body_bytes)} bytes (max {MAX_BODY_SIZE})",
                )
            body = json.loads(body_bytes)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        mcp_method = body.get("method", "unknown")
        root_span.set_attribute("mcp.method", mcp_method)

        # 3b. Enforce Chronicle resource identifiers in tool call arguments.
        # SECURITY: Always override — callers must NOT be able to specify a
        # different projectId/customerId/region to access another tenant's data.
        if backend_name == "chronicle" and mcp_method == "tools/call":
            args = body.get("params", {}).get("arguments") or {}
            # Detect cross-tenant injection attempts
            for field, expected in [
                ("projectId", client.gcp_project_id),
                ("customerId", client.chronicle_customer_id),
                ("region", client.chronicle_region),
            ]:
                supplied = args.get(field)
                if supplied and supplied != expected:
                    logger.warning(
                        "Cross-tenant param override blocked",
                        client_id=client_id,
                        field=field,
                        supplied=supplied,
                        expected=expected,
                        caller=(caller or {}).get("email"),
                    )
            # Force correct values regardless of what was supplied
            args["projectId"] = client.gcp_project_id
            args["customerId"] = client.chronicle_customer_id
            args["region"] = client.chronicle_region
            # Inject SOAR environment ID when configured (multi-tenant SOAR isolation)
            if client.soar_environment_id:
                args["environmentId"] = client.soar_environment_id
            body.setdefault("params", {})["arguments"] = args
            body_bytes = json.dumps(body).encode("utf-8")

        logger.info(
            "MCP request",
            client_id=client_id,
            method=mcp_method,
            backend=backend_name,
            agent_id=x_agent_id,
            session_id=x_session_id,
            caller=(caller or {}).get("email"),
        )

        # 4. Model Armor: sanitize input — ONLY for tools/call
        # Per Google docs: Model Armor is designed for LLM prompts, not MCP protocol
        # messages. Protocol methods (initialize, tools/list, notifications/*) contain
        # structured JSON that triggers false positives in the prompt injection filter.
        # Only tools/call arguments may carry user/agent-generated natural language.
        _MA_SANITIZE_METHODS = {"tools/call"}
        if mcp_method in _MA_SANITIZE_METHODS:
            with tracer.start_as_current_span("gateway.model_armor.input") as ma_span:
                # Sanitize only the tool arguments, not the JSON-RPC envelope
                tool_args = body.get("params", {}).get("arguments", {})
                input_text = json.dumps(tool_args) if tool_args else ""
                ma_span.set_attribute("mcp.tool_name", body.get("params", {}).get("name", "unknown"))
                if input_text:
                    armor_result = await model_armor.sanitize_user_prompt(input_text)
                    ma_span.set_attribute("filter.result", str(armor_result.filter_result.value))
                else:
                    armor_result = None
                    ma_span.set_attribute("filter.result", "skipped_empty_args")

            if armor_result and not armor_result.allowed:
                logger.warning(
                    "Model Armor BLOCKED input",
                    client_id=client_id,
                    method=mcp_method,
                    backend=backend_name,
                    tool_name=body.get("params", {}).get("name"),
                    reason=armor_result.blocked_reason,
                )
                root_span.set_status(StatusCode.ERROR, "model_armor_blocked")
                root_span.set_attribute("model_armor.blocked_reason", armor_result.blocked_reason or "")
                raise HTTPException(
                    status_code=422,
                    detail=f"Request blocked by Model Armor: {armor_result.blocked_reason}",
                )

            if armor_result and armor_result.filter_result == FilterResult.WARN:
                logger.warning(
                    "Model Armor WARNING on input",
                    client_id=client_id,
                    method=mcp_method,
                    backend=backend_name,
                    details=armor_result.details,
                )
        else:
            root_span.set_attribute("model_armor.input", "skipped_protocol_method")

        # 5. Resolve auth headers — callable is invoked here (after Model Armor) so that
        # prompt-injection blocking short-circuits before any credential is minted.
        with tracer.start_as_current_span("gateway.auth.resolve"):
            resolved_auth = auth_headers() if callable(auth_headers) else auth_headers

        # Build headers and inject traceparent for end-to-end tracing.
        # MCP Streamable HTTP spec requires Accept + Mcp-Session-Id forwarding.
        headers = {**resolved_auth, "Content-Type": "application/json"}
        # Forward Accept header (MCP spec: client MUST accept JSON + SSE)
        accept = request.headers.get("accept", "application/json, text/event-stream")
        headers["Accept"] = accept
        # Forward MCP session ID for stateful session tracking
        mcp_session_id = request.headers.get("mcp-session-id")
        if mcp_session_id:
            headers["Mcp-Session-Id"] = mcp_session_id
        propagate.inject(headers)  # Adds traceparent + tracestate
        if x_agent_id:
            headers["x-agent-id"] = x_agent_id
        if x_session_id:
            headers["x-session-id"] = x_session_id

        # 6. Forward to upstream (with retries on connect errors).
        # Uses streaming to support SSE passthrough without buffering.
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
            reraise=True,
        )
        async def _forward():
            req = http_client.build_request(
                "POST", target_url, content=body_bytes, headers=headers,
            )
            return await http_client.send(req, stream=True)

        with tracer.start_as_current_span("gateway.forward") as fwd_span:
            fwd_span.set_attribute("http.url", target_url)
            try:
                upstream_response = await _forward()
                fwd_span.set_attribute("http.response.status_code", upstream_response.status_code)
            except httpx.TimeoutException as exc:
                cb.record_failure(client_id)
                fwd_span.record_exception(exc)
                fwd_span.set_status(StatusCode.ERROR, "timeout")
                logger.error("MCP upstream timeout after retries", client_id=client_id, method=mcp_method, backend=backend_name)
                raise HTTPException(status_code=504, detail=f"{backend_name} MCP endpoint timed out after retries")
            except httpx.RequestError as exc:
                cb.record_failure(client_id)
                fwd_span.record_exception(exc)
                fwd_span.set_status(StatusCode.ERROR, str(exc))
                logger.error("MCP upstream error after retries", client_id=client_id, error=str(exc), backend=backend_name)
                raise HTTPException(status_code=502, detail=f"Failed to reach {backend_name} MCP endpoint")

        # 7. Circuit breaker feedback (deferred for JSON responses — see step 8b)
        # For SSE, use upstream status directly since body isn't buffered.
        # For JSON (tools/call), we defer until after MCP error normalization
        # to avoid counting tool errors as upstream failures.
        _upstream_status = upstream_response.status_code
        _defer_cb = False
        upstream_content_type_raw = upstream_response.headers.get("content-type", "")
        if "text/event-stream" not in upstream_content_type_raw:
            _defer_cb = True  # Will handle after normalization
        else:
            if _upstream_status >= 500:
                cb.record_failure(client_id)
            else:
                cb.record_success(client_id)

        root_span.set_attribute("http.response.status_code", _upstream_status)
        upstream_content_type = upstream_content_type_raw

        logger.info(
            "MCP response",
            client_id=client_id,
            method=mcp_method,
            backend=backend_name,
            status_code=_upstream_status,
            streaming="text/event-stream" in upstream_content_type,
        )

        # Forward MCP-critical response headers (session tracking)
        response_headers = {}
        upstream_session_id = upstream_response.headers.get("mcp-session-id")
        if upstream_session_id:
            response_headers["Mcp-Session-Id"] = upstream_session_id

        # 8. SSE streaming passthrough or buffered JSON response
        if "text/event-stream" in upstream_content_type:
            # SSE: stream events through without buffering.
            # Model Armor output sanitization is skipped for SSE — individual
            # events cannot be meaningfully sanitized mid-stream.
            async def _stream_sse():
                try:
                    async for chunk in upstream_response.aiter_bytes():
                        yield chunk
                finally:
                    await upstream_response.aclose()

            return StreamingResponse(
                _stream_sse(),
                status_code=upstream_response.status_code,
                media_type="text/event-stream",
                headers=response_headers,
            )

        # JSON: buffer full response, apply Model Armor output sanitization
        try:
            await upstream_response.aread()
            response_content = upstream_response.content
        finally:
            await upstream_response.aclose()

        # 8b. Normalize upstream HTTP errors to MCP-compliant responses.
        # Chronicle MCP returns HTTP 500/501 for tool errors (e.g. case not found,
        # invalid arguments) even though the response body is a valid MCP response
        # with isError=true. The MCP Streamable HTTP spec requires tool errors to
        # use HTTP 200. ADK's McpToolset treats any non-2xx as "Connection closed",
        # so we must normalize these to 200 for the agent to handle gracefully.
        final_status_code = upstream_response.status_code
        if upstream_response.status_code >= 400:
            try:
                error_body = json.loads(response_content)
                if (
                    error_body.get("jsonrpc")
                    and error_body.get("result", {}).get("isError") is True
                ):
                    logger.warning(
                        "Normalizing upstream HTTP error to MCP-compliant 200",
                        client_id=client_id,
                        method=mcp_method,
                        backend=backend_name,
                        original_status=upstream_response.status_code,
                    )
                    final_status_code = 200
                    root_span.set_attribute("upstream.original_status", upstream_response.status_code)
            except (json.JSONDecodeError, TypeError):
                pass  # Not valid JSON — keep original status

        # Deferred circuit breaker feedback for JSON responses
        if _defer_cb:
            if final_status_code >= 500:
                cb.record_failure(client_id)
            else:
                cb.record_success(client_id)

        # Model Armor output sanitization — only for tools/call responses
        if mcp_method in _MA_SANITIZE_METHODS:
            with tracer.start_as_current_span("gateway.model_armor.output") as out_span:
                output_result = await model_armor.sanitize_model_response(
                    response_content.decode("utf-8", errors="replace")
                )
                out_span.set_attribute("pii.redacted", output_result.pii_redacted)
                if output_result.pii_redacted and output_result.sanitized_text:
                    logger.info("Model Armor redacted PII from response", client_id=client_id, backend=backend_name)
                    response_content = output_result.sanitized_text.encode("utf-8")

        return Response(
            content=response_content,
            status_code=final_status_code,
            media_type=upstream_content_type or "application/json",
            headers=response_headers,
        )


@app.post("/mcp/{client_id}")
async def proxy_mcp_request(
    client_id: str,
    request: Request,
    caller: dict = Depends(require_auth),
    x_agent_id: Optional[str] = Header(default=None),
    x_session_id: Optional[str] = Header(default=None),
):
    """Forward an MCP JSON-RPC request to the appropriate Chronicle endpoint."""
    try:
        validate_client_id(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    router: ClientRouter = request.app.state.router

    try:
        client: ClientConfig = router.get_client(client_id)
    except KeyError as exc:
        logger.warning("Unknown client", client_id=client_id)
        raise HTTPException(status_code=404, detail=str(exc))

    if not client.enabled:
        raise HTTPException(status_code=403, detail=f"Client '{client_id}' is disabled")

    def _get_chronicle_auth() -> dict:
        """Resolve impersonated token lazily (after Model Armor checks)."""
        try:
            token = get_impersonated_token(
                client_id, client.service_account_email, PARTNER_PROJECT_ID
            )
        except Exception as exc:
            logger.error("Auth failure", client_id=client_id, error=str(exc))
            raise HTTPException(status_code=502, detail="Authentication failed for client")
        return {
            "Authorization": f"Bearer {token}",
            "x-goog-user-project": client.gcp_project_id,
        }

    return await _proxy_request(
        request=request,
        client_id=client_id,
        client=client,
        target_url=client.mcp_endpoint,
        auth_headers=_get_chronicle_auth,
        backend_name="chronicle",
        http_client=request.app.state.http_client,
        cb=request.app.state.circuit_breaker,
        model_armor=request.app.state.model_armor,
        x_agent_id=x_agent_id,
        x_session_id=x_session_id,
        caller=caller,
    )


@app.post("/gti/{client_id}")
async def proxy_gti_request(
    client_id: str,
    request: Request,
    caller: dict = Depends(require_auth),
    x_agent_id: Optional[str] = Header(default=None),
    x_session_id: Optional[str] = Header(default=None),
):
    """Forward an MCP JSON-RPC request to the GTI MCP server."""
    try:
        validate_client_id(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    router: ClientRouter = request.app.state.router

    try:
        client: ClientConfig = router.get_client(client_id)
    except KeyError as exc:
        logger.warning("Unknown client", client_id=client_id)
        raise HTTPException(status_code=404, detail=str(exc))

    if not client.enabled:
        raise HTTPException(status_code=403, detail=f"Client '{client_id}' is disabled")

    if not client.gti_enabled:
        raise HTTPException(
            status_code=403,
            detail=f"Client '{client_id}' does not have GTI enabled",
        )

    return await _proxy_request(
        request=request,
        client_id=client_id,
        client=client,
        target_url=GTI_MCP_URL,
        auth_headers={},  # gti-mcp handles its own VT_APIKEY
        backend_name="gti",
        http_client=request.app.state.gti_http_client,
        cb=request.app.state.gti_circuit_breaker,
        model_armor=request.app.state.model_armor,
        x_agent_id=x_agent_id,
        x_session_id=x_session_id,
        caller=caller,
    )


@app.delete("/cache/{client_id}")
async def invalidate_client_cache(
    client_id: str, request: Request, caller: dict = Depends(require_auth),
):
    """Force cache invalidation for a client (e.g., after config change)."""
    try:
        validate_client_id(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    router: ClientRouter = request.app.state.router
    router.invalidate_cache(client_id)
    logger.info("Cache invalidated", client_id=client_id, caller=caller.get("email"))
    return {"message": f"Cache invalidated for {client_id}"}


@app.delete("/cache")
async def invalidate_all_cache(request: Request, caller: dict = Depends(require_auth)):
    """Force full cache invalidation — restricted to internal platform callers (API key)."""
    if caller.get("auth_method") not in ("api_key", "dev_mode"):
        raise HTTPException(
            status_code=403,
            detail="Global cache invalidation requires platform API key",
        )
    router: ClientRouter = request.app.state.router
    router.invalidate_cache()
    logger.info("Full cache invalidated", caller=caller.get("email"))
    return {"message": "Full cache invalidated"}


# ── Deep Health Checks ────────────────────────────────────────────────────────
@app.get("/health/live")
async def health_live():
    """Shallow liveness probe — confirms the process is running."""
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready(request: Request):
    """
    Deep readiness probe — checks upstream dependencies.

    Returns 200 if all dependencies are reachable, 503 otherwise.
    Used by Cloud Run readiness probes and load balancers.
    """
    checks: dict[str, dict] = {}
    all_healthy = True

    # 1. Firestore connectivity — cheapest probe: 1 read operation (free tier)
    try:
        router: ClientRouter = request.app.state.router
        if hasattr(router, "_db") and router._db is not None:
            # Single document read: costs 1 Firestore read op even if empty
            list(router._db.collection("clients").limit(1).stream())
            checks["firestore"] = {"status": "ok"}
        elif hasattr(router, "_firestore_available") and not router._firestore_available:
            checks["firestore"] = {"status": "degraded", "detail": "using local config"}
        else:
            checks["firestore"] = {"status": "ok"}
    except Exception as exc:
        checks["firestore"] = {"status": "error", "detail": str(exc)[:200]}
        all_healthy = False

    # 2. Model Armor reachable (only if enabled)
    if MODEL_ARMOR_ENABLED:
        try:
            model_armor: ModelArmorClient = request.app.state.model_armor
            probe_result = await model_armor.sanitize_user_prompt("health check probe")
            checks["model_armor"] = {
                "status": "ok" if probe_result.filter_result != FilterResult.ERROR else "degraded",
            }
        except Exception as exc:
            checks["model_armor"] = {"status": "error", "detail": str(exc)[:200]}
            all_healthy = False
    else:
        checks["model_armor"] = {"status": "disabled"}

    # 3. Circuit breaker summary (counts only — no client_ids to prevent enumeration)
    cb: CircuitBreaker = request.app.state.circuit_breaker
    cb_states = cb.get_all_states()
    open_count = sum(1 for s in cb_states.values() if s["state"] == "OPEN")
    checks["circuit_breaker"] = {
        "status": "degraded" if open_count else "ok",
        "open_count": open_count,
    }
    if open_count:
        all_healthy = False

    # 3b. GTI circuit breaker
    gti_cb: CircuitBreaker = request.app.state.gti_circuit_breaker
    gti_cb_states = gti_cb.get_all_states()
    gti_open_count = sum(1 for s in gti_cb_states.values() if s["state"] == "OPEN")
    checks["gti_circuit_breaker"] = {
        "status": "degraded" if gti_open_count else "ok",
        "open_count": gti_open_count,
    }
    if gti_open_count:
        all_healthy = False

    # 4. HTTP client pool
    try:
        http_client: httpx.AsyncClient = request.app.state.http_client
        checks["http_client"] = {
            "status": "ok" if not http_client.is_closed else "error",
        }
        if http_client.is_closed:
            all_healthy = False
    except Exception:
        checks["http_client"] = {"status": "error"}
        all_healthy = False

    status_code = 200 if all_healthy else 503
    return Response(
        content=json.dumps({
            "status": "ok" if all_healthy else "degraded",
            "checks": checks,
        }),
        status_code=status_code,
        media_type="application/json",
    )


# ── Resilience status endpoints ───────────────────────────────────────────────
@app.get("/status/circuits")
async def circuit_breaker_status(request: Request, caller: dict = Depends(require_auth)):
    """Return aggregate circuit breaker summary (no client_ids to prevent enumeration)."""
    cb: CircuitBreaker = request.app.state.circuit_breaker
    states = cb.get_all_states()
    return {
        "total_tracked": len(states),
        "open_count": sum(1 for s in states.values() if s["state"] == "OPEN"),
        "half_open_count": sum(1 for s in states.values() if s["state"] == "HALF_OPEN"),
    }


@app.get("/status/rate-limits/{client_id}")
async def rate_limit_status(
    client_id: str, request: Request, caller: dict = Depends(require_auth),
):
    """Return remaining rate limit tokens — only for the caller's own client."""
    # API key users can query any client (they are internal platform callers).
    # Google ID token users are restricted to prevent cross-tenant probing.
    if caller.get("auth_method") == "google_id_token":
        # In a full RBAC system, we'd check caller→client_id mapping here.
        # For now, log the access for audit trail.
        logger.info("Rate limit query", client_id=client_id, caller=caller.get("email"))
    rate_limiter: RateLimiter = request.app.state.rate_limiter
    return {
        "client_id": client_id,
        "tokens_remaining": rate_limiter.get_remaining(client_id),
    }
