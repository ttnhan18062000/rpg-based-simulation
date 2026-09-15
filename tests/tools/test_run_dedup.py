"""Tests for tools/agent-monitoring/run_dedup.py (TCK-20260915-DUPLICATE-RUN-RECORDS).

Coverage: grouping correctness (including a real false-positive this module's own first draft
produced and was corrected for), latest-record selection, and a real-corpus pin of the measured
duplicate classification.
"""
import sys
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


def test_real_corpus_duplicate_classification_matches_measured_baseline():
    """Pins the exact 2026-09-15 measurement from investigation.md. All-time counts on
    runs.jsonl's own history before this date are a closed, non-growing count (unlike a live
    ratchet) -- an exact match is the correct assertion here, not a >= ceiling."""
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
    from generate_retro import _load_runs_and_events

    all_runs, _ = _load_runs_and_events()
    result = classify_duplicate_groups(all_runs)
    assert result["total_duplicate_groups"] == 66, (
        f"expected 66 duplicate groups (measured 2026-09-15), got "
        f"{result['total_duplicate_groups']} -- if new legitimate runs were added since, "
        f"re-measure and update this pin with the new number and date, don't just raise it blindly"
    )
    assert len(result["progressive"]) == 63
    assert len(result["same_status_diff_end"]) == 2
    assert len(result["identical_outcome"]) == 1
