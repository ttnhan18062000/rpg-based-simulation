#!/usr/bin/env python3
"""PostToolUse hook: appends one tool-call record to agent-monitoring/tools.jsonl."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _input_summary(tool_name: str, tool_input: dict) -> str:
    if tool_name in ("Read", "Edit", "Write", "MultiEdit"):
        return (tool_input.get("file_path") or "")[:120]
    if tool_name == "Bash":
        return (tool_input.get("command") or "")[:80]
    if tool_name == "Agent":
        return (tool_input.get("description") or tool_input.get("prompt") or "")[:80]
    return str(tool_input)[:80]


try:
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or {}
    session_id = payload.get("session_id", "")

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Compute duration from pre-hook timestamp
    duration_ms = None
    try:
        start_data = json.loads(Path(".claude/.tool_start").read_text())
        pre = datetime.fromisoformat(start_data["ts"].replace("Z", "+00:00"))
        post = datetime.fromisoformat(now.replace("Z", "+00:00"))
        duration_ms = int((post - pre).total_seconds() * 1000)
    except Exception:
        pass

    # Read workflow sidecar for run_id / seq
    run_id = None
    seq = None
    try:
        sidecar = json.loads(Path(".claude/current_run").read_text())
        run_id = sidecar.get("run_id") or None
        seq = sidecar.get("seq") or None
    except Exception:
        pass

    # Determine status from tool response
    status = "ok"
    if isinstance(tool_response, dict):
        if tool_response.get("is_error") or tool_response.get("error"):
            status = "failed"
    elif isinstance(tool_response, str) and tool_response.startswith("ERROR"):
        status = "failed"

    record = {
        "session_id": session_id,
        "run_id": run_id,
        "seq": seq,
        "ts": now,
        "tool": tool_name,
        "input_summary": _input_summary(tool_name, tool_input),
        "status": status,
        "duration_ms": duration_ms,
    }

    tools_file = Path("agent-monitoring/tools.jsonl")
    tools_file.parent.mkdir(parents=True, exist_ok=True)
    with open(tools_file, "a") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")

except Exception:
    pass
