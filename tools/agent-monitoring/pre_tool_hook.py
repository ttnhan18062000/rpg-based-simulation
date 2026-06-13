#!/usr/bin/env python3
"""PreToolUse hook: saves start timestamp and session_id before each tool call."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    payload = json.load(sys.stdin)
    session_id = payload.get("session_id", "")

    Path(".claude/.current_session_id").write_text(session_id)
    Path(".claude/.tool_start").write_text(json.dumps({
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "session_id": session_id,
    }))
except Exception:
    pass
