"""
Enrichment Agent — ADK Evaluation Module.

Exposes `root_agent` with mock Chronicle + GTI tools for eval.
Uses the GTI-enabled prompt variant since eval scenarios include GTI enrichment.
"""
from google.adk.agents import LlmAgent

from agents.enrichment.prompts import ENRICHMENT_SYSTEM_PROMPT
from evals.mock_tools import (
    translate_udm_query,
    udm_search,
    summarize_entity,
    search_entity,
    get_ioc_match,
    get_case,
    create_case_comment,
    get_file_report,
    get_ip_address_report,
    get_domain_report,
    get_url_report,
    get_entities_related_to_a_file,
    get_entities_related_to_a_domain,
    get_entities_related_to_an_ip_address,
    get_file_behavior_summary,
    get_collection_mitre_tree,
)

root_agent = LlmAgent(
    name="enrichment_agent",
    model="gemini-2.5-flash",
    instruction=ENRICHMENT_SYSTEM_PROMPT,
    tools=[
        translate_udm_query, udm_search, summarize_entity, search_entity, get_ioc_match,
        get_case, create_case_comment,
        get_file_report, get_ip_address_report, get_domain_report, get_url_report,
        get_entities_related_to_a_file, get_entities_related_to_a_domain,
        get_entities_related_to_an_ip_address, get_file_behavior_summary,
        get_collection_mitre_tree,
    ],
)
