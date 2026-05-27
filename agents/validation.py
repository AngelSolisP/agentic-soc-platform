"""Input validation and sanitization for the Agentic SOC platform.

Provides:
- validate_client_id: prevents path traversal attacks in MCP Gateway URLs
- sanitize_alert_payload: field filtering + truncation before LLM prompt injection
"""

import json
import re

# Allowed characters in client_id — alphanumeric, hyphen, underscore, 1–64 chars
_CLIENT_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

# Fields that may be extracted from raw alert dicts and surfaced to the LLM
_ALLOWED_ALERT_FIELDS = {
    "alert_type",
    "severity",
    "source",
    "entities",
    "timestamps",
    "raw_log",
    "case_id",
    "client_id",
    "trigger",
    "priority",
    "indicators",
    "iocs",
    "affected_hosts",
    "affected_users",
}

_RAW_LOG_MAX_BYTES = 2048       # 2 KB cap for raw_log field
_ALERT_DATA_OPEN = "<ALERT_DATA>"
_ALERT_DATA_CLOSE = "</ALERT_DATA>"


def validate_client_id(client_id: str) -> str:
    """Validate a client_id string for use in MCP Gateway URLs.

    Accepts only alphanumeric characters, hyphens, and underscores (1–64 chars).
    This prevents path traversal, URL injection, and shell-meta-character attacks.

    Args:
        client_id: The raw client identifier to validate.

    Returns:
        The original client_id string if it passes validation.

    Raises:
        ValueError: If client_id is invalid (includes message with reason).
    """
    if not isinstance(client_id, str) or not client_id:
        raise ValueError("client_id must be a non-empty string")

    if not _CLIENT_ID_RE.match(client_id):
        raise ValueError(
            f"Invalid client_id {client_id!r}: must match ^[a-zA-Z0-9_-]{{1,64}}$. "
            "Path traversal sequences, URL-encoded characters, spaces, and special "
            "characters are not allowed."
        )

    return client_id


def safe_agent_name(client_id: str) -> str:
    """Convert a client_id into a valid ADK agent name suffix.

    ADK LlmAgent names must be valid Python identifiers (letters, digits,
    underscores only). Client IDs allow hyphens (e.g. 'demo-tenant'),
    so we replace non-identifier characters with underscores.
    """
    return re.sub(r"[^a-zA-Z0-9_]", "_", client_id)


def sanitize_alert_payload(
    raw_alert: "dict | None",
    max_bytes: int = 8192,
) -> str:
    """Sanitize a raw alert dict for safe injection into an LLM prompt.

    Steps:
    1. Return "Not provided" if raw_alert is None.
    2. Keep only the fields in _ALLOWED_ALERT_FIELDS (drops verbose/metadata blobs).
    3. Truncate the raw_log field to _RAW_LOG_MAX_BYTES bytes if present.
    4. JSON-serialize and cap the total output at max_bytes.
    5. Wrap the result in <ALERT_DATA>…</ALERT_DATA> delimiters.

    Args:
        raw_alert: Alert dict from the SIEM, or None.
        max_bytes: Maximum size (bytes) for the JSON portion (default 8192).

    Returns:
        A string safe for inclusion in a prompt template.
    """
    if raw_alert is None:
        return "Not provided"

    # Step 2: field-level filtering
    filtered: dict = {
        key: value
        for key, value in raw_alert.items()
        if key in _ALLOWED_ALERT_FIELDS
    }

    # Step 3: truncate raw_log to avoid log-injection / context flooding
    if "raw_log" in filtered:
        raw_log = filtered["raw_log"]
        if isinstance(raw_log, str):
            encoded = raw_log.encode("utf-8", errors="replace")
            if len(encoded) > _RAW_LOG_MAX_BYTES:
                filtered["raw_log"] = (
                    encoded[:_RAW_LOG_MAX_BYTES].decode("utf-8", errors="replace")
                    + " [TRUNCATED]"
                )

    # Step 4: serialize and cap total size
    json_str = json.dumps(filtered, indent=2, ensure_ascii=False)
    encoded_json = json_str.encode("utf-8", errors="replace")
    if len(encoded_json) > max_bytes:
        truncated = encoded_json[:max_bytes].decode("utf-8", errors="replace")
        # Close the JSON string gracefully so the LLM sees a clear boundary
        json_str = truncated + "\n... [PAYLOAD TRUNCATED]"

    # Step 5: wrap in delimiters
    return f"{_ALERT_DATA_OPEN}\n{json_str}\n{_ALERT_DATA_CLOSE}"
