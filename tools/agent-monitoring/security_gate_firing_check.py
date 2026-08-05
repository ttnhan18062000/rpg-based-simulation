#!/usr/bin/env python3
"""Read-only check: did the Security-Review gate actually fire on every completed
security-tagged ticket? (TCK-20260805-SECURITY-GATE-FIRING-MONITOR)

Distinct from generate_retro.py's compute_retro_metrics()'s `tag_breakdown_skill` section, which
already cross-references `security`-tagged runs against a Security-Review hit — but only as an
aggregate count for the weekly retro report. This module answers a narrower, stricter question
("which specific ticket(s), if any, are missing the hit") suitable for a gate-style pass/fail
check, not a reporting metric. generate_retro.py itself is never modified or duplicated here;
its private helpers are imported and reused, per retrieval_baseline_metrics.py's own precedent.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_retro import (  # noqa: E402
    _collect_tagged_tickets,
    _load_runs_and_events,
    _resolve_status,
)

# TCK-20260705-WORKFLOW-SECURITY-GATE is the ticket that added phase('Security-Review') to
# implement-ticket.js in the first place — its own implementation ran under the pre-gate version
# of the JS, so it structurally could not have fired a gate that did not yet exist while it ran.
# Excluded from both `missed` and `clean`, not flagged as a miss — a checker that flags its own
# founding ticket as broken would be a credibility-destroying false positive.
_BOOTSTRAP_EXCEPTION_TICKETS = frozenset({"TCK-20260705-WORKFLOW-SECURITY-GATE"})

_SECURITY_REVIEW_PHASE = "security-review"
_SECURITY_BLOCKED_STATUS = "SECURITY_BLOCKED"


def check_security_gate_firing(tickets_root: Path | None = None) -> dict:
    """Classifies every `security`-tagged ticket (except `_BOOTSTRAP_EXCEPTION_TICKETS`) into
    exactly one of `missed` / `clean` / `pending`:
      - `missed`: has at least one DONE-resolved runs.jsonl record, but no Security-Review event
        and no SECURITY_BLOCKED final_status anywhere in its run history — the gate should have
        fired on a completed run and did not.
      - `clean`: has at least one DONE-resolved runs.jsonl record, and a Security-Review event or
        SECURITY_BLOCKED final_status exists somewhere in its run history — the gate fired.
      - `pending`: has zero DONE-resolved runs.jsonl records (still in progress, blocked, or no
        run data recorded at all yet) — not yet evaluable, never silently dropped.
    Never mutates agent-monitoring/*.jsonl or any ticket file — read-only.
    """
    tickets_root = tickets_root if tickets_root is not None else Path(".")
    ticket_tag_map = _collect_tagged_tickets(tickets_root)
    runs, events = _load_runs_and_events()

    events_by_run = defaultdict(list)
    for e in events:
        events_by_run[e.get("run_id", "")].append(e)

    runs_by_id = defaultdict(list)
    for r in runs:
        runs_by_id[r.get("run_id", "")].append(r)

    missed, clean, pending, excluded = [], [], [], []

    for ticket_id, tags in sorted(ticket_tag_map.items()):
        if "security" not in tags:
            continue
        if ticket_id in _BOOTSTRAP_EXCEPTION_TICKETS:
            excluded.append(ticket_id)
            continue

        ticket_runs = runs_by_id.get(ticket_id, [])
        has_done = any(_resolve_status(r) == "DONE" for r in ticket_runs)
        if not has_done:
            pending.append(ticket_id)
            continue

        has_gate_hit = any(
            e.get("phase", "").casefold() == _SECURITY_REVIEW_PHASE
            for e in events_by_run.get(ticket_id, [])
        ) or any(_resolve_status(r) == _SECURITY_BLOCKED_STATUS for r in ticket_runs)

        (clean if has_gate_hit else missed).append(ticket_id)

    return {
        "missed": missed,
        "clean": clean,
        "pending": pending,
        "excluded": excluded,
        "derivation": (
            "Derived from generate_retro._collect_tagged_tickets (tickets/done/ + "
            "tickets/inprogress/ frontmatter, security tag) cross-referenced against "
            "generate_retro._load_runs_and_events's real runs.jsonl/events.jsonl. A ticket is "
            "only classified 'missed' or 'clean' once it has at least one DONE-resolved "
            "runs.jsonl record (an in-progress/blocked ticket has not necessarily reached the "
            "Security-Review phase yet, so it lands in 'pending' instead, never silently "
            "dropped). TCK-20260705-WORKFLOW-SECURITY-GATE is excluded (see "
            "_BOOTSTRAP_EXCEPTION_TICKETS comment) since it predates the gate's own existence. "
            "Not a duplicate of generate_retro.py's tag_breakdown_skill aggregate — this is a "
            "strict per-ticket pass/fail list, not a report metric."
        ),
    }


def main():
    report = check_security_gate_firing()
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if report["missed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
