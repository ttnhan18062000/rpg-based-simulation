"""Ratchet-based check for genuinely-accidental duplicate `agent-monitoring/data/*/runs.jsonl`
records (TCK-20260915-DUPLICATE-RUN-RECORDS, child of
TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).

**What this deliberately does NOT flag**: `writeMonitoring()` (`implement-ticket.js`) fires at
every gate exit point within one continuous execution, correctly keeping one stable
`(run_id, execution_id, start_ts)` identity across every call. A session that continues past a
gate failure (fixes it, keeps going) legitimately produces multiple `runs.jsonl` rows for that one
execution -- `NEEDS_CHANGES` -> `DOD_BLOCKED` -> `DONE`, each a real checkpoint. Measured directly
against the corpus and cross-checked against `events.jsonl`'s own phase timeline: 63 of 66
all-time duplicate-key groups show this shape (a different `final_status` per row) and are not a
defect. Counting these would make this check permanently red on healthy, by-design behavior.

**What this DOES flag**: `tools/agent-monitoring/run_dedup.py::classify_duplicate_groups()`'s
`identical_outcome` bucket -- records sharing `(run_id, execution_id, start_ts)` AND
`final_status` AND `end_ts`. Nothing distinguishes these; a legitimate continuation structurally
cannot produce this shape (it always changes `final_status` or reaches a later `end_ts`, since it
represents additional real work). This is the shape a genuine accidental duplicate write produces
-- confirmed for the one real 2026-09-15 baseline instance: a hand-typed `record_run.py --data`
invocation with a non-standard `-final`-suffixed `execution_id` (not the pipeline's own
`secrets.token_hex(4)` shape), most likely run twice with the same copy-pasted argument.

**Why a ratchet, not zero-tolerance**: the historical baseline is 1, not 0 -- the same
"unlandable exact-equality assertion" failure mode as
`TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` and this same epic's own
`SEQUENCE.md` discipline note. This check freezes 1 and forbids growth; it does not retroactively
resolve the historical instance (`runs.jsonl` is never rewritten, matching
`TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` items 1/6's precedent for `working_log.csv`).

Mirrors `working_log_duplicate_check.py`'s own shape: an aggregate `check_*()` function returning
`List[dict]` (`{"status": "PASS"|"FAIL", "evidence": "..."}`), a `MARKER:` + `json.dumps(result)`
stdout contract in `__main__`.
"""
import json
import sys
from pathlib import Path
from typing import List

_TOOLS_DIR = Path(__file__).resolve().parent.parent
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
for _dir in (str(_TOOLS_DIR), str(_MONITORING_TOOLS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from generate_retro import _load_runs_and_events  # noqa: E402
from run_dedup import classify_duplicate_groups  # noqa: E402

# Ratchet ceiling: the real corpus's own genuinely-accidental ("identical outcome") duplicate
# count as of 2026-09-15. May only decrease. Raising it to paper over a newly-introduced
# accidental duplicate defeats the entire point of this check.
IDENTICAL_OUTCOME_CEILING = 1


def check_duplicate_run_records(
    runs: List[dict] = None, ceiling: int = IDENTICAL_OUTCOME_CEILING
) -> List[dict]:
    """Ratcheted check: PASS if the count of genuinely-ambiguous ("identical outcome") duplicate
    run-record groups is at or below `ceiling`, FAIL if it has grown.

    `runs` defaults to the real corpus (loaded via `_load_runs_and_events()`) when not supplied --
    tests inject a synthetic list instead of touching the real `agent-monitoring/data/` shards."""
    if runs is None:
        runs, _ = _load_runs_and_events()
    classification = classify_duplicate_groups(runs)
    identical_groups = classification["identical_outcome"]
    count = len(identical_groups)

    if count > ceiling:
        new_count = count - ceiling
        run_ids = sorted({g[0].get("run_id") for g in identical_groups})
        return [{
            "status": "FAIL",
            "evidence": (
                f"{count} genuinely-ambiguous duplicate run-record group(s) exceeds the ratchet "
                f"ceiling ({ceiling}) by {new_count} -- a new accidental duplicate was likely "
                f"introduced. Affected run_id(s): {run_ids}"
            ),
        }]

    return [{
        "status": "PASS",
        "evidence": (
            f"{count} genuinely-ambiguous duplicate run-record group(s) (ceiling {ceiling}); "
            f"{len(classification['progressive'])} legitimate multi-checkpoint continuations and "
            f"{len(classification['same_status_diff_end'])} ambiguous-but-plausible continuations "
            f"correctly not counted against this ratchet"
        ),
    }]


if __name__ == "__main__":
    result = check_duplicate_run_records()
    print("MARKER:" + json.dumps(result))
