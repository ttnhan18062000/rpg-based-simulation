"""Ratchet-based checks for three named historical integrity-debt items from
TCK-20260915-MONITORING-INTEGRITY-BACKLOG (child of
TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).

**Item 2 corrected scope**: the ticket's own text named "34 September closures" with no run
record at all, framed as one tight, identifiable batch. A full, all-time re-derivation (not just
September) found 218 `working_log.csv` rows on/after `MONITORING_START` marked DONE with no
matching `run_id` in `runs.jsonl` -- the September cluster is a small, visible fraction of a much
larger, older gap. A sample cross-check found only ~18 of these are even loosely explainable by a
`FOLDER-*`/`EPIC-*` batch record's own text mentioning the ticket_id (and that overlap is a
fragile substring-match heuristic, not proof of real coverage) -- the great majority (~200) are
genuinely unexplained. None of the 218 can be backfilled: there is no way to reconstruct an
accurate historical execution record after the fact. This check ratchets the full, honestly
measured 218, not the ticket's own narrower 34.

**Item 4**: 66 `runs.jsonl` records and 55 `events.jsonl` records (excluding the `unknown-week`
shard, which item 5 covers separately) carry `ts`/`start_ts: None` -- all June-era (W24-W27),
predating a fix to whatever writer omitted the field. Unusable for any time-windowed query but not
retroactively reconstructable.

**Item 5**: `agent-monitoring/data/unknown-week/` holds 34 rows total (5 runs, 28 events, 1 tool
call) -- the shard `iso_week()`/week-sharding falls into when a record's `ts` can't be parsed into
an ISO week at all. Directly related to item 4 (an unparseable `ts` is exactly what routes a
record here), tracked separately since it is a distinct artifact (a whole shard directory, not a
field-level defect within otherwise-normal shards).

**Why a ratchet, not zero-tolerance or a fix**: all three items are historical, pre-existing data
defects with no accurate backfill possible -- the same "accept and document, freeze the baseline,
forbid growth" disposition this epic's `SEQUENCE.md` explicitly allows. A genuinely NEW instance
of any of the three (a regression in a currently-working writer) still fails this check.

Mirrors the batch's own `check_*()` shape: `List[dict]` (`{"status": "PASS"|"FAIL", "evidence":
"..."}`), `MARKER:` + `json.dumps(result)` stdout contract in `__main__`.
"""
import csv
import glob
import json
import sys
from pathlib import Path
from typing import List

_TOOLS_DIR = Path(__file__).resolve().parent.parent
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
_REPO_ROOT = _TOOLS_DIR.parent
for _dir in (str(_TOOLS_DIR), str(_MONITORING_TOOLS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from generate_retro import _load_runs_and_events  # noqa: E402

# Ratchet ceilings: the real corpus's own measured counts as of 2026-09-15. May only decrease.
# Raising any of them to paper over a newly-introduced instance defeats the point of this check.
NO_RUN_RECORD_CEILING = 218
UNUSABLE_TS_RUN_CEILING = 66
UNUSABLE_TS_EVENT_CEILING = 55
UNKNOWN_WEEK_ROW_CEILING = 34

MONITORING_START = "2026-06-07"
WORKING_LOG_PATH = _REPO_ROOT / "tickets" / "working_log.csv"
DATA_DIR = _REPO_ROOT / "agent-monitoring" / "data"


def find_working_log_rows_missing_run_record(
    run_ids: "set[str]" = None, working_log_path: Path = WORKING_LOG_PATH
) -> List[str]:
    """Item 2: every TCK-prefixed, DONE, on/after-MONITORING_START working_log.csv row whose
    ticket_id has no matching run_id anywhere in runs.jsonl. Malformed (non-6-field) rows are
    skipped rather than misread (see TCK-20260915-MONITORING-INTEGRITY-BACKLOG item 3 -- the same
    ticket that fixed the last 9 of these)."""
    if run_ids is None:
        runs, _ = _load_runs_and_events()
        run_ids = {r.get("run_id") for r in runs if r.get("run_id")}

    missing = []
    if not working_log_path.exists():
        return missing
    with open(working_log_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            if len(row) != 6:
                continue
            ts, tid, _title, status, _summary, _path = row
            if not tid.startswith("TCK-"):
                continue
            if "DONE" not in status:
                continue
            if ts < MONITORING_START:
                continue
            if tid not in run_ids:
                missing.append(tid)
    return missing


def find_unusable_ts_records(runs: List[dict] = None, events: List[dict] = None) -> "tuple[list, list]":
    """Item 4: (run_ids, event run_ids) with `start_ts`/`ts` of None, excluding the
    `unknown-week` shard (item 5 counts that shard separately)."""
    if runs is None or events is None:
        loaded_runs, loaded_events = _load_runs_and_events()
        runs = runs if runs is not None else loaded_runs
        events = events if events is not None else loaded_events

    bad_runs = [r.get("run_id") for r in runs if r.get("start_ts", r.get("ts")) is None]
    bad_events = [e.get("run_id") for e in events if e.get("ts") is None]
    return bad_runs, bad_events


def count_unknown_week_rows(data_dir: Path = DATA_DIR) -> int:
    """Item 5: total row count across every `*.jsonl` file directly under
    `agent-monitoring/data/unknown-week/`."""
    unknown_week_dir = data_dir / "unknown-week"
    if not unknown_week_dir.exists():
        return 0
    total = 0
    for path in glob.glob(str(unknown_week_dir / "*.jsonl")):
        with open(path, encoding="utf-8") as f:
            total += sum(1 for line in f if line.strip())
    return total


def _ratchet_result(label: str, count: int, ceiling: int, extra: str = "") -> dict:
    if count > ceiling:
        return {
            "status": "FAIL",
            "evidence": (
                f"{label}: {count} exceeds the ratchet ceiling ({ceiling}) by "
                f"{count - ceiling}.{(' ' + extra) if extra else ''}"
            ),
        }
    return {"status": "PASS", "evidence": f"{label}: {count} (ceiling {ceiling})"}


def check_monitoring_integrity_backlog(
    run_ids: "set[str]" = None,
    runs: List[dict] = None,
    events: List[dict] = None,
    working_log_path: Path = WORKING_LOG_PATH,
    data_dir: Path = DATA_DIR,
    no_run_record_ceiling: int = NO_RUN_RECORD_CEILING,
    unusable_ts_run_ceiling: int = UNUSABLE_TS_RUN_CEILING,
    unusable_ts_event_ceiling: int = UNUSABLE_TS_EVENT_CEILING,
    unknown_week_ceiling: int = UNKNOWN_WEEK_ROW_CEILING,
) -> List[dict]:
    """Four-condition ratchet: PASS per condition if at or below its own ceiling, FAIL if grown.
    All parameters default to the real corpus; tests inject synthetic values instead."""
    if runs is None or events is None:
        loaded_runs, loaded_events = _load_runs_and_events()
        runs = runs if runs is not None else loaded_runs
        events = events if events is not None else loaded_events
    if run_ids is None:
        run_ids = {r.get("run_id") for r in runs if r.get("run_id")}

    missing = find_working_log_rows_missing_run_record(run_ids, working_log_path)
    bad_runs, bad_events = find_unusable_ts_records(runs, events)
    unknown_week_count = count_unknown_week_rows(data_dir)

    return [
        _ratchet_result(
            "working_log DONE rows with no run record (item 2)", len(missing), no_run_record_ceiling,
        ),
        _ratchet_result(
            "runs.jsonl records with unusable ts (item 4)", len(bad_runs), unusable_ts_run_ceiling,
        ),
        _ratchet_result(
            "events.jsonl records with unusable ts (item 4)", len(bad_events), unusable_ts_event_ceiling,
        ),
        _ratchet_result(
            "unknown-week/ shard row count (item 5)", unknown_week_count, unknown_week_ceiling,
        ),
    ]


if __name__ == "__main__":
    result = check_monitoring_integrity_backlog()
    print("MARKER:" + json.dumps(result))
