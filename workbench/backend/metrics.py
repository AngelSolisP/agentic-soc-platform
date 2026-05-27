"""Agent performance metrics aggregation from workflow_stages."""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

STAGES_COLLECTION = "workflow_stages"


def get_agent_performance(db, client_id: str = None, days: int = 30) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()

    query = db.collection(STAGES_COLLECTION)
    if client_id:
        query = query.where("client_id", "==", client_id)

    docs = query.stream()

    by_agent: dict[str, dict] = defaultdict(lambda: {
        "total_runs": 0,
        "completed": 0,
        "errors": 0,
        "total_duration": 0.0,
        "verdicts": defaultdict(int),
    })

    for doc in docs:
        data = doc.to_dict()
        started = data.get("started_at", "")
        if isinstance(started, str) and started < cutoff_iso:
            continue

        agent = data.get("agent_name", "unknown")
        stats = by_agent[agent]
        stats["total_runs"] += 1

        if data.get("status") == "COMPLETED":
            stats["completed"] += 1
        elif data.get("status") == "ERROR":
            stats["errors"] += 1

        duration = data.get("duration_seconds", 0)
        if isinstance(duration, (int, float)):
            stats["total_duration"] += duration

        output = data.get("output_structured", {})
        if isinstance(output, dict) and "verdict" in output:
            stats["verdicts"][output["verdict"]] += 1

    result = []
    for agent_name, stats in by_agent.items():
        total = stats["total_runs"]
        avg_duration = stats["total_duration"] / total if total > 0 else 0
        error_rate = stats["errors"] / total if total > 0 else 0

        result.append({
            "agent_name": agent_name,
            "total_runs": total,
            "completed": stats["completed"],
            "errors": stats["errors"],
            "avg_duration_seconds": round(avg_duration, 2),
            "error_rate": round(error_rate, 4),
            "verdicts": dict(stats["verdicts"]),
        })

    return result
