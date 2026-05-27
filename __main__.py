#!/usr/bin/env python3
"""
Agentic SOC — MSSP Platform CLI.

Usage:
    python -m agentic-soc process \
        --client-id nfr-partner-client \
        --case-id CASE-001 \
        --alert-type PHISHING

    python -m agentic-soc serve
        # Starts MCP Gateway + HITL backend locally

    python -m agentic-soc deploy --project my-project --gateway-url https://gw.run.app
        # Deploy to Vertex AI Agent Engine
"""

import argparse
import asyncio
import logging
import os
import sys
import json
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("agentic-soc")


def cmd_process(args):
    """Process a single alert through the full orchestrator pipeline."""
    from agents.orchestrator.agent import AgenticSOCOrchestrator

    partner_project = args.partner_project or os.environ.get("PARTNER_PROJECT_ID", "")
    if not partner_project:
        logger.error("PARTNER_PROJECT_ID env var or --partner-project required")
        sys.exit(1)

    orchestrator = AgenticSOCOrchestrator(
        partner_project_id=partner_project,
        gateway_url=args.gateway_url or os.environ.get("MCP_GATEWAY_URL"),
    )

    raw_alert = None
    if args.raw_alert_file:
        with open(args.raw_alert_file) as f:
            raw_alert = json.load(f)

    result = asyncio.run(
        orchestrator.process_alert(
            client_id=args.client_id,
            case_id=args.case_id,
            alert_type=args.alert_type,
            severity=args.severity,
            trigger=args.trigger,
            raw_alert=raw_alert,
            autonomous_mode=args.autonomous,
        )
    )

    print("\n=== Orchestrator Result ===")
    print(json.dumps(result, indent=2, default=str))


def cmd_serve(args):
    """Start the MCP Gateway and HITL backend locally."""
    import subprocess

    processes = []
    gateway_port = args.gateway_port or int(os.environ.get("MCP_GATEWAY_PORT", "8080"))
    hitl_port = args.hitl_port or int(os.environ.get("HITL_BACKEND_PORT", "8081"))

    logger.info(f"Starting MCP Gateway on port {gateway_port}")
    processes.append(subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "proxy.mcp_gateway.main:app",
        "--host", "0.0.0.0", "--port", str(gateway_port), "--reload",
    ]))

    logger.info(f"Starting HITL Backend on port {hitl_port}")
    processes.append(subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "ui.hitl_dashboard.backend.main:app",
        "--host", "0.0.0.0", "--port", str(hitl_port), "--reload",
    ]))

    a2a_port = args.a2a_port or int(os.environ.get("A2A_GATEWAY_PORT", "8082"))
    logger.info(f"Starting A2A Gateway on port {a2a_port}")
    processes.append(subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "a2a_gateway.main:app",
        "--host", "0.0.0.0", "--port", str(a2a_port), "--reload",
    ]))

    workbench_port = args.workbench_port or int(os.environ.get("WORKBENCH_PORT", "8083"))
    logger.info(f"Starting Workbench on port {workbench_port}")
    processes.append(subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "workbench.backend.main:app",
        "--host", "0.0.0.0", "--port", str(workbench_port), "--reload",
    ]))

    logger.info(
        f"Services running:\n"
        f"  MCP Gateway:    http://localhost:{gateway_port}\n"
        f"  HITL Dashboard: http://localhost:{hitl_port}\n"
        f"  A2A Gateway:    http://localhost:{a2a_port}\n"
        f"  Workbench:     http://localhost:{workbench_port}\n"
        f"Press Ctrl+C to stop."
    )

    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        for p in processes:
            p.terminate()


def cmd_deploy(args):
    """Deploy the orchestrator to Vertex AI Agent Engine."""
    from scripts.deploy_agent import main as deploy_main, validate_args

    errors = validate_args(args)
    if errors:
        for err in errors:
            logger.error(err)
        sys.exit(1)

    # Build argv list from parsed args to pass to deploy script
    argv = ["--project", args.project, "--region", args.region]
    if args.gateway_url:
        argv += ["--gateway-url", args.gateway_url]
    if args.gti_url:
        argv += ["--gti-url", args.gti_url]
    argv += ["--model", args.model, "--display-name", args.display_name]
    if args.resource_id:
        argv += ["--resource-id", args.resource_id]
    if args.update:
        argv.append("--update")
    if args.rollback:
        argv.append("--rollback")
    if args.dry_run:
        argv.append("--dry-run")

    deploy_main(argv)


def main():
    parser = argparse.ArgumentParser(
        prog="agentic-soc",
        description="Agentic SOC — MSSP Platform CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # process command
    proc = subparsers.add_parser("process", help="Process a single alert")
    proc.add_argument("--client-id", required=True)
    proc.add_argument("--case-id", required=True)
    proc.add_argument("--alert-type", required=True)
    proc.add_argument("--severity", default="MEDIUM")
    proc.add_argument("--trigger", default="RULE_DETECTION")
    proc.add_argument("--autonomous", action="store_true")
    proc.add_argument("--raw-alert-file", help="Path to JSON file with raw alert data")
    proc.add_argument("--gateway-url")
    proc.add_argument("--partner-project")
    proc.set_defaults(func=cmd_process)

    # serve command
    srv = subparsers.add_parser("serve", help="Start local dev services")
    srv.add_argument("--gateway-port", type=int)
    srv.add_argument("--hitl-port", type=int)
    srv.add_argument("--a2a-port", type=int)
    srv.add_argument("--workbench-port", type=int, help="Workbench port (default: 8083)")
    srv.set_defaults(func=cmd_serve)

    # deploy command
    dep = subparsers.add_parser("deploy", help="Deploy to Vertex AI Agent Engine")
    dep.add_argument("--project", default=os.environ.get("PARTNER_PROJECT_ID", ""))
    dep.add_argument("--region", default=os.environ.get("PARTNER_REGION", "us-central1"))
    dep.add_argument("--gateway-url", default=os.environ.get("MCP_GATEWAY_URL", ""))
    dep.add_argument("--gti-url", default=os.environ.get("GTI_GATEWAY_URL", ""))
    dep.add_argument("--model", default=os.environ.get("GEMINI_PRO_MODEL", "gemini-2.5-pro"))
    dep.add_argument("--display-name", default="Agentic SOC Orchestrator")
    dep.add_argument("--resource-id", default=None)
    dep.add_argument("--update", action="store_true")
    dep.add_argument("--rollback", action="store_true")
    dep.add_argument("--dry-run", action="store_true")
    dep.set_defaults(func=cmd_deploy)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
