#!/usr/bin/env python3
"""PreToolUse hook: saves a start stamp for this one tool call and the session id.

TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS: the stamp is keyed by session_id + tool_use_id
(`.claude/tool_starts/<session_id>.<tool_use_id>`), not one shared, unkeyed `.claude/.tool_start`. The shared file
was overwritten by every concurrent session and every parallel call, which produced durations like a `cat` at 8.6 h.
`post_tool_hook.py` reads and deletes exactly its own stamp; with no tool_use_id nothing is written and the duration
stays unknown (null), never a wrong number.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SAFE = re.compile(r"[^A-Za-z0-9_.-]")


def stamp_path(session_id: str, tool_use_id: str) -> Path:
    """The per-call stamp path (shared with post_tool_hook.py); ids are reduced to a safe file-name alphabet."""
    return Path(".claude") / "tool_starts" / f"{_SAFE.sub('_', session_id)}.{_SAFE.sub('_', tool_use_id)}"


if __name__ == "__main__":
    try:
        payload = json.load(sys.stdin)
        session_id = payload.get("session_id", "")
        tool_use_id = payload.get("tool_use_id") or ""

        Path(".claude/.current_session_id").write_text(session_id)
        if session_id and tool_use_id:
            path = stamp_path(session_id, tool_use_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}))
    except Exception:
        pass
