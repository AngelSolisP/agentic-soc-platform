#!/usr/bin/env python3
"""
Client Onboarding Script

Registers a new MSSP client in the Agentic SOC platform:
1. Validates the client YAML config
2. Tests connectivity to the client's Chronicle MCP endpoint
3. Stores config in Firestore
4. Stores client SA email in Secret Manager

Usage:
    python scripts/onboard_client.py --config config/clients/acme-corp.yaml
    python scripts/onboard_client.py --config config/clients/acme-corp.yaml --dry-run
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


REQUIRED_FIELDS = [
    "client_id",
    "display_name",
    "gcp_project_id",
    "chronicle_customer_id",
    "service_account_email",
]


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config


def validate_config(config: dict) -> list[str]:
    """Return list of validation errors."""
    errors = []
    for field in REQUIRED_FIELDS:
        if not config.get(field) or config[field].startswith("REPLACE_ME"):
            errors.append(f"Missing or placeholder value for: {field}")

    client_id = config.get("client_id", "")
    if not client_id.replace("-", "").replace("_", "").isalnum():
        errors.append(f"client_id must be alphanumeric with hyphens/underscores: '{client_id}'")

    return errors


def test_mcp_connectivity(config: dict, gateway_url: str) -> bool:
    """Test that the MCP Gateway can route to this client's Chronicle."""
    import httpx

    mcp_url = f"{gateway_url}/mcp/{config['client_id']}"
    try:
        r = httpx.post(
            mcp_url,
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            timeout=30,
        )
        if r.status_code == 200:
            logger.info("✅ MCP connectivity test passed")
            return True
        logger.warning(f"⚠️  MCP test returned status {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        logger.warning(f"⚠️  MCP connectivity test failed: {e}")
        return False


def store_in_firestore(config: dict, partner_project_id: str) -> None:
    from google.cloud import firestore

    db = firestore.Client(project=partner_project_id)
    now = datetime.now(timezone.utc).isoformat()
    doc_data = {
        "client_id": config["client_id"],
        "display_name": config["display_name"],
        "gcp_project_id": config["gcp_project_id"],
        "chronicle_customer_id": config["chronicle_customer_id"],
        "chronicle_region": config.get("chronicle_region", "us"),
        "service_account_email": config["service_account_email"],
        "enabled": config.get("enabled", True),
        "autonomous_mode": config.get("autonomous_mode", False),
        "extra": config.get("extra", {}),
        "onboarded_at": now,
        "onboarded_by": os.environ.get("USER", "script"),
    }
    db.collection("clients").document(config["client_id"]).set(doc_data)
    logger.info(f"✅ Client '{config['client_id']}' stored in Firestore")


def store_sa_in_secret_manager(
    client_id: str,
    sa_email: str,
    partner_project_id: str,
    secret_prefix: str = "agentic-soc",
) -> None:
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    secret_id = f"{secret_prefix}-{client_id}-sa-email"
    parent = f"projects/{partner_project_id}"
    secret_path = f"{parent}/secrets/{secret_id}"

    # Create secret if it doesn't exist
    try:
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        logger.info(f"✅ Secret '{secret_id}' created")
    except Exception:
        logger.info(f"  Secret '{secret_id}' already exists, adding new version")

    # Add version with SA email
    client.add_secret_version(
        request={
            "parent": secret_path,
            "payload": {"data": sa_email.encode()},
        }
    )
    logger.info(f"✅ SA email stored in Secret Manager as '{secret_id}'")


def main():
    parser = argparse.ArgumentParser(description="Onboard a new MSSP client")
    parser.add_argument("--config", required=True, help="Path to client YAML config")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no writes")
    parser.add_argument(
        "--gateway-url",
        default=os.environ.get("MCP_GATEWAY_URL", ""),
        help="MCP Gateway URL for connectivity test",
    )
    parser.add_argument(
        "--partner-project",
        default=os.environ.get("PARTNER_PROJECT_ID", ""),
        help="Partner GCP project ID",
    )
    parser.add_argument(
        "--skip-connectivity",
        action="store_true",
        help="Skip MCP connectivity test",
    )
    args = parser.parse_args()

    if not args.partner_project:
        logger.error("PARTNER_PROJECT_ID env var or --partner-project required")
        sys.exit(1)

    # 1. Load and validate config
    logger.info(f"Loading config from: {args.config}")
    config = load_config(args.config)

    errors = validate_config(config)
    if errors:
        logger.error("Config validation failed:")
        for err in errors:
            logger.error(f"  - {err}")
        sys.exit(1)

    logger.info(f"✅ Config valid for client: {config['client_id']}")

    if args.dry_run:
        logger.info("DRY RUN — no changes will be made")
        logger.info(json.dumps(config, indent=2))
        return

    # 2. Test connectivity (optional)
    if not args.skip_connectivity and args.gateway_url:
        test_mcp_connectivity(config, args.gateway_url)
    elif not args.gateway_url:
        logger.warning("Skipping connectivity test: no --gateway-url provided")

    # 3. Store in Firestore
    store_in_firestore(config, args.partner_project)

    # 4. Store SA email in Secret Manager
    store_sa_in_secret_manager(
        client_id=config["client_id"],
        sa_email=config["service_account_email"],
        partner_project_id=args.partner_project,
    )

    logger.info(f"🎉 Client '{config['client_id']}' onboarded successfully!")
    logger.info(
        f"   Chronicle MCP endpoint: "
        f"https://chronicle.{config.get('chronicle_region', 'us')}.rep.googleapis.com/mcp"
        f"?customer_id={config['chronicle_customer_id']}"
    )


if __name__ == "__main__":
    main()
