"""
Shared OpenTelemetry tracing configuration.

Initializes a TracerProvider with either:
- ConsoleSpanExporter (default, for local development)
- OTLP exporter to Google Cloud Trace (production)

Usage:
    from observability.tracing import init_tracing, get_tracer

    init_tracing("agentic-soc-gateway")
    tracer = get_tracer("agentic_soc.gateway")

    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("client.id", client_id)
"""

import logging
import os
import signal
import sys
import threading

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagators.composite import CompositePropagator

logger = logging.getLogger(__name__)

_initialized = False
_init_lock = threading.Lock()
_shutdown_done = False


def init_tracing(service_name: str = "agentic-soc") -> None:
    """Initialize the global TracerProvider.

    Reads OTEL_EXPORTER_TYPE env var:
        "console" (default) — prints spans to stdout as JSON
        "cloud"             — sends spans to Google Cloud Trace via OTLP

    Calling this multiple times is safe (no-op after first call).
    """
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return

        resource_attrs = {
            SERVICE_NAME: service_name,
            "deployment.environment": os.environ.get("ENVIRONMENT", "local"),
        }
        # telemetry.googleapis.com requires gcp.project_id to route spans
        # GOOGLE_CLOUD_PROJECT: auto-injected by Agent Engine
        # PARTNER_PROJECT_ID: set on Cloud Run Gateway/HITL
        gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PARTNER_PROJECT_ID", "")
        if gcp_project:
            resource_attrs["gcp.project_id"] = gcp_project
        resource = Resource.create(resource_attrs)

        provider = TracerProvider(resource=resource)

        exporter_type = os.environ.get("OTEL_EXPORTER_TYPE", "console")
        if exporter_type == "cloud":
            try:
                exporter = _create_cloud_exporter()
                logger.info("OTel: Cloud Trace exporter (OTLP → telemetry.googleapis.com)")
            except Exception:
                logger.warning("OTel: Cloud exporter failed, falling back to console", exc_info=True)
                exporter = ConsoleSpanExporter()
        else:
            exporter = ConsoleSpanExporter()
            logger.info("OTel: Console exporter (stdout)")

        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        set_global_textmap(CompositePropagator([
            TraceContextTextMapPropagator(),
            W3CBaggagePropagator(),
        ]))
        logger.info("OTel: W3C TraceContext propagator configured")
        _initialized = True


def _create_cloud_exporter():
    """Create an OTLP gRPC exporter authenticated to Google Cloud Trace."""
    import google.auth
    import google.auth.transport.requests
    from google.auth.transport.grpc import AuthMetadataPlugin
    import grpc
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    credentials, project_id = google.auth.default()
    request = google.auth.transport.requests.Request()
    auth_plugin = AuthMetadataPlugin(credentials=credentials, request=request)

    channel_creds = grpc.composite_channel_credentials(
        grpc.ssl_channel_credentials(),
        grpc.metadata_call_credentials(auth_plugin),
    )

    # Do NOT set x-goog-user-project header explicitly — with service account
    # auth on Cloud Run, the quota project is automatic. Setting it manually
    # creates duplicates that cause API failures (per Google migration guide).
    return OTLPSpanExporter(
        endpoint="telemetry.googleapis.com:443",
        credentials=channel_creds,
    )


def get_tracer(name: str) -> trace.Tracer:
    """Return a named Tracer from the global TracerProvider."""
    return trace.get_tracer(name)


def get_current_trace_id() -> str | None:
    """Return the current trace ID as a 32-char hex string, or None if not in a span."""
    ctx = trace.get_current_span().get_span_context()
    if not ctx.is_valid:
        return None
    return format(ctx.trace_id, "032x")


def shutdown_tracing(timeout_millis: int = 5000) -> None:
    """Flush and shut down the TracerProvider.

    Must be called on graceful shutdown to avoid losing buffered spans.
    OTel BatchSpanProcessor buffers spans in memory — without explicit
    flush+shutdown, spans are lost when Cloud Run sends SIGTERM.

    Safe to call multiple times (no-op after first call).

    Args:
        timeout_millis: Max time to wait for span export (default 5s,
            leaves headroom before Cloud Run's 10s SIGKILL).
    """
    global _shutdown_done
    if _shutdown_done:
        return
    _shutdown_done = True
    provider = trace.get_tracer_provider()
    if hasattr(provider, "force_flush"):
        try:
            provider.force_flush(timeout_millis=timeout_millis)
        except Exception:
            logger.warning("OTel force_flush failed", exc_info=True)
    if hasattr(provider, "shutdown"):
        try:
            provider.shutdown()
        except Exception:
            logger.warning("OTel shutdown failed", exc_info=True)
    logger.info("OTel: TracerProvider shut down")


def _sigterm_handler(signum, frame):
    """Handle SIGTERM from Cloud Run scale-down.

    Python atexit handlers do NOT run on SIGTERM. This handler ensures
    buffered OTel spans are exported before the process exits.
    Cloud Run gives 10s after SIGTERM before SIGKILL.
    """
    shutdown_tracing()
    sys.exit(0)


def register_sigterm_handler() -> None:
    """Register SIGTERM handler for Cloud Run graceful shutdown.

    Call this once during application startup (e.g., in FastAPI lifespan).
    """
    signal.signal(signal.SIGTERM, _sigterm_handler)
