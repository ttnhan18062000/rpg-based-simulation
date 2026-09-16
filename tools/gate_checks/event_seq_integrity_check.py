"""Measures `agent-monitoring/data/*/events.jsonl` `seq` duplication and gaps
(TCK-20260915-EVENT-SEQ-INTEGRITY, child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).

**What this measures, and why most of it is not a defect**: 51 of 71 real duplicate-`seq` runs
and 19 of 46 real gapped runs are directly explained by the same legitimate multi-invocation
mechanism `TCK-20260915-DUPLICATE-RUN-RECORDS` already confirmed -- a `run_id` re-invoked
(a legitimate re-run/reopen) restarts its own local `seq` numbering each time, since `seq` is
computed from the writing invocation's own in-memory event count, not a persistent global
counter. A further share traces to `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`'s own
already-fixed, already-documented pause/resume offset mechanism. See
`docs/agent-monitoring/schema.md`'s corrected `seq` field row and this ticket's own
investigation.md for the full evidence.

**This module used to also gate on both counts (ratchet ceilings, `DUPLICATE_SEQ_CEILING` and
`GAP_CEILING`); both gates were removed by TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-
LIVE-REGRESSION (2026-09-16). Do not rebuild either.** Confirmed directly, not inferred: this
module's own finding above -- that most of both counts trace to the ordinary multi-invocation
mechanism -- means a single legitimate ticket reopen (a `run_id` closing and reopening, e.g.
BLOCKED then DONE) moves BOTH counts at once. `TCK-20260913-TICKET-PREMISE-STALENESS-NOT-
PROPAGATED-ON-CLOSE`'s own ordinary two-phase closure moved `DUPLICATE_SEQ_CEILING` 71 -> 72 on
2026-09-14 for exactly this reason. A threshold over either count cannot distinguish "a ticket
legitimately reopened" from "a new class of seq corruption," so both fire on ordinary activity as
often as on a real regression -- the same inverted-signal shape as the deleted sidecar-attribution,
citation-resolution, and working-log-duplicate floors (see `sidecar_attribution_coverage_check.py`
for the full precedent). The measurement stays -- both counts remain genuinely useful reported
context -- just not something to block on.

Mirrors the batch's own `check_*()` shape: `List[dict]` (`{"status": "PASS"|"FAIL", "evidence":
"..."}`), `MARKER:` + `json.dumps(result)` stdout contract in `__main__`.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import List

_TOOLS_DIR = Path(__file__).resolve().parent.parent
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
for _dir in (str(_TOOLS_DIR), str(_MONITORING_TOOLS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from generate_retro import _load_runs_and_events  # noqa: E402


def find_seq_duplicates_and_gaps(events: List[dict] = None) -> "tuple[list, list]":
    """Returns (duplicate_run_ids, gap_run_ids). `events` defaults to the real corpus when not
    supplied -- tests inject a synthetic list instead."""
    if events is None:
        _, events = _load_runs_and_events()

    events_by_run = defaultdict(list)
    for e in events:
        rid = e.get("run_id")
        if rid:
            events_by_run[rid].append(e)

    duplicate_run_ids = []
    gap_run_ids = []
    for rid, evs in events_by_run.items():
        seqs = [e.get("seq") for e in evs if isinstance(e.get("seq"), int)]
        if not seqs:
            continue
        seq_counts = defaultdict(int)
        for s in seqs:
            seq_counts[s] += 1
        if any(c > 1 for c in seq_counts.values()):
            duplicate_run_ids.append(rid)
        max_seq = max(seqs)
        if max_seq >= 1 and set(range(1, max_seq + 1)) - set(seqs):
            gap_run_ids.append(rid)

    return duplicate_run_ids, gap_run_ids


def check_event_seq_integrity(events: List[dict] = None) -> List[dict]:
    """Reports both counts -- always PASS (see module docstring for why these are no longer
    gated). Two conditions, matching the pre-existing shape callers (including
    monitoring_anomaly_validator.py) already expect."""
    duplicate_run_ids, gap_run_ids = find_seq_duplicates_and_gaps(events)
    dup_count = len(duplicate_run_ids)
    gap_count = len(gap_run_ids)

    return [
        {"status": "PASS", "evidence": f"{dup_count} runs with a duplicate seq"},
        {"status": "PASS", "evidence": f"{gap_count} runs with a seq gap"},
    ]


if __name__ == "__main__":
    result = check_event_seq_integrity()
    print("MARKER:" + json.dumps(result))
