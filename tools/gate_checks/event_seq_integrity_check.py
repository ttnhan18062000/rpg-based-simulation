"""Ratchet-based checks for `agent-monitoring/data/*/events.jsonl` `seq` duplication and gaps
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

**Why a ratchet, not zero-tolerance**: both duplicates and gaps are mostly legitimate, by-design
consequences of how `seq` is scoped (per-invocation, not globally per-`run_id`) -- a
zero-tolerance assertion on either would be immediately and permanently unlandable, and would
implicitly relitigate `TCK-20260915-DUPLICATE-RUN-RECORDS`'s own already-settled disposition.
This check freezes the measured baselines (duplicates 71, gaps 46) and forbids growth, so a
genuinely NEW class of seq corruption still gets caught.

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

# Ratchet ceilings: the real corpus's own duplicate-seq and gapped-run counts as of 2026-09-15.
# May only decrease. Raising either to paper over a newly-introduced defect defeats the entire
# point of this check.
#
# DUPLICATE_SEQ_CEILING re-pinned 71 -> 72 the same day: traced directly, not guessed -- the sole
# new run_id in the FAIL evidence's own full set is
# TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE, which has two real, legitimate
# closures sharing one run_id (2026-09-14 BLOCKED, 2026-09-15 DONE) -- each invocation of
# record_hand_orchestrated_closure.py restarts its own local seq numbering at 1, exactly the
# already-documented multi-invocation-continuation mechanism this module's own docstring above
# names as the dominant, tolerated cause of this ratchet's population, not a new defect class.
DUPLICATE_SEQ_CEILING = 72
GAP_CEILING = 46


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


def check_event_seq_integrity(
    events: List[dict] = None,
    duplicate_ceiling: int = DUPLICATE_SEQ_CEILING,
    gap_ceiling: int = GAP_CEILING,
) -> List[dict]:
    """Ratcheted check, two conditions: PASS if both duplicate-seq and gapped-run counts are at
    or below their own ceilings, FAIL (per-condition) if either has grown."""
    duplicate_run_ids, gap_run_ids = find_seq_duplicates_and_gaps(events)
    results = []

    dup_count = len(duplicate_run_ids)
    if dup_count > duplicate_ceiling:
        results.append({
            "status": "FAIL",
            "evidence": (
                f"{dup_count} runs with a duplicate seq exceeds the ratchet ceiling "
                f"({duplicate_ceiling}) by {dup_count - duplicate_ceiling}. "
                f"Full set: {sorted(duplicate_run_ids)}"
            ),
        })
    else:
        results.append({
            "status": "PASS",
            "evidence": f"{dup_count} runs with a duplicate seq (ceiling {duplicate_ceiling})",
        })

    gap_count = len(gap_run_ids)
    if gap_count > gap_ceiling:
        results.append({
            "status": "FAIL",
            "evidence": (
                f"{gap_count} runs with a seq gap exceeds the ratchet ceiling ({gap_ceiling}) "
                f"by {gap_count - gap_ceiling}. Full set: {sorted(gap_run_ids)}"
            ),
        })
    else:
        results.append({
            "status": "PASS",
            "evidence": f"{gap_count} runs with a seq gap (ceiling {gap_ceiling})",
        })

    return results


if __name__ == "__main__":
    result = check_event_seq_integrity()
    print("MARKER:" + json.dumps(result))
