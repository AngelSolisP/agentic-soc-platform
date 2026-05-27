#!/usr/bin/env python3
"""
Deploy Agentic SOC Orchestrator to Vertex AI Agent Engine.

Uses the modern vertexai.agent_engines API to deploy a custom AgenticSOCApp
that wraps the full multi-agent orchestrator for cloud-native serving.

Prerequisites:
    - gcloud auth login
    - PARTNER_PROJECT_ID set
    - MCP Gateway deployed and accessible on Cloud Run

Usage:
    # Fresh deploy
    python scripts/deploy_agent.py --project my-project --gateway-url https://gw.run.app

    # Dry run (validate only — no GCP calls)
    python scripts/deploy_agent.py --project my-project --dry-run

    # Update existing deployment
    python scripts/deploy_agent.py --project my-project --update --resource-id RESOURCE_ID

    # Rollback to previous version
    python scripts/deploy_agent.py --project my-project --rollback --resource-id RESOURCE_ID
"""

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Requirements sent to Agent Engine runtime
AGENT_ENGINE_REQUIREMENTS = [
    "google-cloud-aiplatform[adk,agent_engines]",
    "google-adk[a2a]>=1.27.4",
    "google-auth>=2.28.0",
    "httpx>=0.27.0",
    "pyyaml>=6.0.1",
    "google-cloud-firestore>=2.16.0",
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp-proto-grpc>=1.20.0",
    "structlog>=24.2.0",
    "mcp>=1.3.0",
]

# Source code packages to bundle
EXTRA_PACKAGES = [
    "agents/",
    "runbooks/",
    "config/",
    "observability/",
]

def build_memory_bank_config(project_id: str, region: str) -> dict:
    """Build Memory Bank config with full model resource paths.

    Model format required by API:
        projects/{project}/locations/{location}/publishers/google/models/{model}
    """
    model_prefix = f"projects/{project_id}/locations/{region}/publishers/google/models"
    return {
        "generation_config": {
            "model": f"{model_prefix}/gemini-2.5-flash",
        },
        "similarity_search_config": {
            "embedding_model": f"{model_prefix}/text-embedding-005",
        },
        "ttl_config": {
            "granular_ttl_config": {
                "create_ttl": "7776000s",            # 90 days
                "generate_created_ttl": "7776000s",   # 90 days
                "generate_updated_ttl": "15552000s",  # 180 days (consolidated)
            },
        },
        "customization_configs": [
            {
                "memory_topics": [
                    {
                        "custom_memory_topic": {
                            "label": "alert_patterns",
                            "description": (
                                "Recurring alert patterns, known false positives, "
                                "common attack vectors for this client"
                            ),
                        }
                    },
                    {
                        "custom_memory_topic": {
                            "label": "case_outcomes",
                            "description": (
                                "Past case dispositions, triage verdicts, enrichment "
                                "findings, containment actions taken"
                            ),
                        }
                    },
                    {
                        "custom_memory_topic": {
                            "label": "analyst_preferences",
                            "description": (
                                "Analyst escalation preferences, SLA thresholds, "
                                "notification channels, custom procedures"
                            ),
                        }
                    },
                ]
            }
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Deploy Agentic SOC to Vertex AI Agent Engine"
    )
    parser.add_argument(
        "--project",
        default=os.environ.get("PARTNER_PROJECT_ID", ""),
        help="GCP project ID (or PARTNER_PROJECT_ID env)",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("PARTNER_REGION", "us-central1"),
        help="GCP region (default: us-central1)",
    )
    parser.add_argument(
        "--gateway-url",
        default=os.environ.get("MCP_GATEWAY_URL", ""),
        help="MCP Gateway Cloud Run URL (or MCP_GATEWAY_URL env)",
    )
    parser.add_argument(
        "--gti-url",
        default=os.environ.get("GTI_GATEWAY_URL", ""),
        help="GTI Gateway URL (or GTI_GATEWAY_URL env)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("GEMINI_PRO_MODEL", "gemini-2.5-pro"),
        help="Gemini model for the orchestrator",
    )
    parser.add_argument(
        "--display-name",
        default="Agentic SOC Orchestrator",
        help="Display name for the Agent Engine resource",
    )
    parser.add_argument(
        "--resource-id",
        default=None,
        help="Existing Agent Engine resource ID (for --update/--rollback)",
    )
    parser.add_argument(
        "--update", action="store_true",
        help="Update existing deployment (requires --resource-id)",
    )
    parser.add_argument(
        "--rollback", action="store_true",
        help="Rollback to previous version (requires --resource-id)",
    )
    parser.add_argument(
        "--staging-bucket",
        default=os.environ.get("VERTEX_STAGING_BUCKET", ""),
        help="GCS bucket for Vertex AI staging (or VERTEX_STAGING_BUCKET env). "
             "Auto-derived from project ID if not set.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate agent construction only, no GCP calls",
    )
    return parser


def validate_args(args) -> list[str]:
    """Validate parsed arguments. Returns list of error messages (empty = valid)."""
    errors = []
    if not args.project:
        errors.append("--project or PARTNER_PROJECT_ID required")
    if not args.gateway_url and not args.dry_run:
        errors.append("--gateway-url or MCP_GATEWAY_URL required for deployment")
    if args.update and not args.resource_id:
        errors.append("--resource-id required when using --update")
    if args.rollback and not args.resource_id:
        errors.append("--resource-id required when using --rollback")
    return errors


def build_env_vars(
    project_id: str,
    gateway_url: str,
    model: str,
    gti_url: str = "",
) -> dict[str, str]:
    """Build environment variables dict for Agent Engine deployment."""
    env = {
        "PARTNER_PROJECT_ID": project_id,
        "MCP_GATEWAY_URL": gateway_url,
        "GEMINI_PRO_MODEL": model,
        "OTEL_EXPORTER_TYPE": "cloud",
        # ADK/genai backend: use Vertex AI (SA auth), not AI Studio (API key).
        # GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are auto-injected by Agent Engine.
        "GOOGLE_GENAI_USE_VERTEXAI": "true",
        # Cost protection: cap LLM calls per pipeline and timeout
        "MAX_LLM_CALLS_PER_PIPELINE": "25",
        "AGENT_TIMEOUT_SECONDS": "120",
    }
    if gti_url:
        env["GTI_GATEWAY_URL"] = gti_url
    return env


def do_dry_run() -> bool:
    """Validate AgenticSOCApp construction without deploying."""
    from agents.orchestrator.deployed_app import AgenticSOCApp

    logger.info("DRY RUN — validating AgenticSOCApp construction")
    app = AgenticSOCApp()
    app.set_up()
    logger.info("Orchestrator created successfully")

    health = app.health_check()
    logger.info("Health check: %s", health)

    if health["status"] != "healthy":
        logger.error("Health check failed after set_up()")
        return False

    logger.info("Validation passed. Run without --dry-run to deploy.")
    return True


def deploy_new(
    project_id: str,
    region: str,
    display_name: str,
    env_vars: dict[str, str],
    staging_bucket: str = "",
) -> str:
    """Create a new Agent Engine deployment. Returns resource name.

    Uses vertexai.Client() API (v1beta1) which supports context_spec
    for Memory Bank configuration.
    """
    import vertexai
    from agents.orchestrator.deployed_app import AgenticSOCApp

    client = vertexai.Client(project=project_id, location=region)

    app = AgenticSOCApp()
    memory_bank_config = build_memory_bank_config(project_id, region)

    config = {
        "display_name": display_name,
        "requirements": AGENT_ENGINE_REQUIREMENTS,
        "extra_packages": EXTRA_PACKAGES,
        "env_vars": env_vars,
        "context_spec": {
            "memory_bank_config": memory_bank_config,
        },
    }
    if staging_bucket:
        config["staging_bucket"] = staging_bucket

    logger.info("Creating new Agent Engine deployment...")
    engine = client.agent_engines.create(agent=app, config=config)

    resource_name = engine.api_resource.name
    resource_id = resource_name.split("/")[-1]
    logger.info("Agent Engine deployed: %s", resource_name)
    logger.info("Resource ID: %s", resource_id)
    logger.info("Save this Resource ID for future --update / --rollback.")
    return resource_name


def deploy_update(
    project_id: str,
    region: str,
    resource_id: str,
    display_name: str,
    env_vars: dict[str, str],
    staging_bucket: str = "",
) -> str:
    """Update an existing Agent Engine deployment. Returns resource name.

    Uses vertexai.Client() API (v1beta1) which supports context_spec
    for Memory Bank configuration.
    """
    import vertexai
    from agents.orchestrator.deployed_app import AgenticSOCApp

    client = vertexai.Client(project=project_id, location=region)

    app = AgenticSOCApp()
    memory_bank_config = build_memory_bank_config(project_id, region)

    config = {
        "display_name": display_name,
        "requirements": AGENT_ENGINE_REQUIREMENTS,
        "extra_packages": EXTRA_PACKAGES,
        "env_vars": env_vars,
        "context_spec": {
            "memory_bank_config": memory_bank_config,
        },
    }
    if staging_bucket:
        config["staging_bucket"] = staging_bucket

    # Build full resource name if only numeric ID was provided
    if resource_id.isdigit():
        full_name = f"projects/{project_id}/locations/{region}/reasoningEngines/{resource_id}"
    else:
        full_name = resource_id

    logger.info("Updating Agent Engine deployment: %s", full_name)
    engine = client.agent_engines.update(name=full_name, agent=app, config=config)

    logger.info("Agent Engine updated: %s", engine.api_resource.name)
    return engine.api_resource.name


def deploy_rollback(
    project_id: str,
    region: str,
    resource_id: str,
) -> None:
    """Rollback an Agent Engine deployment to its previous version."""
    import vertexai

    client = vertexai.Client(project=project_id, location=region)

    if resource_id.isdigit():
        full_name = f"projects/{project_id}/locations/{region}/reasoningEngines/{resource_id}"
    else:
        full_name = resource_id

    logger.info("Rolling back Agent Engine: %s", full_name)
    client.agent_engines.delete(name=full_name)
    logger.info("Agent Engine deleted: %s. Redeploy previous version.", full_name)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    errors = validate_args(args)
    if errors:
        for err in errors:
            logger.error(err)
        sys.exit(1)

    # Auto-derive staging bucket from project ID if not provided
    staging_bucket = args.staging_bucket
    if not staging_bucket and not args.dry_run:
        staging_bucket = f"gs://{args.project}-vertex-staging"
        logger.info("Auto-derived staging bucket: %s", staging_bucket)

    logger.info("Project:     %s", args.project)
    logger.info("Region:      %s", args.region)
    logger.info("Gateway:     %s", args.gateway_url or "(dry-run)")
    logger.info("Model:       %s", args.model)
    logger.info("Display:     %s", args.display_name)
    logger.info("Staging:     %s", staging_bucket or "(dry-run)")

    if args.dry_run:
        success = do_dry_run()
        sys.exit(0 if success else 1)

    env_vars = build_env_vars(
        project_id=args.project,
        gateway_url=args.gateway_url,
        model=args.model,
        gti_url=args.gti_url,
    )

    if args.rollback:
        deploy_rollback(
            project_id=args.project,
            region=args.region,
            resource_id=args.resource_id,
        )
    elif args.update:
        deploy_update(
            project_id=args.project,
            region=args.region,
            resource_id=args.resource_id,
            display_name=args.display_name,
            env_vars=env_vars,
            staging_bucket=staging_bucket,
        )
    else:
        deploy_new(
            project_id=args.project,
            region=args.region,
            display_name=args.display_name,
            env_vars=env_vars,
            staging_bucket=staging_bucket,
        )


if __name__ == "__main__":
    main()
