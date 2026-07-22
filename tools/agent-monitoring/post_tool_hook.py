#!/usr/bin/env python3
"""PostToolUse hook: appends one tool-call record to agent-monitoring/tools.jsonl."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from writer import write_line  # noqa: E402


def _input_summary(tool_name: str, tool_input: dict) -> str:
    if tool_name in ("Read", "Edit", "Write", "MultiEdit"):
        return (tool_input.get("file_path") or "")[:120]
    if tool_name == "Bash":
        return (tool_input.get("command") or "")[:80]
    if tool_name == "Agent":
        return (tool_input.get("description") or tool_input.get("prompt") or "")[:80]
    if tool_name.startswith("mcp__"):
        # e.g. mcp__knowledge-search__search_docs with {"query": "..."}
        query = tool_input.get("query") or tool_input.get("q") or tool_input.get("text") or ""
        return f"query={query!r}"[:120]
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
    phase = None
    agent = None
    execution_id = None
    provider = None
    ticket_id = None
    try:
        sidecar = json.loads(Path(".claude/current_run").read_text())
        run_id = sidecar.get("run_id") or None
        seq = sidecar.get("seq") or None
        phase = sidecar.get("phase") or None
        agent = sidecar.get("agent") or None
        execution_id = sidecar.get("execution_id") or None
        provider = sidecar.get("provider") or None
        ticket_id = sidecar.get("ticket_id") or None
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
        "phase": phase,
        "agent": agent,
        "ts": now,
        "tool": tool_name,
        "input_summary": _input_summary(tool_name, tool_input),
        "status": status,
        "duration_ms": duration_ms,
        "execution_id": execution_id,
        "provider": provider,
        "ticket_id": ticket_id,
    }

    tools_file = Path("agent-monitoring/tools.jsonl")
    tools_file.parent.mkdir(parents=True, exist_ok=True)
    write_line(tools_file, json.dumps(record, separators=(",", ":")))

except Exception:
    pass
