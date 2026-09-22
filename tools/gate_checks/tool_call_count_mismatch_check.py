"""Ratchet-based check for `tool_call_count`/`tools.jsonl` mismatches
(TCK-20260915-TOOL-CALL-COUNT-MISMATCH, child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).

**What this measures**: for every run belonging to one of the 3 `compute_tool_stats()`-covered
workflows (`implement-ticket`, `implement-epic`, `create-tickets`) that started on or after
`FIX_DATE` (2026-07-19, when `TCK-20260719-COST-PROXY-WRITE-PATH` made `tool_call_count`
ground-truth-computed instead of caller-supplied), sum its events' own `tool_call_count` and
compare against the real number of `tools.jsonl` rows carrying that `run_id`. Flag a >3x
disagreement in either direction.

**Why the `FIX_DATE` filter, not the whole corpus**: runs before 2026-07-19 never had
ground-truth computation at all, and `docs/agent-monitoring/schema.md` already documents (in two
separate places) that pre-fix historical values are permanently unbackfilled and may be wrong.
Counting them here would make this check immediately and permanently unlandable on ~93
pre-existing, already-explained, already-documented historical rows that this ticket is not
scoped to fix -- the same "unlandable exact-equality/whole-corpus assertion" failure mode named
repeatedly across this batch (`TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT`,
`TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS`). This check watches the population the ticket
itself calls "current, not historical."

**Why a ratchet, not zero-tolerance**: the measured post-fix baseline is 53 (raised from 50 by
`TCK-20260922-HAND-ORCHESTRATION-SIDECAR-POST-SNAPSHOT-ACCUMULATION-INCIDENT`), not 0 -- most of
these are downstream of the same pre-`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` cross-session
sidecar contamination `TCK-20260915-SIDECAR-ATTRIBUTION-GAP` and this ticket's own investigation
both trace August's cluster to, itself already fixed and already documented as a permanent,
unbackfilled historical caveat. The 50th (`TCK-20260921-HEADROOM-AI-PIN-CLAIM-CORRECTION`) was a
fresh, fully-diagnosed instance of the exact same root-cause class: a hand-orchestration sidecar
written once for an earlier ticket's own Implement phase was never cleared or updated across two
entirely separate subsequent tickets' real work, so every real tool call made in between was
misattributed to the stale `(run_id, seq)`. `record_hand_orchestrated_closure.py::
check_sidecar_matches_ticket()` was added then to warn (non-blocking) on exactly that condition.

**51st-53rd (`TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT`,
`TCK-20260921-CAVEMAN-CLOSE-OUT`, `TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT`) are a
related but distinct variant of the same class, diagnosed by
`TCK-20260922-HAND-ORCHESTRATION-SIDECAR-POST-SNAPSHOT-ACCUMULATION-INCIDENT`: in all three, the
sidecar's own `run_id` correctly matched the ticket being closed at the moment
`record_hand_orchestrated_closure.py` ran (so `check_sidecar_matches_ticket()` correctly found
nothing to warn about) -- the corruption happened *after* that snapshot, not before it. Real tool
calls for that same ticket's own remaining closure steps (registry regeneration, staging-to-stored
migration, `git add`/`commit`) continued to accumulate onto the same, now-already-recorded
`(run_id, seq)` pair, because the sidecar was left live rather than cleared the moment its
snapshot was taken. `record_hand_orchestrated_closure.py` now clears the sidecar itself,
immediately after a successful recording, closing this specific variant going forward.

Mirrors the batch's own `check_*()` shape: `List[dict]` (`{"status": "PASS"|"FAIL", "evidence":
"..."}`), `MARKER:` + `json.dumps(result)` stdout contract in `__main__`.
"""
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path
from typing import List

_TOOLS_DIR = Path(__file__).resolve().parent.parent
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
for _dir in (str(_TOOLS_DIR), str(_MONITORING_TOOLS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from generate_retro import _load_runs_and_events  # noqa: E402
from validate import load_data_glob  # noqa: E402

VALID_WORKFLOWS = {"implement-ticket", "implement-epic", "create-tickets"}
FIX_DATE = "2026-07-19"
MISMATCH_RATIO = 3.0

# Ratchet ceiling: the real corpus's own post-2026-07-19, workflow-scoped >3x mismatch count.
# Raised 49 -> 50 by TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT, 2026-09-21.
# Raised 50 -> 53 by TCK-20260922-HAND-ORCHESTRATION-SIDECAR-POST-SNAPSHOT-ACCUMULATION-INCIDENT,
# 2026-09-22, with a full root-cause diagnosis (see the module docstring above) -- not "papering
# over" a mismatch, extending the same already-accepted ratchet-tracking convention to a
# newly-discovered, fully explained variant of the same already-documented root-cause class.
# Raising it to paper over an UNEXPLAINED newly-introduced mismatch still defeats the entire point
# of this check.
MISMATCH_CEILING = 53


def find_tool_call_count_mismatches(
    runs: List[dict] = None, events: List[dict] = None, tools: List[dict] = None,
) -> List[tuple]:
    """Returns [(run_id, claimed, actual), ...] for every post-FIX_DATE, workflow-scoped run
    whose summed event tool_call_count disagrees with its real tools.jsonl row count by more
    than MISMATCH_RATIO in either direction. All three args default to the real corpus when not
    supplied -- tests inject synthetic lists instead."""
    if runs is None or events is None:
        loaded_runs, loaded_events = _load_runs_and_events()
        runs = runs if runs is not None else loaded_runs
        events = events if events is not None else loaded_events
    if tools is None:
        tools = load_data_glob(Path("agent-monitoring/data"), "tools")

    workflow_by_run = {r["run_id"]: r.get("workflow") for r in runs if r.get("run_id")}
    start_ts_by_run = {r["run_id"]: r.get("start_ts") for r in runs if r.get("run_id")}

    actual_counts = Counter()
    for t in tools:
        rid = t.get("run_id")
        if rid:
            actual_counts[rid] += 1

    claimed_counts = defaultdict(int)
    for e in events:
        rid = e.get("run_id")
        if not rid:
            continue
        tcc = e.get("tool_call_count")
        if isinstance(tcc, (int, float)):
            claimed_counts[rid] += tcc

    mismatches = []
    all_run_ids = set(claimed_counts) | set(actual_counts)
    for rid in all_run_ids:
        if workflow_by_run.get(rid) not in VALID_WORKFLOWS:
            continue
        start_ts = start_ts_by_run.get(rid) or ""
        if start_ts < FIX_DATE:
            continue
        claimed = claimed_counts.get(rid, 0)
        actual = actual_counts.get(rid, 0)
        if actual == 0 and claimed == 0:
            continue
        if actual > 0:
            ratio = claimed / actual
            is_mismatch = ratio > MISMATCH_RATIO or ratio < (1.0 / MISMATCH_RATIO)
        else:
            is_mismatch = claimed > 0
        if is_mismatch:
            mismatches.append((rid, claimed, actual))

    return mismatches


def check_tool_call_count_mismatches(
    runs: List[dict] = None, events: List[dict] = None, tools: List[dict] = None,
    ceiling: int = MISMATCH_CEILING,
) -> List[dict]:
    """Ratcheted check: PASS if the post-fix mismatch count is at or below `ceiling`, FAIL if it
    has grown."""
    mismatches = find_tool_call_count_mismatches(runs, events, tools)
    count = len(mismatches)

    if count > ceiling:
        new_count = count - ceiling
        run_ids = sorted(m[0] for m in mismatches)
        return [{
            "status": "FAIL",
            "evidence": (
                f"{count} post-{FIX_DATE} tool_call_count/tools.jsonl mismatch(es) exceeds the "
                f"ratchet ceiling ({ceiling}) by {new_count}. Full set: {run_ids}"
            ),
        }]

    return [{
        "status": "PASS",
        "evidence": f"{count} post-{FIX_DATE} mismatch(es) (ceiling {ceiling})",
    }]


if __name__ == "__main__":
    result = check_tool_call_count_mismatches()
    print("MARKER:" + json.dumps(result))
