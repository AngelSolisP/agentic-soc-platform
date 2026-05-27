"""
Risk Scoring — Entity risk context from Chronicle watchlists.

Queries Chronicle watchlists to check if entities involved in a case
are on risk-elevated lists (privileged accounts, compromised hosts, etc.).
Returns a risk modifier that the Triage Agent uses to calibrate confidence.

Phase A: Risk Analytics Integration.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Risk multipliers based on watchlist membership
RISK_MODIFIERS = {
    "critical_assets": 0.20,      # Crown jewel systems
    "privileged_accounts": 0.15,  # Admin/service accounts
    "vip_users": 0.15,            # Executive accounts
    "compromised_entities": 0.20, # Previously compromised
    "default": 0.10,              # Any other watchlist
}


def calculate_risk_modifier(watchlist_name: str) -> float:
    """Calculate risk modifier based on watchlist name.

    Args:
        watchlist_name: Name of the watchlist the entity belongs to.

    Returns:
        Risk modifier (0.0 to 0.20) to add to confidence_score.
    """
    name_lower = watchlist_name.lower()
    for key, modifier in RISK_MODIFIERS.items():
        if key in name_lower:
            return modifier
    return RISK_MODIFIERS["default"]


def aggregate_entity_risk(entity_watchlists: list[dict]) -> dict:
    """Aggregate risk across all watchlist memberships for an entity.

    Args:
        entity_watchlists: List of {"entity": str, "watchlist": str} dicts.

    Returns:
        Dict with risk summary:
        {
            "total_modifier": float,  # Capped at 0.30
            "watchlisted_entities": [...],
            "highest_risk_watchlist": str,
            "risk_level": "HIGH" | "MEDIUM" | "LOW" | "NONE"
        }
    """
    if not entity_watchlists:
        return {
            "total_modifier": 0.0,
            "watchlisted_entities": [],
            "highest_risk_watchlist": None,
            "risk_level": "NONE",
        }

    max_modifier = 0.0
    highest_watchlist = ""
    entities = []

    for entry in entity_watchlists:
        watchlist = entry.get("watchlist", "")
        entity = entry.get("entity", "")
        modifier = calculate_risk_modifier(watchlist)

        if modifier > max_modifier:
            max_modifier = modifier
            highest_watchlist = watchlist

        entities.append({
            "entity": entity,
            "watchlist": watchlist,
            "modifier": modifier,
        })

    # Cap total modifier at 0.30 to prevent confidence inflation
    total = min(sum(e["modifier"] for e in entities), 0.30)

    if total >= 0.20:
        risk_level = "HIGH"
    elif total >= 0.10:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "total_modifier": round(total, 2),
        "watchlisted_entities": entities,
        "highest_risk_watchlist": highest_watchlist,
        "risk_level": risk_level,
    }


def format_risk_context_for_prompt(risk_summary: dict) -> str:
    """Format risk summary as text for injection into agent prompts.

    Args:
        risk_summary: Output from aggregate_entity_risk().

    Returns:
        Human-readable risk context string.
    """
    if risk_summary["risk_level"] == "NONE":
        return "No entities on risk watchlists."

    lines = [f"**Entity Risk Level: {risk_summary['risk_level']}** (modifier: +{risk_summary['total_modifier']})"]
    for entry in risk_summary["watchlisted_entities"]:
        lines.append(f"  - {entry['entity']} → watchlist: {entry['watchlist']} (+{entry['modifier']})")

    return "\n".join(lines)


def get_risk_score_modifier(entity_watchlists: list[dict]) -> dict:
    """Calculate the cumulative risk modifier for entities based on their watchlist memberships.

    Use this tool AFTER calling list_watchlists to interpret the results.
    Watchlisted entities (privileged accounts, VIPs, critical assets) should
    increase the triage confidence_score and may justify priority escalation.

    Args:
        entity_watchlists: List of {"entity": str, "watchlist": str} from list_watchlists.

    Returns:
        Risk summary dict including total_modifier and risk_level.
    """
    summary = aggregate_entity_risk(entity_watchlists)
    # Add human-readable context for the agent
    summary["formatted_context"] = format_risk_context_for_prompt(summary)
    return summary
