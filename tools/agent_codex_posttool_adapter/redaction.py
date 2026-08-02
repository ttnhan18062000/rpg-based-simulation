"""Tool-input summarization and tool-response status derivation (Step 2).

Structurally parallel to tools/agent-monitoring/post_tool_hook.py::_input_summary and its
status-derivation logic, built fresh here since no importable shared helper exists anywhere in
the repo (confirmed by investigation.md's Question 4 grep). Neither function returns, logs, or
stores `tool_response` content itself — only the derived `"ok"`/`"failed"` flag ever leaves this
module.
"""
from __future__ import annotations


def summarize_tool_input(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        return (tool_input.get("command") or "")[:80]
    if tool_name in ("Read", "Edit", "Write", "MultiEdit"):
        return (tool_input.get("file_path") or "")[:120]
    if tool_name == "Agent":
        return (tool_input.get("description") or tool_input.get("prompt") or "")[:80]
    if tool_name.startswith("mcp__"):
        query = tool_input.get("query") or tool_input.get("q") or tool_input.get("text") or ""
        return f"query={query!r}"[:120]
    return str(tool_input)[:80]


def derive_status(tool_response: object) -> str:
    if isinstance(tool_response, dict):
        if tool_response.get("is_error") or tool_response.get("error"):
            return "failed"
    elif isinstance(tool_response, str) and tool_response.startswith("ERROR"):
        return "failed"
    return "ok"
