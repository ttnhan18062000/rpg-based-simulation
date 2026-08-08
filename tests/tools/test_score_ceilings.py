"""TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE — structural_ceiling classification."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from simq_ceiling import (  # noqa: E402
    FLAG_GATED_PILLAR_CEILINGS,
    TIME_GATE_PILLAR,
    _load_time_gates,
    lookup_ceiling,
    tick_budget_ceilings,
)


def test_tick_budget_ceiling_flags_short_scenarios():
    ceilings = tick_budget_ceilings()
    # sandbox_world_seed42_200t: 200 ticks. zero_combat_by_tick=200 -> ticks <= threshold -> flagged.
    assert ("sandbox_world_seed42_200t", "COMBAT") in ceilings
    # A 1000t scenario should clear the same threshold comfortably.
    thousand_tick_combat_pairs = [
        k for k in ceilings if k[1] == "COMBAT" and k[0].endswith("_1000t")
    ]
    assert thousand_tick_combat_pairs == []


def test_tick_budget_covers_confirmed_time_gates():
    time_gates = _load_time_gates()
    for gate_key in TIME_GATE_PILLAR:
        assert gate_key in time_gates, f"{gate_key} missing from detection_params.yaml"


def test_flag_gated_combat_ceiling_present():
    assert "COMBAT" in FLAG_GATED_PILLAR_CEILINGS
    result = lookup_ceiling("dungeon_crawl_seed42_1000t", "COMBAT")
    # A long-tick scenario clears the tick_budget check, so the flag_gated ceiling should surface.
    assert result is not None
    assert result.ceiling_kind in ("flag_gated", "tick_budget")


def test_ceiling_lookup_returns_none_for_unclassified_pair():
    # A 1000t scenario clears every WORLD time_gate (max threshold 500) and WORLD has no
    # flag_gated/corrected entry -- genuinely unclassified.
    result = lookup_ceiling("dungeon_crawl_seed42_1000t", "WORLD")
    assert result is None


def test_corrected_narrative_entry_present():
    result = lookup_ceiling("some_run_key_not_in_tick_budget_or_flag_table", "NARRATIVE")
    assert result is not None
    assert result.ceiling_kind == "corrected"
    assert result.since_ticket == "TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG"


def test_grade_regression_failure_message_includes_ceiling_when_known():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests" / "simulation_quality"))
    from test_grade_regression import _format_score_failures  # noqa: E402

    run_key = "dungeon_crawl_seed42_1000t"
    anchors = {"COMBAT": {"grade": "C", "score": 0.0}}
    actual_scores = {"COMBAT": 5.0}  # far outside tolerance, forces a failure line
    lines = _format_score_failures(run_key, anchors, actual_scores)
    assert len(lines) == 1
    assert "known flag_gated" in lines[0]
    assert "TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY" in lines[0]
