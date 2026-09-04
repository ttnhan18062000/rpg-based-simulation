#!/usr/bin/env python3
"""PostToolUse hook: appends one tool-call record to agent-monitoring/data/<ISO-week>/tools.jsonl."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from writer import write_line  # noqa: E402

# TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE: a per-session scoped sidecar file is new durable
# state and needs a defined lifecycle (CLAUDE.md's Durable State Rule) — there is no "session
# end" hook in this repo to delete it precisely, so any subsequent hook invocation from any
# session opportunistically sweeps up scoped files this old, bounding growth.
_SIDECAR_STALE_SECONDS = 24 * 3600


def _prune_stale_scoped_sidecars() -> None:
    try:
        claude_dir = Path(".claude")
        now = time.time()
        for path in claude_dir.glob("current_run.*"):
            try:
                if now - path.stat().st_mtime > _SIDECAR_STALE_SECONDS:
                    path.unlink()
            except OSError:
                pass
    except Exception:
        pass


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

    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat().replace("+00:00", "Z")
    iso_week = now_dt.strftime("%G-W%V")  # matches generate_retro.py::iso_week() (tools/agent-monitoring/generate_retro.py:126)
                                            # and its --week current-week default (generate_retro.py:152).
                                            # Duplicated (not imported) to keep this hot hook's import
                                            # graph stdlib-only — see Decision 3 in plan.md. If this
                                            # format ever changes, update generate_retro.py::iso_week() too.

    # Compute duration from pre-hook timestamp
    duration_ms = None
    try:
        start_data = json.loads(Path(".claude/.tool_start").read_text())
        pre = datetime.fromisoformat(start_data["ts"].replace("Z", "+00:00"))
        post = datetime.fromisoformat(now.replace("Z", "+00:00"))
        duration_ms = int((post - pre).total_seconds() * 1000)
    except Exception:
        pass

    # Read workflow sidecar for run_id / seq. See also tools/retrieval_cache.py's
    # read_current_run_sidecar() — a separate reader of the same file convention for the KGMCP
    # cache-access log, deliberately NOT unified into a shared helper (TCK-20260824-RETRIEVAL-
    # CACHE-SIDECAR-UNIFY's own reasoning) but kept in sync by convention; check it when changing
    # this block. TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE: prefer a
    # per-session scoped file (`.claude/current_run.<session_id>`) over the shared unscoped file —
    # the shared file is overwritten by every concurrent session's own writeSidecar() call, so
    # reading it unconditionally silently misattributes tool calls to whichever session wrote it
    # last (confirmed live: a closed ticket kept absorbing another session's tool-call rows for two
    # days).
    #
    # TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION: when NO scoped file exists yet for this
    # session, do not fall back to the unscoped file — write a null-valued sentinel instead and
    # report null attribution. Every real writer (writeSidecar() in implement-ticket.js, and
    # hand-orchestration per .claude/skills/implement-ticket/SKILL.md) writes the scoped file and
    # the unscoped file together, atomically — so a session with no scoped file genuinely has no
    # real ticket attribution to report yet, and falling back to the unscoped file would silently
    # inherit whatever foreign (possibly long-closed) ticket another concurrent session last wrote
    # there, which is the exact bug this ticket fixes. The sentinel write is create-if-absent only:
    # if a real writeSidecar() call for this same session_id lands later, it unconditionally
    # overwrites this same path with real values (it does not check for an existing file), so the
    # sentinel never clobbers real attribution — it only fills the window before the first real
    # write. The sentinel is a normal `current_run.*` file, so `_prune_stale_scoped_sidecars()`
    # below sweeps it identically to any other scoped file, with no separate cleanup path.
    run_id = None
    seq = None
    phase = None
    agent = None
    execution_id = None
    provider = None
    ticket_id = None
    scoped_path = Path(f".claude/current_run.{session_id}") if session_id else None
    if scoped_path is not None and scoped_path.exists():
        sidecar_path = scoped_path
    elif scoped_path is not None:
        try:
            scoped_path.parent.mkdir(parents=True, exist_ok=True)
            scoped_path.write_text(json.dumps({
                "run_id": None, "seq": None, "phase": None, "agent": None,
                "execution_id": None, "provider": None, "ticket_id": None,
            }))
        except Exception:
            pass
        sidecar_path = scoped_path
    else:
        # No session_id in the hook payload at all (defensive — real Claude Code hooks always
        # supply one). Degrade to the pre-TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION behavior
        # rather than losing attribution entirely for a case this repo has never actually hit.
        sidecar_path = Path(".claude/current_run")
    try:
        sidecar = json.loads(sidecar_path.read_text())
        run_id = sidecar.get("run_id") or None
        seq = sidecar.get("seq") or None
        phase = sidecar.get("phase") or None
        agent = sidecar.get("agent") or None
        execution_id = sidecar.get("execution_id") or None
        provider = sidecar.get("provider") or None
        ticket_id = sidecar.get("ticket_id") or None
    except Exception:
        pass

    _prune_stale_scoped_sidecars()

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

    tools_file = Path("agent-monitoring/data") / iso_week / "tools.jsonl"
    tools_file.parent.mkdir(parents=True, exist_ok=True)
    write_line(tools_file, json.dumps(record, separators=(",", ":")))

except Exception:
    pass
