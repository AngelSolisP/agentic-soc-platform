"""
Pytest configuration — adds the project root to sys.path
so that imports like `from proxy.mcp_gateway.main import app` work
regardless of how pytest is invoked.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ENFORCE_CLIENT_AUTH defaults to true in production.
# Tests run without Firestore analyst_assignments, so disable globally.
os.environ.setdefault("ENFORCE_CLIENT_AUTH", "false")
