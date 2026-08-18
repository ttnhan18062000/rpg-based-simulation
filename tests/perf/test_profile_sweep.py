"""
Unit tests for scripts/profile_sweep.py's pure analysis functions.

Deliberately does not run a full sweep (cProfile over real Kernel ticks across scenarios/tiers)
in this file — that's a slow, manually-invoked dev diagnostic, not a CI-tier unit test. These
tests cover the hotspot-extraction and cross-scenario-classification logic in isolation, since
those are the parts a future contributor is most likely to need to change or trust.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from profile_sweep import (
    extract_top_hotspots,
    classify_cross_scenario,
    compute_tick_timing,
    HotspotRecord,
)


def _fake_stats(entries):
    """
    Build a stand-in for pstats.Stats exposing just the .stats dict shape
    extract_top_hotspots reads: {(file, line, func): (cc, nc, tt, ct, callers)}.
    """
    return SimpleNamespace(stats=entries)


def test_extract_top_hotspots_sorts_by_cumtime_descending():
    stats = _fake_stats(
        {
            ("a.py", 10, "cheap"): (1, 1, 0.001, 0.001, {}),
            ("b.py", 20, "expensive"): (5, 5, 0.010, 0.500, {}),
            ("c.py", 30, "medium"): (2, 2, 0.005, 0.050, {}),
        }
    )
    result = extract_top_hotspots(stats, n=3)
    assert [r.function for r in result] == ["expensive", "medium", "cheap"]
    assert result[0].cumtime_ms == 500.0


def test_extract_top_hotspots_respects_top_n():
    stats = _fake_stats(
        {(f"f{i}.py", i, f"fn{i}"): (1, 1, 0.001 * i, 0.001 * i, {}) for i in range(10)}
    )
    result = extract_top_hotspots(stats, n=3)
    assert len(result) == 3


def test_extract_top_hotspots_recursive_call_format():
    # cc != nc signals recursion; the function must format ncalls as "nc/cc" in that case.
    stats = _fake_stats({("r.py", 1, "recurse"): (2, 5, 0.001, 0.010, {})})
    result = extract_top_hotspots(stats, n=1)
    assert result[0].ncalls == "5/2"


def test_classify_cross_scenario_splits_shared_and_unique():
    shared = HotspotRecord("shared_fn", "shared.py", 1, "10", 1.0, 10.0, 1.0)
    only_a = HotspotRecord("a_only", "a.py", 2, "10", 1.0, 5.0, 0.5)
    only_b = HotspotRecord("b_only", "b.py", 3, "10", 1.0, 3.0, 0.3)

    per_run = {
        "scenario_a": [shared, only_a],
        "scenario_b": [shared, only_b],
    }
    cross, specific = classify_cross_scenario(per_run)

    assert len(cross) == 1
    assert cross[0]["function"] == "shared_fn"
    assert cross[0]["seen_in"] == ["scenario_a", "scenario_b"]

    assert [h["function"] for h in specific["scenario_a"]] == ["a_only"]
    assert [h["function"] for h in specific["scenario_b"]] == ["b_only"]


def test_classify_cross_scenario_keeps_highest_cumtime_representative():
    # Same (file, line, function) location seen with two different cumtime readings
    # across runs — the representative record kept should be the larger one.
    low = HotspotRecord("fn", "x.py", 1, "10", 1.0, 2.0, 0.2)
    high = HotspotRecord("fn", "x.py", 1, "10", 1.0, 9.0, 0.9)
    per_run = {"run1": [low], "run2": [high]}
    cross, _specific = classify_cross_scenario(per_run)
    assert cross[0]["cumtime_ms"] == 9.0


def test_compute_tick_timing_basic_stats():
    durations = [10.0, 20.0, 30.0, 40.0, 50.0]
    result = compute_tick_timing(durations)
    assert result["avg"] == 30.0
    assert result["max"] == 50.0
    assert result["p50"] == 30.0


def test_compute_tick_timing_empty_list_does_not_crash():
    result = compute_tick_timing([])
    assert result == {"avg": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0}
