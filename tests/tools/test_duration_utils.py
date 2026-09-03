"""Tests for tools/agent-monitoring/duration_utils.py (TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from duration_utils import PAUSE_THRESHOLD_SECONDS, _parse_ts, compute_active_idle_split  # noqa: E402


def _event(ts, phase, agent, seq=1):
    return {"ts": ts, "phase": phase, "agent": agent, "seq": seq}


def test_all_active_when_no_gap_exceeds_threshold():
    events = [
        _event("2026-01-01T00:00:00Z", "Scope", "ticket-scoper"),
        _event("2026-01-01T00:05:00Z", "Implement", "implementer"),
        _event("2026-01-01T00:09:00Z", "Verify", "done-checker"),
    ]
    result = compute_active_idle_split(
        "2026-01-01T00:00:00Z", "2026-01-01T00:10:00Z", events
    )
    assert result["idle_gap_s"] == 0.0
    assert result["active_duration_s"] == result["total_duration_s"] == 600.0


def test_single_large_gap_is_fully_idle():
    events = [_event("2026-01-01T00:00:00Z", "Scope", "ticket-scoper")]
    result = compute_active_idle_split(
        "2026-01-01T00:00:00Z", "2026-01-01T02:00:00Z", events
    )
    # start->event gap is 0; event->end gap is 7200s, over threshold.
    assert result["idle_gap_s"] == 7200.0
    assert result["active_duration_s"] == 0.0
    assert result["largest_gap_from"] == "Scope:ticket-scoper"
    assert result["largest_gap_to"] == "end"


def test_no_events_treats_entire_span_by_threshold():
    result = compute_active_idle_split("2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z", [])
    assert result["total_duration_s"] == 3600.0
    assert result["idle_gap_s"] == 3600.0  # single start->end gap, 1hr >= 1800s threshold
    assert result["active_duration_s"] == 0.0
    assert result["largest_gap_from"] == "start"
    assert result["largest_gap_to"] == "end"


def test_no_events_short_span_is_fully_active():
    result = compute_active_idle_split("2026-01-01T00:00:00Z", "2026-01-01T00:05:00Z", [])
    assert result["idle_gap_s"] == 0.0
    assert result["active_duration_s"] == 300.0


def test_seq_collision_orders_by_ts_not_seq():
    # Two events share seq=1 (a real pause/resume seq-reset scenario) but have real, distinct,
    # non-monotonic-with-seq timestamps. Ordering must follow ts, never seq.
    events = [
        _event("2026-01-01T00:30:00Z", "Plan", "planner", seq=1),
        _event("2026-01-01T00:01:00Z", "Scope", "ticket-scoper", seq=1),
    ]
    result = compute_active_idle_split(
        "2026-01-01T00:00:00Z", "2026-01-01T00:31:00Z", events
    )
    assert result["total_duration_s"] == 1860.0
    assert result["active_duration_s"] + result["idle_gap_s"] == result["total_duration_s"]
    assert result["active_duration_s"] >= 0.0
    assert result["idle_gap_s"] >= 0.0


def test_events_with_missing_or_non_string_ts_are_skipped():
    events = [
        {"phase": "Scope", "agent": "ticket-scoper"},  # missing ts entirely
        {"ts": None, "phase": "Investigate", "agent": "investigator"},
        {"ts": 12345, "phase": "Plan", "agent": "planner"},  # non-string ts
        _event("2026-01-01T00:05:00Z", "Implement", "implementer"),
    ]
    result = compute_active_idle_split(
        "2026-01-01T00:00:00Z", "2026-01-01T00:10:00Z", events
    )
    assert result is not None
    assert result["active_duration_s"] == 600.0


def test_unparseable_start_or_end_ts_returns_none():
    assert compute_active_idle_split(None, "2026-01-01T00:10:00Z", []) is None
    assert compute_active_idle_split("2026-01-01T00:00:00Z", "not-a-timestamp", []) is None
    assert compute_active_idle_split("", "", []) is None


def test_active_plus_idle_equals_total_duration_invariant():
    events = [
        _event("2026-01-01T00:01:00Z", "Scope", "ticket-scoper"),
        _event("2026-01-01T01:30:00Z", "Investigate", "investigator"),  # 89min gap, idle
        _event("2026-01-01T01:35:00Z", "Plan", "planner"),  # 5min gap, active
    ]
    result = compute_active_idle_split(
        "2026-01-01T00:00:00Z", "2026-01-01T02:00:00Z", events
    )
    assert result["active_duration_s"] + result["idle_gap_s"] == result["total_duration_s"]


def test_custom_pause_threshold_is_honored():
    events = [_event("2026-01-01T00:10:00Z", "Scope", "ticket-scoper")]
    # 10min gap: idle at a 5min threshold, active at the 30min default.
    result_default = compute_active_idle_split(
        "2026-01-01T00:00:00Z", "2026-01-01T00:10:00Z", events
    )
    result_strict = compute_active_idle_split(
        "2026-01-01T00:00:00Z", "2026-01-01T00:10:00Z", events, pause_threshold_s=300
    )
    assert result_default["idle_gap_s"] == 0.0
    assert result_strict["idle_gap_s"] == 600.0


def test_default_pause_threshold_matches_generate_retro_slow_runs_threshold():
    # Deliberate consistency check, not a coincidence -- see module docstring decision 1.
    assert PAUSE_THRESHOLD_SECONDS == 1800


def test_parse_ts_handles_z_suffix_and_rejects_garbage():
    assert _parse_ts("2026-01-01T00:00:00Z") is not None
    assert _parse_ts("not-a-timestamp") is None
    assert _parse_ts(None) is None
    assert _parse_ts(12345) is None


def test_real_corpus_simq_depth_social_reproduces_documented_gap():
    events = []
    for events_path in sorted((_REPO_ROOT / "agent-monitoring" / "data").glob("*/events.jsonl")):
        with events_path.open() as f:
            for line in f:
                row = json.loads(line)
                if row.get("run_id") == "TCK-20260710-SIMQ-DEPTH-SOCIAL":
                    events.append(row)
    assert len(events) == 10  # sanity: real corpus row still present with expected shape

    result = compute_active_idle_split(
        "2026-07-11T18:58:27Z", "2026-07-12T08:47:16Z", events
    )
    assert result["total_duration_s"] == 49729.0  # matches runs.jsonl's own duration_s
    # The documented ~590.6 min Investigate->Plan gap is the single largest gap.
    assert abs(result["largest_gap_s"] / 60 - 590.6) < 0.1
    assert result["largest_gap_from"] == "Investigate:investigator"
    assert result["largest_gap_to"] == "Plan:planner"
    # active_duration_s is materially smaller than the raw 828-min duration_s.
    assert result["active_duration_s"] / 60 < 828 / 2
    assert result["active_duration_s"] + result["idle_gap_s"] == result["total_duration_s"]


def test_largest_gap_boundary_labels_identify_correct_phase_transition():
    events = [
        _event("2026-01-01T00:01:00Z", "Scope", "ticket-scoper"),
        _event("2026-01-01T02:01:00Z", "Investigate", "investigator"),  # 2hr gap, largest
        _event("2026-01-01T02:06:00Z", "Plan", "planner"),
    ]
    result = compute_active_idle_split(
        "2026-01-01T00:00:00Z", "2026-01-01T02:10:00Z", events
    )
    assert result["largest_gap_from"] == "Scope:ticket-scoper"
    assert result["largest_gap_to"] == "Investigate:investigator"
