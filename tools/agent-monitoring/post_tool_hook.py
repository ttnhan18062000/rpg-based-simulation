#!/usr/bin/env python3
"""PostToolUse / PostToolUseFailure hook: appends one tool-call record to
agent-working/agent-monitoring/data/<ISO-week>/tools.jsonl.

TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS: a PostToolUseFailure payload (`hook_event_name`, `error`,
`is_interrupt`) writes `status: failed` plus a short `error_class`; the duration comes from the payload's own
`duration_ms` when Claude Code sends one, else from this call's own start stamp (see pre_tool_hook.py), else null.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from writer import write_line  # noqa: E402
# Decision 3 (TCK-20260902-MONITORING-SHARD-WRITE-PATH's plan.md) ruled out importing
# generate_retro.py (2,344 lines, pulls in sqlite3/re/three cross-module imports) into this hot
# hook purely to reuse a one-line strftime call -- a real, heavy transitive-dependency cost for a
# trivial reuse. monitoring_batch_identifier.py is the opposite trade-off: it is itself stdlib-only
# (sys, datetime, pathlib -- confirmed by its own test asserting no subprocess/heavy import), and
# it is the one place the actual new logic this ticket needs (git-worktree-aware branch
# resolution, detached-HEAD handling, sidecar self-healing) lives at all -- there is no cheaper
# duplicate-instead-of-share trade-off available here, unlike Decision 3's case.
from monitoring_batch_identifier import resolve_write_target  # noqa: E402

# TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE: a per-session scoped sidecar file is new durable
# state and needs a defined lifecycle (CLAUDE.md's Durable State Rule) — there is no "session
# end" hook in this repo to delete it precisely, so any subsequent hook invocation from any
# session opportunistically sweeps up scoped files this old, bounding growth.
_SIDECAR_STALE_SECONDS = 24 * 3600
_STAMP_STALE_SECONDS = 24 * 3600   # a call whose post hook never ran leaves its start stamp behind; swept like the sidecars


def _error_class(error_text: str, is_interrupt: bool = False) -> str:
    """A short, closed-set class for a failed call (never the raw error text, which can carry paths and secrets)."""
    import re

    if is_interrupt:
        return "interrupt"
    text = (error_text or "").strip()
    match = re.match(r"Exit code (\d+)", text)
    if match:
        return f"exit_{match.group(1)}"
    low = text.lower()
    if re.search(r"timed? ?out|timeout|deadline exceeded", low):
        return "timeout"
    if re.search(r"\btls\b|ssl|certificate|handshake", low):
        return "tls"
    if re.search(r"\b50[234]\b|bad gateway|service unavailable", low):
        return "http_5xx"
    if re.search(r"permission denied|not permitted|forbidden|\b40[13]\b", low):
        return "permission"
    if re.search(r"no such file|not found|\b404\b", low):
        return "not_found"
    return "error"


def _call_duration_ms(payload: dict, session_id: str, tool_use_id: str, now_dt) -> int | None:
    """This call's duration in ms: the payload's own figure, else this call's own start stamp (read once and
    deleted), else None. Never a figure from another call's stamp."""
    own = payload.get("duration_ms")
    if isinstance(own, (int, float)) and not isinstance(own, bool) and own >= 0:
        return int(own)
    if not (session_id and tool_use_id):
        return None
    try:
        from pre_tool_hook import stamp_path

        path = stamp_path(session_id, tool_use_id)
        started = datetime.fromisoformat(json.loads(path.read_text())["ts"].replace("Z", "+00:00"))
        path.unlink(missing_ok=True)
        ms = int((now_dt - started).total_seconds() * 1000)
        return ms if ms >= 0 else None
    except Exception:
        return None


def _prune_stale_start_stamps() -> None:
    try:
        now = time.time()
        for path in Path(".claude/tool_starts").glob("*"):
            try:
                if now - path.stat().st_mtime > _STAMP_STALE_SECONDS:
                    path.unlink()
            except OSError:
                pass
    except Exception:
        pass


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


def _read_ranged(tool_name: str, tool_input: dict) -> bool | None:
    """Whether a Read call passed offset/limit (ranged) rather than reading the whole file.

    TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS: input_summary alone
    (file_path only, see _input_summary below) cannot answer this — verified empirically against
    the real corpus before adding this field, not assumed. null for every non-Read tool.
    """
    if tool_name != "Read":
        return None
    return tool_input.get("offset") is not None or tool_input.get("limit") is not None


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

    tool_use_id = payload.get("tool_use_id") or ""
    duration_ms = _call_duration_ms(payload, session_id, tool_use_id, now_dt)

    # Read workflow sidecar for run_id / seq. tools/retrieval_cache.py previously carried a
    # separate reader of the same file convention (read_current_run_sidecar(), for the KGMCP
    # cache-access log) — removed by TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL along
    # with that log's own writer chain; this hook's own inlined reader is unaffected.
    # TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE: prefer a
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
    _prune_stale_start_stamps()

    # Determine status: a PostToolUseFailure payload is a failure by definition; otherwise from the tool response
    status = "ok"
    error_text = ""
    event_name = payload.get("hook_event_name") or "PostToolUse"
    if event_name == "PostToolUseFailure" or payload.get("error"):
        status = "failed"
        error_text = str(payload.get("error") or "")
    elif isinstance(tool_response, dict):
        if tool_response.get("is_error") or tool_response.get("error"):
            status = "failed"
            error_text = str(tool_response.get("error") or "")
    elif isinstance(tool_response, str) and tool_response.startswith("ERROR"):
        status = "failed"
        error_text = tool_response

    record = {
        "session_id": session_id,
        "run_id": run_id,
        "seq": seq,
        "phase": phase,
        "agent": agent,
        "ts": now,
        "tool": tool_name,
        "input_summary": _input_summary(tool_name, tool_input),
        "read_ranged": _read_ranged(tool_name, tool_input),
        "status": status,
        "duration_ms": duration_ms,
        "execution_id": execution_id,
        "provider": provider,
        "ticket_id": ticket_id,
    }
    if status == "failed":
        record["error_class"] = _error_class(error_text, bool(payload.get("is_interrupt")))

    # TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX: per-PR/batch write target (superseding the
    # prior per-ticket key, and reconciling this file's own former ticket_id-based branch with
    # every other site's run_id-based one -- one shared identifier now, not two that could
    # disagree). Two different branches can never collide on a git diff hunk if they write to
    # different paths, even under a GitHub squash-merge (this repo's own merge=union
    # .gitattributes entry only protects a real git merge, never a squash-merge). No `if
    # ticket_id` branch any more: a batch identifier is always resolvable (worst case, a
    # clearly-labeled detached-HEAD fallback -- see monitoring_batch_identifier.py), unlike
    # ticket_id, which was genuinely absent for ad-hoc, non-ticket work. Consolidated back into
    # the canonical tools.jsonl by tools/agent-monitoring/monitoring_consolidation.py.
    # iso_week is (re)computed from now_dt here, not inside resolve_write_target() -- see that
    # function's own docstring: this hook's own datetime import is what a test suite freezes to
    # test week-boundary behavior deterministically.
    tools_file = resolve_write_target("tools", iso_week=now_dt.strftime("%G-W%V"))
    tools_file.parent.mkdir(parents=True, exist_ok=True)
    write_line(tools_file, json.dumps(record, separators=(",", ":")))

    # TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES: a throttled low-disk line in this same hook
    # entry (no settings.json change). It reads one small state file per call and does one statvfs per 10 minutes;
    # any failure is swallowed so the tool call and the record above are never affected.
    try:
        sys.path.append(str(Path(__file__).resolve().parents[2]))
        from tools.sessions.disk_warning import mid_session_line  # noqa: E402

        disk_line = mid_session_line(session_id, Path(".claude"))
        if disk_line:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": disk_line}}))
    except Exception:
        pass

except Exception:
    pass
