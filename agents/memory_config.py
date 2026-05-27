"""
Memory Service Factory — Vertex AI Memory Bank integration.

Production: VertexAiMemoryBankService (persistent, semantic search).
Local dev:  InMemoryMemoryService (keyword matching, no persistence).

Detection: GOOGLE_CLOUD_AGENT_ENGINE_ID is auto-injected by Agent Engine.
Fallback:  AGENT_ENGINE_ID env var for manual configuration.
"""

import logging
import os

logger = logging.getLogger(__name__)


def create_memory_service():
    """Create memory service: VertexAiMemoryBankService for production, InMemory for local dev."""
    agent_engine_id = os.environ.get(
        "GOOGLE_CLOUD_AGENT_ENGINE_ID"
    ) or os.environ.get("AGENT_ENGINE_ID")

    if agent_engine_id:
        try:
            from google.adk.memory import VertexAiMemoryBankService

            project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

            if not project:
                logger.warning(
                    "Agent Engine ID set but GOOGLE_CLOUD_PROJECT missing, "
                    "falling back to InMemoryMemoryService"
                )
                from google.adk.memory import InMemoryMemoryService
                return InMemoryMemoryService()

            logger.info(
                "Using VertexAiMemoryBankService",
                extra={
                    "project": project,
                    "location": location,
                    "agent_engine_id": agent_engine_id,
                },
            )
            return VertexAiMemoryBankService(
                project=project,
                location=location,
                agent_engine_id=agent_engine_id,
            )
        except Exception as e:
            logger.warning(
                "VertexAiMemoryBankService init failed, falling back to InMemory: %s", e
            )
            from google.adk.memory import InMemoryMemoryService
            return InMemoryMemoryService()

    from google.adk.memory import InMemoryMemoryService
    return InMemoryMemoryService()
