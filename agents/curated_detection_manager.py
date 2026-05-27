"""
Curated Detection Manager — List and manage Google-curated detection rule sets.

Provides utilities for querying curated rule sets and their deployment status
across client tenants. This is used by the Detection Engineering Agent (Phase 2).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def format_curated_rule_set_summary(rule_sets: list[dict]) -> str:
    """Format a list of curated rule sets for a prompt/comment.

    Args:
        rule_sets: List of rule sets from list_curated_rule_sets.

    Returns:
        Human-readable summary of available rule sets and their status.
    """
    if not rule_sets:
        return "No curated rule sets found."

    lines = ["**Available Curated Detection Rule Sets:**"]
    for rs in rule_sets:
        status = "ENABLED" if rs.get("enabled") else "DISABLED"
        lines.append(f"  - {rs.get('displayName', rs.get('name'))}: {status}")
        if rs.get("description"):
            lines.append(f"    _{rs.get('description')}_")

    return "\n".join(lines)


def filter_active_rule_sets(rule_sets: list[dict]) -> list[str]:
    """Filter rule sets to return only the IDs of active ones.

    Args:
        rule_sets: List of rule sets.

    Returns:
        List of rule set IDs (resource names).
    """
    return [rs["name"] for rs in rule_sets if rs.get("enabled")]
