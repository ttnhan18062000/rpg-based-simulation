"""Tests for tools/agent-monitoring/run_dedup.py (TCK-20260915-DUPLICATE-RUN-RECORDS).

Coverage: grouping correctness (including a real false-positive this module's own first draft
produced and was corrected for), latest-record selection, and a real-corpus pin of the measured
duplicate classification.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from run_dedup import (  # noqa: E402
    classify_duplicate_groups,
    dedupe_to_latest_per_execution,
    execution_key,
    group_runs_by_execution,
    latest_in_group,
)


def test_execution_key_groups_by_run_id_execution_id_start_ts():
    a = {"run_id": "TCK-A", "execution_id": "exec-1", "start_ts": "2026-01-01T00:00:00Z"}
    b = {"run_id": "TCK-A", "execution_id": "exec-1", "start_ts": "2026-01-01T00:00:00Z"}
    assert execution_key(a, 0) == execution_key(b, 1)


def test_execution_key_different_execution_id_not_grouped():
    a = {"run_id": "TCK-A", "execution_id": "exec-1", "start_ts": "2026-01-01T00:00:00Z"}
    b = {"run_id": "TCK-A", "execution_id": "exec-2", "start_ts": "2026-01-01T00:00:00Z"}
    assert execution_key(a, 0) != execution_key(b, 1)


def test_execution_key_groups_execution_id_less_records_by_run_id_and_start_ts():
    a = {"run_id": "TCK-A", "start_ts": "2026-01-01T00:00:00Z"}
    b = {"run_id": "TCK-A", "start_ts": "2026-01-01T00:00:00Z"}
    assert execution_key(a, 0) == execution_key(b, 1)


def test_execution_key_two_records_both_missing_start_ts_are_not_grouped():
    """The real false positive found while building this module: two totally unrelated
    pre-schema-unification records for the same run_id, both missing start_ts, must never be
    treated as an "identical duplicate" just because both happen to lack the field."""
    a = {"run_id": "TCK-OLD", "seq": 2, "status": "complete"}
    b = {"run_id": "TCK-OLD", "seq": 5, "status": "completed"}
    assert execution_key(a, 0) != execution_key(b, 1)


def test_group_runs_by_execution_preserves_singletons():
    runs = [
        {"run_id": "TCK-A", "execution_id": "e1", "start_ts": "t1"},
        {"run_id": "TCK-B", "execution_id": "e2", "start_ts": "t2"},
    ]
    groups = group_runs_by_execution(runs)
    assert len(groups) == 2
    assert all(len(g) == 1 for g in groups)


def test_latest_in_group_picks_highest_end_ts():
    early = {"end_ts": "2026-01-01T00:00:00Z", "agent_count": 3}
    late = {"end_ts": "2026-01-01T01:00:00Z", "agent_count": 2}
    assert latest_in_group([early, late]) == late


def test_latest_in_group_falls_back_to_agent_count_on_missing_end_ts():
    a = {"end_ts": None, "agent_count": 1}
    b = {"end_ts": None, "agent_count": 5}
    assert latest_in_group([a, b]) == b


def test_dedupe_to_latest_per_execution_collapses_progressive_group():
    runs = [
        {"run_id": "TCK-A", "execution_id": "e1", "start_ts": "t1",
         "final_status": "NEEDS_CHANGES", "end_ts": "2026-01-01T00:10:00Z", "agent_count": 3},
        {"run_id": "TCK-A", "execution_id": "e1", "start_ts": "t1",
         "final_status": "DONE", "end_ts": "2026-01-01T00:30:00Z", "agent_count": 9},
        {"run_id": "TCK-B", "execution_id": "e2", "start_ts": "t2",
         "final_status": "DONE", "end_ts": "2026-01-01T00:05:00Z", "agent_count": 2},
    ]
    result = dedupe_to_latest_per_execution(runs)
    assert len(result) == 2
    a_result = next(r for r in result if r["run_id"] == "TCK-A")
    assert a_result["final_status"] == "DONE"
    assert a_result["agent_count"] == 9


def test_classify_duplicate_groups_shapes():
    runs = [
        # progressive: different final_status
        {"run_id": "TCK-P", "execution_id": "ep", "start_ts": "tp", "final_status": "NEEDS_CHANGES", "end_ts": "e1"},
        {"run_id": "TCK-P", "execution_id": "ep", "start_ts": "tp", "final_status": "DONE", "end_ts": "e2"},
        # same status, different end_ts
        {"run_id": "TCK-S", "execution_id": "es", "start_ts": "ts", "final_status": "DONE", "end_ts": "e1"},
        {"run_id": "TCK-S", "execution_id": "es", "start_ts": "ts", "final_status": "DONE", "end_ts": "e2"},
        # identical outcome
        {"run_id": "TCK-I", "execution_id": "ei", "start_ts": "ti", "final_status": "DONE", "end_ts": "e1"},
        {"run_id": "TCK-I", "execution_id": "ei", "start_ts": "ti", "final_status": "DONE", "end_ts": "e1"},
        # not a duplicate at all
        {"run_id": "TCK-U", "execution_id": "eu", "start_ts": "tu", "final_status": "DONE", "end_ts": "e1"},
    ]
    result = classify_duplicate_groups(runs)
    assert result["total_duplicate_groups"] == 3
    assert len(result["progressive"]) == 1
    assert len(result["same_status_diff_end"]) == 1
    assert len(result["identical_outcome"]) == 1


_MEASUREMENT_CUTOFF_DATE = "2026-09-15"


def _start_ts_date(run: dict) -> str | None:
    """The `YYYY-MM-DD` date `run["start_ts"]` falls on, or `None` if it can't be determined.

    Handles two shapes found in the real corpus: the current ISO-8601 string schema
    (`"2026-09-15T12:00:00Z"` -- first 10 characters are the date), and a handful of pre-schema-
    unification legacy records (`TCK-20260619-E53D*` and one `FOLDER-*` batch record) that carry
    `start_ts` as a raw Unix epoch number instead. A record with no `start_ts` at all, or one that
    is neither a string nor a number, returns `None` -- see the test below for why treating these
    as "excluded" rather than crashing or guessing is safe here."""
    ts = run.get("start_ts")
    if not ts:
        return None
    if isinstance(ts, str):
        return ts[:10]
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except (OverflowError, OSError, ValueError):
            return None
    return None


def test_real_corpus_duplicate_classification_matches_measured_baseline():
    """Pins the 2026-09-15 measurement from the ticket that introduced this test
    (TCK-20260915-DUPLICATE-RUN-RECORDS), re-measured and corrected by
    TCK-20260929-RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS.

    All-time counts over runs.jsonl's *entire* history are not a closed, non-growing count --
    every legitimate re-dispatch of any ticket (a gate failure fixed and re-run, exactly what
    TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE did) adds a new "progressive" duplicate
    group and would break an unscoped exact-equality assertion forever. What IS closed and
    non-growing is the population of runs whose `start_ts` falls **on or before the 2026-09-15
    measurement date** (inclusive of the whole day) -- that slice of history cannot change no
    matter how many new runs are recorded afterward. Scoping to it, then asserting exact equality
    against it, is what makes exact equality the right assertion shape here rather than a >=
    ceiling.

    A run whose `start_ts` can't be dated (missing entirely, or an unparseable type) is excluded
    from the scoped window rather than guessed at, and this is provably safe: `execution_key()`
    (see run_dedup.py) already treats any record with a falsy `start_ts` as its own forced
    singleton group (keyed by its list position), so such a record can never be part of a
    duplicate group -- whether it's included or excluded from this date filter has zero effect on
    the counts below. Measured directly: as of the 2026-09-15 cutoff, 105 of the corpus's 1761
    runs have no determinable `start_ts`; including or excluding them from the scoped population
    yields identical classification results.
    """
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
    from generate_retro import _load_runs_and_events

    all_runs, _ = _load_runs_and_events()
    scoped_runs = [
        r for r in all_runs
        if (date := _start_ts_date(r)) is not None and date <= _MEASUREMENT_CUTOFF_DATE
    ]
    result = classify_duplicate_groups(scoped_runs)
    assert result["total_duplicate_groups"] == 66, (
        f"expected 66 duplicate groups among runs with start_ts <= {_MEASUREMENT_CUTOFF_DATE} "
        f"(measured 2026-09-15), got {result['total_duplicate_groups']} -- this window is closed "
        f"and must never grow on its own; if it moved, something re-dated a historical run or "
        f"changed classify_duplicate_groups()'s own logic -- re-measure and investigate why "
        f"before touching this pin, don't just raise it blindly"
    )
    assert len(result["progressive"]) == 63
    assert len(result["same_status_diff_end"]) == 2
    assert len(result["identical_outcome"]) == 1
