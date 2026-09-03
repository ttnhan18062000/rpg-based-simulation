#!/usr/bin/env python3
"""Resume-aware `seq` continuation lookup for TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION.

A ticket's run can be paused mid-pipeline and resumed later as a separate `implement-ticket.js`
invocation sharing the same `run_id`. Every `seq`-producing site in that file (`pushEvent`'s
`events.length + 1` and each `writeSidecar(events.length + 1, ...)` call) derives `seq` purely
from the resumed session's own in-memory `events` array, which restarts at 0 — so the resumed
session's `seq` values collide with the pre-pause session's, silently aliasing the new session's
tool-call attribution onto the prior session's `(run_id, seq)` buckets in `tools.jsonl`.

`compute_seq_offset(run_id, events)` looks up the max `seq` this `run_id` already has in
`agent-monitoring/events.jsonl` (the authoritative 1:1 per-call record — see this ticket's
investigation.md for why `events.jsonl`, not `tools.jsonl`, is the correct source) so the
resumed session's numbering can continue past it instead of restarting at 1.

Mirrors `scope_ticket_relocate.py`'s shape: a pure lookup function plus a `MARKER:`-prefixed-JSON
`__main__` entrypoint, so `.claude/workflows/implement-ticket.js` can call it via the same
`bash()` + `markerIndex`/`JSON.parse` pattern `resolveScopeTicketLocation()` already uses.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import load_data_glob  # noqa: E402

EVENTS_FILE = Path("agent-monitoring/data")


def compute_seq_offset(run_id: str, events: list) -> int:
    """Return the max prior `seq` already recorded for `run_id` in `events` (0 if none).
    Pure/read-only — never mutates `events` or its elements."""
    max_seq = 0
    for e in events:
        if e.get("run_id") != run_id:
            continue
        seq = e.get("seq")
        if isinstance(seq, int) and seq > max_seq:
            max_seq = seq
    return max_seq


if __name__ == "__main__":
    print("MARKER:" + json.dumps(compute_seq_offset(sys.argv[1], load_data_glob(EVENTS_FILE, "events"))))
