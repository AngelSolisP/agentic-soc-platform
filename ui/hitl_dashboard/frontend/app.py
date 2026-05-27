"""
HITL Dashboard — Streamlit Frontend

Analyst interface for reviewing and approving/rejecting AI agent
proposed actions. Connects to the HITL Dashboard Backend API.
"""

import os
import json
import requests
import streamlit as st
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
BACKEND_URL = os.environ.get("HITL_BACKEND_URL", "http://localhost:8081")
AUTO_REFRESH_SECONDS = int(os.environ.get("HITL_REFRESH_SECONDS", "30"))
# Auth token for backend API calls (identity token or API key)
_AUTH_TOKEN = os.environ.get("HITL_AUTH_TOKEN", "")


def _auth_headers() -> dict:
    """Build Authorization header for backend API calls."""
    if _AUTH_TOKEN:
        return {"Authorization": f"Bearer {_AUTH_TOKEN}"}
    return {}

st.set_page_config(
    page_title="Agentic SOC — HITL Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fetch_approvals(status: str = "PENDING", client_id: str = "") -> list:
    params = {"status": status}
    if client_id:
        params["client_id"] = client_id
    try:
        r = requests.get(f"{BACKEND_URL}/approvals", params=params, headers=_auth_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to fetch approvals: {e}")
        return []


def fetch_stats() -> dict:
    try:
        r = requests.get(f"{BACKEND_URL}/stats", headers=_auth_headers(), timeout=5)
        r.raise_for_status()
        return r.json().get("stats", {})
    except Exception:
        return {}


def submit_decision(
    approval_id: str,
    decision: str,
    analyst_id: str,
    notes: str = "",
    modified_params: dict = None,
):
    payload = {
        "decision": decision,
        "analyst_id": analyst_id,
        "analyst_notes": notes,
    }
    if modified_params:
        payload["modified_parameters"] = modified_params
    try:
        r = requests.post(
            f"{BACKEND_URL}/approvals/{approval_id}/decide",
            json=payload,
            headers=_auth_headers(),
            timeout=10,
        )
        r.raise_for_status()
        return True, r.json().get("message", "Decision recorded.")
    except Exception as e:
        return False, str(e)


def format_dt(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso_str or "—"


def severity_badge(action: dict) -> str:
    action_name = action.get("proposed_action", "")
    high_risk = ["isolate_endpoint", "disable_user", "block_ip"]
    if action_name in high_risk:
        return "🔴 HIGH IMPACT"
    return "🟡 MEDIUM IMPACT"


def fetch_pipeline_by_session(session_id: str) -> list:
    try:
        r = requests.get(f"{BACKEND_URL}/pipeline/session/{session_id}", headers=_auth_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def fetch_pipeline_by_case(case_id: str, client_id: str = "") -> list:
    params = {}
    if client_id:
        params["client_id"] = client_id
    try:
        r = requests.get(f"{BACKEND_URL}/pipeline/case/{case_id}", params=params, headers=_auth_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def fetch_recent_pipelines(client_id: str = "") -> list:
    params = {}
    if client_id:
        params["client_id"] = client_id
    try:
        r = requests.get(f"{BACKEND_URL}/pipeline/recent", params=params, headers=_auth_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def render_pipeline(stages: list):
    """Render a workflow pipeline as a visual stage sequence."""
    if not stages:
        st.info("No pipeline stages recorded for this workflow.")
        return

    # Pipeline header: Triage → Enrichment → Case Manager → Response
    stage_names = ["triage", "enrichment", "case_manager", "response"]
    stage_labels = {
        "triage": "Triage",
        "enrichment": "Enrichment",
        "case_manager": "Case Manager",
        "response": "Response",
    }
    stage_status = {s["agent_name"]: s for s in stages}

    # Visual pipeline bar
    cols = st.columns(len(stage_names))
    for i, name in enumerate(stage_names):
        stage = stage_status.get(name)
        with cols[i]:
            if stage is None:
                st.markdown(f"**{stage_labels[name]}**")
                st.caption("⚪ Not executed")
            elif stage["status"] == "COMPLETED":
                dur = stage.get("duration_seconds", 0)
                st.markdown(f"**{stage_labels[name]}**")
                st.caption(f"🟢 {dur}s")
            elif stage["status"] == "FAILED":
                st.markdown(f"**{stage_labels[name]}**")
                st.caption("🔴 Failed")
            elif stage["status"] == "SKIPPED":
                st.markdown(f"**{stage_labels[name]}**")
                st.caption("⏭️ Skipped")
            else:
                st.markdown(f"**{stage_labels[name]}**")
                st.caption("🟠 In progress")

    st.divider()

    # Expandable details per stage
    for stage in stages:
        label = stage_labels.get(stage["agent_name"], stage["agent_name"])
        status_icon = {"COMPLETED": "🟢", "FAILED": "🔴", "SKIPPED": "⏭️"}.get(
            stage["status"], "🟠"
        )
        dur = stage.get("duration_seconds", "—")
        header = f"{status_icon} {label} | {dur}s | {stage.get('started_at', '')[:19]}"

        with st.expander(header, expanded=(stage["status"] == "FAILED")):
            tab_structured, tab_raw = st.tabs(["Structured Output", "Raw Output"])

            with tab_structured:
                if stage.get("output_structured"):
                    st.json(stage["output_structured"])
                else:
                    st.caption("No structured JSON extracted from agent output.")

            with tab_raw:
                st.code(stage.get("output_raw", "—"), language="markdown")

            if stage.get("input_summary"):
                st.markdown("**Input Summary:**")
                st.json(stage["input_summary"])

            if stage.get("error"):
                st.error(f"Error: {stage['error']}")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🛡️ Agentic SOC")
    st.markdown("**HITL Approval Dashboard**")
    st.divider()

    analyst_id = st.text_input("Your Analyst ID", value="analyst-1", key="analyst_id")
    client_filter = st.text_input("Filter by Client ID", value="", placeholder="Leave empty for all")
    status_filter = st.selectbox(
        "Status Filter",
        ["PENDING", "APPROVED", "REJECTED", "MODIFIED", "ALL"],
    )

    st.divider()
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

    # Stats
    st.subheader("Queue Stats")
    stats = fetch_stats()
    col1, col2 = st.columns(2)
    col1.metric("Pending", stats.get("PENDING", 0))
    col2.metric("Approved", stats.get("APPROVED", 0))
    col3, col4 = st.columns(2)
    col3.metric("Rejected", stats.get("REJECTED", 0))
    col4.metric("Modified", stats.get("MODIFIED", 0))


# ── Main Content ──────────────────────────────────────────────────────────────
st.title("🛡️ Agentic SOC Dashboard")

main_tab_approvals, main_tab_pipeline = st.tabs(["Approval Queue", "Workflow Pipeline"])

# ── Pipeline Tab ─────────────────────────────────────────────────────────────
with main_tab_pipeline:
    st.subheader("Agent Workflow Pipeline")
    st.caption("ICM Glass Box — inspect intermediate agent outputs per case.")

    pipeline_case_id = st.text_input(
        "Case ID", value="", placeholder="Enter a case ID to view its pipeline", key="pipeline_case"
    )
    if pipeline_case_id:
        stages = fetch_pipeline_by_case(pipeline_case_id, client_filter)
        render_pipeline(stages)
    else:
        st.markdown("**Recent Workflows:**")
        recent = fetch_recent_pipelines(client_filter)
        if not recent:
            st.info("No pipeline data yet. Stages are recorded when agents process alerts.")
        else:
            # Group by session_id
            sessions = {}
            for s in recent:
                sid = s["session_id"]
                if sid not in sessions:
                    sessions[sid] = {
                        "case_id": s["case_id"],
                        "client_id": s["client_id"],
                        "started": s.get("started_at", ""),
                        "stages": [],
                    }
                sessions[sid]["stages"].append(s)

            for sid, info in list(sessions.items())[:10]:
                with st.expander(
                    f"Case: {info['case_id']} | Client: {info['client_id']} | {info['started'][:19]}",
                    expanded=False,
                ):
                    render_pipeline(sorted(info["stages"], key=lambda x: x["stage_order"]))

# ── Approvals Tab ────────────────────────────────────────────────────────────
with main_tab_approvals:
    st.subheader("Agent Action Approval Queue")

    fetch_status = "ALL" if status_filter == "ALL" else status_filter
    if status_filter == "ALL":
        approvals = []
        for s in ["PENDING", "APPROVED", "REJECTED", "MODIFIED"]:
            approvals.extend(fetch_approvals(status=s, client_id=client_filter))
    else:
        approvals = fetch_approvals(status=status_filter, client_id=client_filter)

    if not approvals:
        st.info("No approvals found matching the current filter.")
        st.stop()

    for approval in approvals:
        approval_id = approval.get("approval_id", "unknown")
        case_id = approval.get("case_id", "—")
        client_id = approval.get("client_id", "—")
        agent_name = approval.get("agent_name", "—")
        status = approval.get("status", "—")
        proposed_action = approval.get("proposed_action", {})
        triage_summary = approval.get("triage_summary", "")
        created_at = format_dt(approval.get("created_at", ""))
        decided_by = approval.get("decided_by")

        status_color = {
            "PENDING": "🟠",
            "APPROVED": "🟢",
            "REJECTED": "🔴",
            "MODIFIED": "🔵",
        }.get(status, "⚪")

        with st.expander(
            f"{status_color} [{status}] Case: {case_id} | Client: {client_id} | "
            f"{proposed_action.get('proposed_action', 'unknown')} | {created_at}",
            expanded=(status == "PENDING"),
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("### Agent Reasoning")
                st.markdown(triage_summary or "*No reasoning provided*")

                st.markdown("### Proposed Action")
                impact_badge = severity_badge(proposed_action)
                st.markdown(f"**Impact:** {impact_badge}")
                st.json(proposed_action)

            with col2:
                st.markdown("### Case Details")
                st.markdown(f"**Case ID:** `{case_id}`")
                st.markdown(f"**Client:** `{client_id}`")
                st.markdown(f"**Agent:** `{agent_name}`")
                st.markdown(f"**Created:** {created_at}")
                if decided_by:
                    st.markdown(f"**Decided by:** `{decided_by}`")
                    st.markdown(f"**Decided at:** {format_dt(approval.get('decided_at', ''))}")

                if approval.get("analyst_instructions"):
                    st.markdown("**Analyst Notes:**")
                    st.info(approval["analyst_instructions"])

                # ICM Glass Box: show pipeline context for this case
                session_id = approval.get("session_id")
                if session_id and st.button(
                    "🔍 View Pipeline", key=f"pipeline_{approval_id}", use_container_width=True
                ):
                    st.session_state[f"show_pipeline_{approval_id}"] = True

            if st.session_state.get(f"show_pipeline_{approval_id}"):
                st.markdown("### Agent Pipeline (Glass Box)")
                pipeline_session = approval.get("session_id", "")
                if pipeline_session:
                    stages = fetch_pipeline_by_session(pipeline_session)
                else:
                    stages = fetch_pipeline_by_case(case_id, client_id)
                render_pipeline(stages)

            # Decision controls (only for PENDING)
            if status == "PENDING":
                st.divider()
                st.markdown("### Your Decision")

                notes = st.text_area(
                    "Analyst Notes (optional)",
                    key=f"notes_{approval_id}",
                    placeholder="Reason for approval/rejection, context...",
                )

                decision_col1, decision_col2, decision_col3 = st.columns(3)

                with decision_col1:
                    if st.button(
                        "✅ Approve",
                        key=f"approve_{approval_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        ok, msg = submit_decision(approval_id, "APPROVED", analyst_id, notes)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(f"Failed: {msg}")

                with decision_col2:
                    if st.button(
                        "❌ Reject",
                        key=f"reject_{approval_id}",
                        use_container_width=True,
                    ):
                        if not notes:
                            st.warning("Please provide a rejection reason in Analyst Notes.")
                        else:
                            ok, msg = submit_decision(approval_id, "REJECTED", analyst_id, notes)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(f"Failed: {msg}")

                with decision_col3:
                    if st.button(
                        "✏️ Modify & Approve",
                        key=f"modify_{approval_id}",
                        use_container_width=True,
                    ):
                        st.session_state[f"show_modify_{approval_id}"] = True

                # Modify form
                if st.session_state.get(f"show_modify_{approval_id}"):
                    st.markdown("**Modified Parameters (JSON):**")
                    modified_json = st.text_area(
                        "Enter modified parameters as JSON",
                        key=f"modified_params_{approval_id}",
                        value=json.dumps(proposed_action.get("parameters", {}), indent=2),
                    )
                    if st.button("Submit Modified", key=f"submit_modify_{approval_id}"):
                        try:
                            modified_params = json.loads(modified_json)
                            ok, msg = submit_decision(
                                approval_id, "MODIFIED", analyst_id, notes, modified_params
                            )
                            if ok:
                                st.success(msg)
                                st.session_state.pop(f"show_modify_{approval_id}", None)
                                st.rerun()
                            else:
                                st.error(f"Failed: {msg}")
                        except json.JSONDecodeError:
                            st.error("Invalid JSON in modified parameters.")
