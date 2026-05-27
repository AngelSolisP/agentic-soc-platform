"""Shared fixtures for ADK evaluation tests."""
import os

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip eval-marked tests when GOOGLE_API_KEY is not set."""
    skip_eval = pytest.mark.skip(
        reason="GOOGLE_API_KEY not set — Tier 2 evals require Gemini access"
    )
    for item in items:
        if "eval" in item.keywords and not os.environ.get("GOOGLE_API_KEY"):
            item.add_marker(skip_eval)
