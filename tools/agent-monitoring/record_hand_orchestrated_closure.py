#!/usr/bin/env python3
"""Convenience wrapper for hand-orchestrated ticket closures to record real monitoring coverage
in one call, instead of hand-crafting two separate --data JSON blobs for record_run.py and
record_events.py. (TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE)

Reuses record_run.py's validate_record/compute_duration_s and record_events.py's
validate_record/warn_vocabulary_drift/compute_tool_stats directly -- this wrapper only fills in
the boilerplate fields (run_id, execution_id, provider, ticket_id, agent, seq) that are identical
across every phase of one ticket's closure, so a hand-orchestrating session no longer has to repeat
them by hand for every event.

Usage:
    python3 tools/agent-monitoring/record_hand_orchestrated_closure.py \\
        --ticket-id TCK-20260904-EXAMPLE --tier hotfix \\
        --title "Short ticket title" \\
        --log-summary "One sentence of what was implemented." \\
        --events '[
          {"phase": "Scope", "status": "ok", "summary": "..."},
          {"phase": "Implement", "status": "ok", "summary": "..."},
          {"phase": "Test", "status": "ok", "summary": "..."},
          {"phase": "Parity", "status": "skipped", "summary": "..."},
          {"phase": "Verify", "status": "ok", "summary": "..."},
          {"phase": "Finalize", "status": "ok", "summary": "..."}
        ]'

Each event object only needs `phase`/`status`/`summary` (plus an optional per-event `ts`, `agent`
override) -- `run_id`, `execution_id`, `provider`, `ticket_id`, and `seq` (1-indexed, in array
order) are filled in automatically and shared across the whole batch, matching a single real
`Workflow` run's own shape. `--start-ts`/`--end-ts` accept explicit ISO-8601 values when known
(`duration_source: "declared"`). Without `--start-ts` the start is derived from the closing session's own
`tools.jsonl` rows (`duration_source: "tool_activity"`, see `hand_closure_time.py`); with no evidence the run records
`duration_source: "unknown"`, `start_ts == end_ts` and `duration_s: null`, never a 0 that reads as a measurement
(TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS). Runs and events also carry the closing `session_id`.

`tool_call_count`/`cost_proxy_score` are only ever added when real `tools.jsonl` rows are found
for a given (run_id, seq) -- a hand-orchestrating session never has a live per-phase sidecar
during the actual work, so an unattributed phase correctly gets no such keys at all (never a
false `0`/`0.0`). TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION adds the closing session's own unattributed rows
(`hand_closure_time.Resolution.claimed`, each row claimed by at most one closure) as one ticket-level total on the final
event, marked `cost_source: "session_window"` (`"sidecar"` for the sidecar path); nothing claimed -> still no keys.

The run record's `workflow` field stays `implement-ticket` by default (see `--workflow` below,
TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP's recorded rationale) so existing
`workflow`-keyed consumers keep working unchanged, but every record from this wrapper always
carries `"execution_mode": "hand"` (TCK-20260929-RUN-EXECUTION-MODE-FIELD) -- a separate field,
never inferred, so `generate_retro.py`'s Run Summary can split real pipeline runs from hand
closures without changing what `workflow` means to anyone already reading it.

This call also appends one row to `agent-working/tickets/working_log.csv` (`--title`/`--log-summary` plus
`--artifacts-path`, which defaults to `agent-working/stored_artifacts/<ticket-id>` for standard/epic tier or
"none (hotfix — no staging artifacts)" for hotfix) -- do not append that row by hand separately
when using this wrapper, or the ticket will get a duplicate working_log entry.

As of `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE`, that warning is also
enforced, not just documented: before appending, this script checks whether
`agent-working/tickets/working_log.csv` already has a row for this exact `(ticket_id, title)` pair (via the
tolerant parser, `working_log_parser.parse_working_log`) and refuses -- prints an `ERROR:` to
stderr naming the existing row and exits non-zero -- rather than silently writing a duplicate. The
run/event monitoring writes above still happen either way; only the working-log append is
guarded. This is a deliberate "fail loudly" choice over a silent idempotent skip -- see that
ticket's Implementation Notes for the reasoning.

It also regenerates `docs/REGISTRY.yaml` (TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES, Scope 3
addendum) via `generate_registry()`, the same function the pipeline's Finalize step uses, so a hand
closure needs no separate `make docs-registry` step. Fail-open like the log write: a failure only
warns. Precondition: the ticket must already be in `agent-working/tickets/done/` when this runs (the documented
closing order), or the regenerated registry will not carry its `agent-working/tickets/done/` entry.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record_events  # noqa: E402
import record_run  # noqa: E402
from vocabulary import (  # noqa: E402
    CANONICAL_TIERS, WORKFLOW_AGENT_PREFIXES, WORKFLOW_AGENTS, infer_workflow, is_known_agent,
)
from monitoring_batch_identifier import resolve_write_target  # noqa: E402
import hand_closure_time  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from working_log_writer import append_working_log_row  # noqa: E402
from working_log_parser import parse_working_log, parse_pending_working_log_shards  # noqa: E402
from generate_registry import generate_registry  # noqa: E402
_REPO_ROOT_STR = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_STR not in sys.path:
    sys.path.append(_REPO_ROOT_STR)
from tools.agent_working_paths import AGENT_MONITORING, STORED_ARTIFACTS, TICKETS, posix  # noqa: E402


def unregistered_agents(ticket_id: str, default_agent: str, events: list) -> list[str]:
    """Agent literals (the `--agent` default plus any per-event `agent` override) that the registry
    does not know for the workflow inferred from `ticket_id`, in first-seen order. A ticket id that
    maps to no known workflow is never rejected (same skip as `warn_vocabulary_drift`)."""
    workflow = infer_workflow(ticket_id)
    if workflow is None:
        return []
    seen: list[str] = []
    for agent in [default_agent, *(e.get("agent") for e in events if isinstance(e, dict))]:
        if agent is not None and agent not in seen and not is_known_agent(workflow, agent):
            seen.append(agent)
    return seen


def _allowed_agents_text(ticket_id: str) -> str:
    workflow = infer_workflow(ticket_id)
    literals = sorted(WORKFLOW_AGENTS.get(workflow, set()))
    prefixes = [f"{p}*" for p in WORKFLOW_AGENT_PREFIXES.get(workflow, ())]
    return ", ".join(literals + prefixes)


def _print_anomaly_validator_result() -> None:
    """Advisory only: run the monitoring anomaly validator after a successful record and print a
    one-line verdict. Never changes the exit code; any failure to run it just says so."""
    validator = Path(__file__).resolve().parent.parent / "gate_checks" / "monitoring_anomaly_validator.py"
    try:
        proc = subprocess.run([sys.executable, str(validator)], capture_output=True, text=True, timeout=120)
        marker = next((l for l in proc.stdout.splitlines() if l.startswith("MARKER:")), None)
        results = json.loads(marker[len("MARKER:"):]) if marker else []
        failing = sorted({r["check"] for r in results if r.get("status") == "FAIL"})
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as e:
        print(f"ADVISORY: monitoring_anomaly_validator did not run: {e}", file=sys.stderr)
        return
    if failing:
        print(f"ADVISORY: monitoring_anomaly_validator reports FAIL in: {', '.join(failing)}", file=sys.stderr)
    else:
        print("ADVISORY: monitoring_anomaly_validator: no FAIL")


def _existing_row_for(
    csv_path: Path, ticket_id: str, title: str, data_root: Path = AGENT_MONITORING / "data"
) -> dict | None:
    """Read-only lookup: the first kept (non-ambiguous) row matching (ticket_id, title) in
    csv_path OR still-pending in a per-batch working_log shard under data_root, else None.

    TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS: `data_root`'s cwd-relative
    default is deliberately left as-is (not anchored to `Path(__file__)`), unlike
    `working_log_writer._WORKING_LOG_PATH`/`_DEFAULT_DATA_ROOT`. This script and its cwd-relative
    `working_log_path` at `main()`'s call site (below) are always resolved against the *same* cwd,
    matching `monitoring_batch_identifier.resolve_write_target()`'s own documented convention that
    every real call site assumes cwd is the checkout it's recording for -- there is no anchor
    mismatch to cause cross-checkout drift here, unlike the bug in `monitoring_consolidation.py`
    (an `__file__`-anchored `data_dir` paired with a cwd-relative CSV write). Anchoring this script
    to `Path(__file__)` instead would break the real invariant it depends on: a hand-orchestrating
    session always runs this script from within the checkout it's closing a ticket in, and
    `tests/tools/test_record_hand_orchestrated_closure.py` exercises exactly that by invoking it as
    a subprocess with `cwd=` a scratch checkout distinct from this file's own location.

    TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET: `append_working_log_row()` now stages to a
    shard rather than writing csv_path directly, so a prior direct call for this exact ticket is
    invisible to a CSV-only scan -- checking only csv_path would silently blind this double-write
    guard the same way it was designed to catch. Uses the tolerant parser
    (working_log_parser.parse_working_log) for the CSV side, not a raw csv.reader -- a naive
    reader can misclassify known-malformed historical rows, and this lookup must never produce a
    false negative (missing a real duplicate) or a false positive (an ambiguous/malformed row
    wrongly read as a match) because of that.

    Does not open csv_path in a write/append mode, so it is invisible to
    tests/tools/test_working_log_writer.py's sole-writer AST guard -- that guard scans for
    write-mode opens against agent-working/tickets/working_log.csv, and this function only reads.
    """
    if csv_path.exists():
        result = parse_working_log(csv_path)
        for parsed in result.rows:
            if parsed.record is None:
                continue
            if (
                parsed.record.get("ticket_id", "").strip() == ticket_id
                and parsed.record.get("title", "").strip() == title
            ):
                return parsed.record
    for row in parse_pending_working_log_shards(data_root):
        if row.get("ticket_id", "").strip() == ticket_id and row.get("title", "").strip() == title:
            return row
    return None


def build_records(
    ticket_id: str,
    tier: str,
    final_status: str,
    events: list[dict],
    start_ts: str | None,
    end_ts: str | None,
    workflow: str,
    provider: str,
    default_agent: str,
    now: str | None = None,
    session_id: str | None = None,
    resolution: "hand_closure_time.Resolution | None" = None,
) -> tuple[dict, list[dict]]:
    """Expands a minimal `events` list (phase/status/summary per entry) into a full run record
    plus a full event-record batch, both matching record_run.py's/record_events.py's own REQUIRED
    field sets exactly -- so the two modules' own `validate_record()` accepts the output unchanged.
    """
    now = now or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    execution_id = f"{provider}-{ticket_id}-{int(time.time() * 1000)}"

    run_record = {
        "run_id": ticket_id,
        "execution_id": execution_id,
        "provider": provider,
        "ticket_id": ticket_id,
        "start_ts": resolution.start_ts if resolution else start_ts or now,
        "end_ts": resolution.end_ts if resolution else end_ts or now,
        "workflow": workflow,
        "tier": tier,
        "final_status": final_status,
        "agent_count": len(events),
        "execution_mode": "hand",
        # TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS: provenance of start/end (declared | tool_activity | unknown)
        # and the closing session; absent on rows that predate the fields
        **({"duration_source": resolution.duration_source} if resolution else {}),
        **({"session_id": session_id} if resolution else {}),
        **({"claim_peers": resolution.claim_peers} if resolution and resolution.claim_peers is not None else {}),
    }

    event_records = [
        {
            "run_id": ticket_id,
            "execution_id": execution_id,
            "provider": provider,
            "ticket_id": ticket_id,
            "seq": i,
            **({"session_id": session_id} if resolution else {}),
            "phase": e["phase"],
            "agent": e.get("agent", default_agent),
            "status": e["status"],
            "summary": e["summary"],
            "ts": e.get("ts", now),
            # optional advisory list carried verbatim (TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS);
            # the key is absent, never a false [], when the event has none
            **({"test_quality_findings": e["test_quality_findings"]} if e.get("test_quality_findings") is not None else {}),
            **({"test_quality_findings_normalized": e["test_quality_findings_normalized"]} if e.get("test_quality_findings_normalized") is not None else {}),
            **({"tests_read": e["tests_read"]} if e.get("tests_read") is not None else {}),
        }
        for i, e in enumerate(events, start=1)
    ]

    return run_record, event_records


def attach_session_window_cost(event_records: list[dict], claimed: tuple[dict, ...] | list[dict]) -> list[dict]:
    """TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION: put the cost of the rows this closure claimed (the closing session's
    unattributed `tools.jsonl` rows, see `hand_closure_time`) on the FINAL event that has no sidecar attribution, with
    `cost_source: "session_window"`. The claim is one ticket-level total: phases are not resolved (the events share the
    closure time), so consumers must read `cost_source` before using a per-phase figure. Nothing claimed -> the keys stay
    absent, never a 0; a row with a sidecar `run_id` is never in `claimed`."""
    if not claimed:
        return event_records
    target = next((i for i in range(len(event_records) - 1, -1, -1) if "cost_source" not in event_records[i]), None)
    if target is None:
        return event_records
    out = list(event_records)
    out[target] = {**out[target], "tool_call_count": len(claimed),
                   "cost_proxy_score": record_events.compute_cost_proxy_score(list(claimed)), "cost_source": "session_window"}
    return out


def remove_stale_active_copies(ticket_id: str, tickets_root: Path = Path("agent-working/tickets")) -> list[str]:
    """Delete same-basename copies of a CLOSED ticket under `todos/` (recursively) and `inprogress/`, returning
    the removed paths. Only when the ticket's own `done/` file exists, so an unclosed ticket is never touched.
    A ticket filed directly into `todos/` is the normal planner hand-off and CLAUDE.md only tells a lane to delete
    a `todos/{folder}/` source, so the stale copy otherwise survives and the closed-ticket-resurrection corpus test
    fails at PR time (TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS)."""
    name = f"{ticket_id}.md"
    done = tickets_root / "done"
    if not (done / name).exists() and not any(done.glob(f"*/{name}")):
        return []
    removed = []
    for active in ("todos", "inprogress"):
        base = tickets_root / active
        for path in sorted(base.rglob(name)) if base.is_dir() else []:
            path.unlink()
            removed.append(path.as_posix())
    return removed


def check_sidecar_matches_ticket(ticket_id: str) -> str | None:
    """Advisory-only: warns (returns a message, never raises) when `.claude/current_run`'s own
    `run_id` doesn't match the ticket about to be closed.

    This module's own docstring already documents the EXPECTED, benign case: "a hand-orchestrating
    session never has a live per-phase sidecar during the actual work, so an unattributed phase
    correctly gets no such keys at all" -- no sidecar file at all is normal and fine. This check
    catches a DIFFERENT, WORSE case: a STALE sidecar left over from an EARLIER ticket, never
    cleared or updated when the session moved on to unrelated work. Every real tool call made
    since then gets silently attributed to the old (run_id, seq) instead of the ticket that's
    actually running -- corrupting `tool_call_count`/`cost_proxy_score` for BOTH the old ticket
    (inflated, often all bunched into whatever `seq` was last written) and the new one (starved,
    reading as `0`/unattributed rather than the real count).

    Confirmed real, not hypothetical: `TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT`
    -- a sidecar written once for one hotfix's own Implement phase was never updated across two
    entirely separate subsequent tickets' real work (5.5 hours, 170 real tool-call rows), which
    `tests/tools/test_tool_call_count_mismatch_check.py` flagged before that check's own blocking
    ceiling was removed by `TCK-20260922-TOOL-CALL-COUNT-MISMATCH-RATCHET-REPORT-ONLY`.

    Prefers the session-scoped sidecar (`.claude/current_run.$CLAUDE_CODE_SESSION_ID`) when
    present, matching this repo's own established precedent elsewhere (multiple concurrent
    sessions share the unscoped file); falls back to the unscoped file otherwise.
    """
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    candidates = []
    if session_id:
        candidates.append(Path(f".claude/current_run.{session_id}"))
    candidates.append(Path(".claude/current_run"))

    for path in candidates:
        if not path.exists():
            continue
        try:
            sidecar = json.loads(path.read_text())
        except Exception:
            continue
        sidecar_run_id = sidecar.get("run_id")
        if sidecar_run_id and sidecar_run_id != ticket_id:
            return (
                f"sidecar-staleness: {path} still has run_id={sidecar_run_id!r} (seq="
                f"{sidecar.get('seq')!r}), which does not match --ticket-id {ticket_id!r}. If "
                f"this sidecar was written for a DIFFERENT, earlier ticket and never cleared or "
                f"updated, every real tool call made since then has likely been misattributed to "
                f"that stale run_id — corrupting both tickets' tool_call_count/cost_proxy_score. "
                f"Clear or update the sidecar before closing further tickets. See "
                f"TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT for a real, "
                f"diagnosed instance of exactly this."
            )
        return None
    return None


def clear_sidecar_if_matches(ticket_id: str) -> None:
    """Clear `.claude/current_run`/`.claude/current_run.$CLAUDE_CODE_SESSION_ID` immediately
    after this ticket's closure has been recorded, if either still holds this ticket's own
    `run_id` -- never a different one (see below).

    TCK-20260922-HAND-ORCHESTRATION-SIDECAR-POST-SNAPSHOT-ACCUMULATION-INCIDENT: a *different*
    variant from the one `check_sidecar_matches_ticket()` above catches. There, the sidecar's
    `run_id` correctly matched the ticket at the moment this script ran (no warning fired) --
    the corruption happened AFTER this script's own ground-truth snapshot: real tool calls for
    this same ticket's remaining closure steps (registry regen, staging-to-stored migration,
    `git add`/`commit`) kept accumulating onto the same, now-already-recorded `(run_id, seq)`
    pair, because nothing cleared the sidecar once its snapshot was taken. Confirmed real via 3
    fresh instances found the same day `check_sidecar_matches_ticket()`'s own prior ceiling raise
    landed: `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT`,
    `TCK-20260921-CAVEMAN-CLOSE-OUT`, `TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT`.

    Deliberately only clears a sidecar that still holds THIS ticket_id -- if it already holds a
    DIFFERENT one (the stale-sidecar case `check_sidecar_matches_ticket()` already warned about
    above, in this same call), clearing it here would destroy that evidence rather than fix
    anything; leave it exactly as `check_sidecar_matches_ticket()`'s own warning describes it.
    Never raises -- a failure to clear must not fail the closure recording that already
    succeeded.
    """
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    candidates = []
    if session_id:
        candidates.append(Path(f".claude/current_run.{session_id}"))
    candidates.append(Path(".claude/current_run"))
    empty = {
        "run_id": None, "seq": None, "phase": None, "agent": None,
        "execution_id": None, "provider": None, "ticket_id": None,
    }
    for path in candidates:
        if not path.exists():
            continue
        try:
            sidecar = json.loads(path.read_text())
        except Exception:
            continue
        if sidecar.get("run_id") == ticket_id:
            try:
                path.write_text(json.dumps(empty))
            except OSError:
                pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--tier", required=True, choices=sorted(CANONICAL_TIERS - {"n/a"}))
    parser.add_argument("--events", required=True, help="JSON array of {phase, status, summary, ts?, agent?}")
    parser.add_argument("--final-status", default="DONE")
    parser.add_argument("--start-ts", default=None, help="ISO-8601; defaults to now")
    parser.add_argument("--end-ts", default=None, help="ISO-8601; defaults to now")
    parser.add_argument("--workflow", default="implement-ticket")
    parser.add_argument("--provider", default="claude")
    parser.add_argument("--agent", default="claude", help="Default agent value for events that don't override it")
    parser.add_argument("--title", required=True, help="Ticket title, for agent-working/tickets/working_log.csv")
    parser.add_argument("--log-summary", required=True, help="One-sentence summary for agent-working/tickets/working_log.csv")
    parser.add_argument(
        "--artifacts-path",
        default=None,
        help="Defaults to agent-working/stored_artifacts/<ticket-id> for standard/epic tier, "
        "'none (hotfix — no staging artifacts)' for hotfix",
    )
    args = parser.parse_args()

    sidecar_warning = check_sidecar_matches_ticket(args.ticket_id)
    if sidecar_warning:
        print(f"WARNING: {sidecar_warning}", file=sys.stderr)

    try:
        events = json.loads(args.events)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in --events: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(events, list) or not events:
        print("ERROR: --events must be a non-empty JSON array", file=sys.stderr)
        sys.exit(1)

    for i, e in enumerate(events):
        missing = {f for f in ("phase", "status", "summary") if f not in e or e[f] is None}
        if missing:
            print(f"ERROR: events[{i}] missing required fields {sorted(missing)}", file=sys.stderr)
            sys.exit(1)

    bad_agents = unregistered_agents(args.ticket_id, args.agent, events)
    if bad_agents:
        print(
            f"ERROR: unregistered agent literal(s) {bad_agents}; nothing was written. Allowed: "
            f"{_allowed_agents_text(args.ticket_id)}. A hand-orchestrated close normally uses "
            "--agent claude.",
            file=sys.stderr,
        )
        sys.exit(1)

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    resolution = hand_closure_time.resolve_for_session(
        now, args.start_ts, args.end_ts, os.environ.get("CLAUDE_CODE_SESSION_ID") or None, AGENT_MONITORING / "data")
    run_record, event_records = build_records(
        args.ticket_id, args.tier, args.final_status, events,
        args.start_ts, args.end_ts, args.workflow, args.provider, args.agent,
        now=now, session_id=os.environ.get("CLAUDE_CODE_SESSION_ID") or None, resolution=resolution,
    )

    run_errors = record_run.validate_record(run_record)
    if run_errors:
        for err in run_errors:
            print(f"ERROR (run record): {err}", file=sys.stderr)
        sys.exit(1)

    event_errors = []
    for i, record in enumerate(event_records):
        for err in record_events.validate_record(record):
            event_errors.append(f"events[{i}] ({record.get('phase')}): {err}")
    if event_errors:
        for err in event_errors:
            print(f"ERROR (event record): {err}", file=sys.stderr)
        sys.exit(1)

    for record in event_records:
        record_events.warn_vocabulary_drift(record)

    run_record["duration_s"] = (
        None if run_record["duration_source"] == hand_closure_time.UNKNOWN else record_run.compute_duration_s(run_record))
    if run_record["duration_s"] is None:  # unknown, or an inverted declared span: never a duration, never 0
        run_record["duration_source"] = hand_closure_time.UNKNOWN
        run_record.pop("claim_peers", None)

    tool_stats = record_events.compute_tool_stats(event_records, omit_when_unattributed=True)
    for i, record in enumerate(event_records):
        key = (record.get("run_id"), record.get("seq"))
        if key in tool_stats:
            tool_call_count, cost_proxy_score = tool_stats[key]
            event_records[i] = {**record, "tool_call_count": tool_call_count, "cost_proxy_score": cost_proxy_score,
                                "cost_source": "sidecar"}
    event_records = attach_session_window_cost(event_records, resolution.claimed)

    # TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX: this was the headline bug -- this wrapper
    # (the one CLAUDE.md instructs every hand-orchestrated close to use) hardcoded the shared
    # paths here, never adopting TCK-20260924's per-identifier write target at all, so every
    # hand-orchestrated closure's run/event records landed in the shared files regardless of what
    # record_run.py/record_events.py's own (correctly per-identifier) write functions did when
    # called directly. Now delegates to the one shared resolver instead of re-deriving (a fourth
    # time) a formula that has already drifted once.
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    runs_file = resolve_write_target("runs", iso_week=iso_week)
    events_file = resolve_write_target("events", iso_week=iso_week)
    runs_file.parent.mkdir(parents=True, exist_ok=True)

    from writer import write_line, write_lines  # noqa: E402

    from session_role import stamp as stamp_session_role  # noqa: E402

    run_ok = write_line(runs_file, json.dumps(stamp_session_role(run_record), separators=(",", ":")))
    lines = [json.dumps(stamp_session_role(record), separators=(",", ":")) for record in event_records]
    events_ok = write_lines(events_file, lines)

    if not run_ok:
        print(f"WARNING: run-record append failed for run_id={args.ticket_id}", file=sys.stderr)
    if not events_ok:
        print(f"WARNING: event-record append failed for {len(event_records)} record(s)", file=sys.stderr)

    artifacts_path = args.artifacts_path
    if artifacts_path is None:
        artifacts_path = (
            "none (hotfix — no staging artifacts)"
            if args.tier == "hotfix"
            else f"{posix(STORED_ARTIFACTS)}/{args.ticket_id}"
        )

    # Cwd-relative by design -- see _existing_row_for()'s docstring
    # (TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS) for why this is safe here.
    working_log_path = TICKETS / "working_log.csv"
    existing = _existing_row_for(working_log_path, args.ticket_id, args.title)
    if existing is not None:
        print(
            f"ERROR: {working_log_path} already has a row for (ticket_id={args.ticket_id!r}, "
            f"title={args.title!r}) at timestamp {existing.get('timestamp')!r} -- refusing to "
            "append a duplicate. This is the double-write shape append_working_log_row() and "
            "this script produce when both are called for the same ticket close "
            "(TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE): if you "
            "already called append_working_log_row() directly for this ticket, do not also run "
            "this script for the working-log append -- it already performs that append "
            "internally. The run/event monitoring records above were still written.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        append_working_log_row(
            run_record["end_ts"], args.ticket_id, args.title, args.final_status, args.log_summary, artifacts_path,
        )
        log_ok = True
    except OSError as e:
        log_ok = False
        print(f"WARNING: working_log.csv append failed: {e}", file=sys.stderr)

    if not log_ok:
        print("WARNING: working_log.csv was not updated — append it manually", file=sys.stderr)

    for stale in remove_stale_active_copies(args.ticket_id):
        print(f"REMOVED stale active-directory copy of {args.ticket_id}: {stale}")

    try:
        generate_registry(
            Path(".").resolve(), Path("docs/REGISTRY.yaml").resolve(),
            include=[f"agent-working/tickets/done/{args.ticket_id}.md", f"agent-working/tickets/done/*/{args.ticket_id}.md",
                     f"agent-working/stored_artifacts/{args.ticket_id}"],
        )
    except Exception as e:  # noqa: BLE001 - registry regeneration must never fail a closure
        print(f"WARNING: docs/REGISTRY.yaml regeneration failed: {e}", file=sys.stderr)

    clear_sidecar_if_matches(args.ticket_id)

    print(f"DONE: recorded 1 run + {len(event_records)} event record(s) for {args.ticket_id}")
    _print_anomaly_validator_result()


if __name__ == "__main__":
    main()
