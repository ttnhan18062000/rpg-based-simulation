"""Assembles the shared 13-field tools.jsonl record shape for a Codex PostToolUse event (Step 2).

Produces exactly the field set tools/agent-monitoring/post_tool_hook.py's own record does
(session_id, run_id, seq, phase, agent, ts, tool, input_summary, status, duration_ms,
execution_id, provider, ticket_id), so this adapter is a fourth call site into the same shared
shape, not a divergent one. The 6 Codex-only envelope/payload fields (transcript_path, cwd,
model, permission_mode, turn_id, tool_use_id) have no parameter here at all, so there is nothing
to accidentally pass through.

`duration_ms` is always None — the Codex PostToolUse payload carries no pre-hook-start timestamp
sidecar equivalent to Claude's .claude/.tool_start; fabricating one would invent durable meaning
that does not exist.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .input_model import CodexPostToolUsePayload
from .redaction import derive_status, summarize_tool_input


def build_record(
    payload: CodexPostToolUsePayload,
    *,
    execution_id: str,
    provider: str,
    ticket_id: str,
    run_id: str | None = None,
    seq: int | None = None,
    phase: str | None = None,
    agent: str | None = None,
    now: str | None = None,
) -> dict:
    ts = now if now is not None else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "session_id": payload.session_id,
        "run_id": run_id,
        "seq": seq,
        "phase": phase,
        "agent": agent,
        "ts": ts,
        "tool": payload.tool_name,
        "input_summary": summarize_tool_input(payload.tool_name, payload.tool_input),
        "status": derive_status(payload.tool_response),
        "duration_ms": None,
        "execution_id": execution_id,
        "provider": provider,
        "ticket_id": ticket_id,
    }
