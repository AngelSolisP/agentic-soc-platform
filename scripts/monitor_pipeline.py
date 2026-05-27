#!/usr/bin/env python3
"""
Pipeline Monitor — Real-time observability for E2E pipeline runs.

Polls Firestore workflow_stages and displays agent progress live in the terminal.
Also checks Cloud Logging for errors related to the pipeline run.

Usage:
    # Monitor a specific case:
    .venv/bin/python3 scripts/monitor_pipeline.py --case-id 2629 --client-id demo-tenant

    # Monitor with Cloud Logging (requires gcloud auth):
    .venv/bin/python3 scripts/monitor_pipeline.py --case-id 2629 --client-id demo-tenant --cloud-logs
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

# ─── Config ───────────────────────────────────────────────────────────────────
PROJECT_ID = os.environ.get("PARTNER_PROJECT_ID", "your-partner-gcp-project")
DATABASE = os.environ.get("FIRESTORE_DATABASE", "(default)")
POLL_INTERVAL = 2.0  # seconds


# ─── Colors ───────────────────────────────────────────────────────────────────
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"


STAGE_ICONS = {
    "pipeline_started": f"{C.CYAN}▶{C.RESET}",
    "triage": f"{C.BLUE}🔍{C.RESET}",
    "enrichment": f"{C.MAGENTA}🔬{C.RESET}",
    "case_manager": f"{C.YELLOW}📋{C.RESET}",
    "response": f"{C.RED}🛡{C.RESET}",
}

STATUS_COLORS = {
    "RUNNING": C.YELLOW,
    "COMPLETED": C.GREEN,
    "ERROR": C.RED,
}


def format_duration(seconds):
    if seconds is None:
        return "..."
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{seconds/60:.1f}m"


def print_header(case_id, client_id):
    print(f"\n{C.BOLD}{'='*70}{C.RESET}")
    print(f"{C.BOLD}  PIPELINE MONITOR — Case {case_id} ({client_id}){C.RESET}")
    print(f"{C.BOLD}{'='*70}{C.RESET}")
    print(f"  {C.DIM}Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}{C.RESET}")
    print(f"  {C.DIM}Polling Firestore every {POLL_INTERVAL}s — Ctrl+C to stop{C.RESET}")
    print(f"{C.BOLD}{'─'*70}{C.RESET}\n")


def print_stage(stage, is_new=True):
    name = stage.get("stage_name", stage.get("agent_name", "unknown"))
    status = stage.get("status", "UNKNOWN")
    duration = stage.get("duration_seconds")
    icon = STAGE_ICONS.get(name, "  ")
    color = STATUS_COLORS.get(status, C.DIM)
    prefix = f"{C.GREEN}NEW{C.RESET} " if is_new else "    "

    print(f"  {prefix}{icon} {C.BOLD}{name:<16}{C.RESET} "
          f"{color}{status:<12}{C.RESET} "
          f"{C.DIM}{format_duration(duration)}{C.RESET}")

    # Show structured output summary
    output = stage.get("output_structured")
    if output and isinstance(output, dict):
        # Triage output
        if "verdict" in output:
            v = output.get("verdict", "?")
            p = output.get("priority", "?")
            conf = output.get("confidence_score", "?")
            print(f"         {C.DIM}verdict={v}  priority={p}  confidence={conf}{C.RESET}")

        # Case Manager output
        if "action_taken" in output:
            action = output.get("action_taken", "?")
            prio = output.get("updated_priority", "?")
            esc = output.get("escalated", False)
            print(f"         {C.DIM}action={action}  priority={prio}  escalated={esc}{C.RESET}")

        # Enrichment output
        if "enrichments" in output:
            enrichments = output.get("enrichments", [])
            print(f"         {C.DIM}{len(enrichments)} IoCs enriched{C.RESET}")
            for e in enrichments[:3]:
                ioc = e.get("ioc_value", "?")[:30]
                verdict = e.get("gti_verdict", e.get("chronicle_verdict", "?"))
                print(f"           {C.DIM}• {ioc} → {verdict}{C.RESET}")

    # Show errors
    error = stage.get("error")
    if error:
        print(f"         {C.RED}ERROR: {error[:100]}{C.RESET}")


def print_summary(stages):
    print(f"\n{C.BOLD}{'─'*70}{C.RESET}")
    completed = [s for s in stages if s.get("status") == "COMPLETED"]
    errors = [s for s in stages if s.get("status") == "ERROR"]
    running = [s for s in stages if s.get("status") == "RUNNING"]
    total_duration = sum(s.get("duration_seconds", 0) for s in stages if s.get("duration_seconds"))

    print(f"  {C.BOLD}SUMMARY{C.RESET}: "
          f"{C.GREEN}{len(completed)} completed{C.RESET}  "
          f"{C.YELLOW}{len(running)} running{C.RESET}  "
          f"{C.RED}{len(errors)} errors{C.RESET}  "
          f"{C.DIM}total: {format_duration(total_duration)}{C.RESET}")

    if errors:
        print(f"\n  {C.RED}{C.BOLD}ERRORS:{C.RESET}")
        for s in errors:
            name = s.get("stage_name", "?")
            err = s.get("error", "unknown")
            print(f"    {C.RED}• {name}: {err[:120]}{C.RESET}")


def fetch_cloud_logs(case_id, client_id, minutes=10):
    """Fetch recent Cloud Logging entries for this pipeline run."""
    try:
        import subprocess
        filter_str = (
            f'resource.type="cloud_run_revision" '
            f'(resource.labels.service_name="agentic-soc-workbench-staging" OR '
            f'resource.labels.service_name="agentic-soc-mcp-gateway-staging") '
            f'(severity>=WARNING OR textPayload:"{case_id}") '
            f'timestamp>="{datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}Z"-{minutes}m'
        )
        result = subprocess.run(
            ["gcloud", "logging", "read", filter_str,
             "--project", PROJECT_ID,
             "--limit", "20",
             "--format", "json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print(f"  {C.DIM}Cloud Logging: {result.stderr.strip()[:100]}{C.RESET}")
            return

        logs = json.loads(result.stdout) if result.stdout.strip() else []
        if not logs:
            print(f"  {C.DIM}Cloud Logging: No warnings/errors in last {minutes}m{C.RESET}")
            return

        print(f"\n  {C.BOLD}CLOUD LOGS{C.RESET} (last {minutes}m, {len(logs)} entries):")
        for entry in logs[:10]:
            ts = entry.get("timestamp", "?")[:19]
            sev = entry.get("severity", "?")
            service = entry.get("resource", {}).get("labels", {}).get("service_name", "?")
            msg = (entry.get("textPayload", "") or
                   json.dumps(entry.get("jsonPayload", {}))[:150])
            sev_color = C.RED if sev in ("ERROR", "CRITICAL") else C.YELLOW if sev == "WARNING" else C.DIM
            print(f"    {C.DIM}{ts}{C.RESET} {sev_color}{sev:8}{C.RESET} "
                  f"{C.DIM}{service.replace('agentic-soc-', '')}{C.RESET}")
            print(f"      {msg[:120]}")

    except Exception as e:
        print(f"  {C.DIM}Cloud Logging unavailable: {e}{C.RESET}")


def monitor(case_id, client_id, cloud_logs=False):
    """Main monitoring loop — polls Firestore for workflow_stages."""
    try:
        from google.cloud import firestore
    except ImportError:
        print("ERROR: google-cloud-firestore not installed. Use: .venv/bin/python3")
        sys.exit(1)

    db = firestore.Client(project=PROJECT_ID, database=DATABASE)
    known_stages = {}
    pipeline_complete = False

    print_header(case_id, client_id)

    try:
        while not pipeline_complete:
            stages = (
                db.collection("workflow_stages")
                .where("case_id", "==", case_id)
                .where("client_id", "==", client_id)
                .order_by("stage_order")
                .stream()
            )

            all_stages = []
            new_updates = False

            for doc in stages:
                stage = doc.to_dict()
                stage_id = stage.get("stage_id", doc.id)
                all_stages.append(stage)

                old = known_stages.get(stage_id)
                if old is None:
                    # New stage appeared
                    print_stage(stage, is_new=True)
                    known_stages[stage_id] = stage
                    new_updates = True
                elif old.get("status") != stage.get("status"):
                    # Status changed (RUNNING → COMPLETED, etc.)
                    print_stage(stage, is_new=False)
                    known_stages[stage_id] = stage
                    new_updates = True

            # Check if pipeline is complete (all 4 agent stages done or error)
            stage_names = {s.get("stage_name") for s in all_stages}
            terminal_statuses = {"COMPLETED", "ERROR"}
            agent_stages = [s for s in all_stages if s.get("stage_name") in
                          {"triage", "enrichment", "case_manager", "response"}]

            if agent_stages:
                all_terminal = all(s.get("status") in terminal_statuses for s in agent_stages)
                has_error = any(s.get("status") == "ERROR" for s in agent_stages)

                # Pipeline is done if we have at least triage + all are terminal
                if all_terminal and len(agent_stages) >= 2:
                    pipeline_complete = True
                elif has_error and all_terminal:
                    pipeline_complete = True

            if not new_updates:
                sys.stdout.write(f"\r  {C.DIM}polling... ({len(known_stages)} stages){C.RESET}")
                sys.stdout.flush()

            if not pipeline_complete:
                time.sleep(POLL_INTERVAL)

        # Pipeline finished
        print_summary(list(known_stages.values()))

        if cloud_logs:
            fetch_cloud_logs(case_id, client_id)

        print(f"\n{C.BOLD}{'='*70}{C.RESET}\n")

    except KeyboardInterrupt:
        print(f"\n\n  {C.DIM}Monitor stopped by user{C.RESET}")
        if known_stages:
            print_summary(list(known_stages.values()))
        if cloud_logs:
            fetch_cloud_logs(case_id, client_id)
        print()


def main():
    parser = argparse.ArgumentParser(description="Monitor Agentic SOC pipeline in real-time")
    parser.add_argument("--case-id", required=True, help="Chronicle SOAR case ID")
    parser.add_argument("--client-id", required=True, help="Client tenant ID (e.g. demo-tenant)")
    parser.add_argument("--cloud-logs", action="store_true", help="Also fetch Cloud Logging entries")
    parser.add_argument("--poll", type=float, default=2.0, help="Poll interval in seconds (default: 2)")
    args = parser.parse_args()

    global POLL_INTERVAL
    POLL_INTERVAL = args.poll

    monitor(args.case_id, args.client_id, cloud_logs=args.cloud_logs)


if __name__ == "__main__":
    main()
