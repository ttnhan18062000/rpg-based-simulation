"""
tools/agent-monitoring/shadow_reviewer_events.py — advisory shadow-candidate-reviewer event
emission (TCK-20260904-SHADOW-REVIEWER-LOGGING).

Deliberately NOT built on top of tools/retrieval_events.py::emit_retrieval_event() -- that
function's own unknown-field guard (RETRIEVAL_EVENT_FIELDS) would reject every field this module
adds. Reproduces its underlying pattern directly: validate via record_events.validate_record(),
write via writer.write_lines() -- no new lock/queue/journal mechanism of its own.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_MONITORING_DIR = Path(__file__).resolve().parent
if str(_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_DIR))

import record_events  # noqa: E402
from cost_proxy import compute_cost_proxy_score  # noqa: E402
from validate import load_data_glob  # noqa: E402
from writer import write_lines  # noqa: E402

shadow_reviewer_event_schema_version: int = 1

# Additive field family on top of events.jsonl's 7 base REQUIRED fields (record_events.REQUIRED)
# -- never replaces or narrows that set, mirrors RETRIEVAL_EVENT_FIELDS's own precedent.
SHADOW_REVIEWER_EVENT_FIELDS: frozenset[str] = frozenset(
    {
        "shadow_reviewer_event_schema_version",
        "candidate_model",
        "candidate_verdict",
        "candidate_violations_count",
        "candidate_tool_call_count",
        "candidate_cost_proxy_score",
        "candidate_wall_time_ms",
        "workflow_wall_time_ms",
    }
)


def _compute_candidate_tool_stats(run_id: str, seq: int) -> tuple[int, float]:
    """Reads real tools.jsonl ground truth for this shadow call's own (run_id, seq) bucket --
    same shape as record_events.py::compute_tool_stats(), scoped to one key instead of a batch."""
    rows = [
        r
        for r in load_data_glob(Path("agent-monitoring/data"), "tools")
        if r.get("run_id") == run_id and r.get("seq") == seq
    ]
    return len(rows), compute_cost_proxy_score(rows)


def emit_shadow_reviewer_event(
    *,
    run_id: str,
    seq: int,
    phase: str,
    agent: str,
    summary: str,
    candidate_model: str,
    candidate_verdict: str,
    candidate_violations_count: int,
    candidate_wall_time_ms: int,
    workflow_wall_time_ms: int,
    status: str = "ok",
    ts: str | None = None,
    events_file: Path | None = None,
) -> bool:
    """Build, validate, and append one shadow-reviewer event record. Never raises on a write
    failure (write_lines()'s bool returned as-is, per CLAUDE.md's "monitoring write failure must
    never fail the workflow"); DOES raise on a record validate_record() itself rejects (base-schema
    misuse), same fail-loud/fail-soft split as emit_retrieval_event()."""
    candidate_tool_call_count, candidate_cost_proxy_score = _compute_candidate_tool_stats(run_id, seq)

    record = {
        "run_id": run_id,
        "seq": seq,
        "ts": ts if ts is not None else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "phase": phase,
        "agent": agent,
        "summary": summary,
        "status": status,
        "shadow_reviewer_event_schema_version": shadow_reviewer_event_schema_version,
        "candidate_model": candidate_model,
        "candidate_verdict": candidate_verdict,
        "candidate_violations_count": candidate_violations_count,
        "candidate_tool_call_count": candidate_tool_call_count,
        "candidate_cost_proxy_score": candidate_cost_proxy_score,
        "candidate_wall_time_ms": candidate_wall_time_ms,
        "workflow_wall_time_ms": workflow_wall_time_ms,
    }

    errors = record_events.validate_record(record)
    if errors:
        raise ValueError(errors)

    if events_file is not None:
        target = events_file
    else:
        # Matches record_events.py's own current-week target (record_events.py:153-154) --
        # EVENTS_FILE no longer exists as a module attribute (TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY).
        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        target = Path("agent-monitoring/data") / iso_week / "events.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    return write_lines(target, [json.dumps(record, separators=(",", ":"))])
