"""Tests for tools/agent-monitoring/weight_sensitivity_check.py (TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE,
promoted from experiments/cost_proxy_calibration/validate_rank_order.py).

Pure unit tests against compute_weight_sensitivity_report() with fixture dicts — no file I/O, no
subprocess, mirroring test_cost_proxy.py's fixture-dict style.
"""
import json
import re
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from weight_sensitivity_check import (  # noqa: E402
    SHIPPED_WEIGHTS,
    _score_with_weights,
    _spearman_rank_correlation,
    compute_weight_sensitivity_report,
)
import weight_sensitivity_check as _wsc  # noqa: E402


def _write_jsonl(path: Path, records: list) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

_W_BASELINE = {"bash": 0.001, "agent": 50, "edit": 1}
_W_CANDIDATE = {"bash": 0.01, "agent": 100, "edit": 10}


def test_score_with_weights_matches_hand_computed_formula():
    tool_rows = [
        {"tool": "Bash", "duration_ms": 1000},
        {"tool": "Bash", "duration_ms": 2000},
        {"tool": "Agent"},
        {"tool": "Read"},
        {"tool": "Edit"},
    ]
    # bash: 0.001 * 3000 = 3.0, agent: 50 * 1 = 50, edit: 1 * 2 = 2 -> total 55.0
    assert _score_with_weights(tool_rows, _W_BASELINE) == 55.0


def test_score_with_weights_empty_group_is_zero():
    assert _score_with_weights([], _W_BASELINE) == 0.0


def test_shipped_weights_reads_real_cost_proxy_constants_not_a_second_copy():
    # SHIPPED_WEIGHTS must reflect cost_proxy.py's actual live constants, not a hardcoded literal
    # that could silently drift out of sync if cost_proxy.py's weights ever change.
    from cost_proxy import W_AGENT, W_BASH, W_EDIT

    assert SHIPPED_WEIGHTS == {"bash": W_BASH, "agent": W_AGENT, "edit": W_EDIT}


def test_spearman_identical_rankings_is_one():
    rank = {"a": 0, "b": 1, "c": 2}
    assert _spearman_rank_correlation(rank, rank) == 1.0


def test_spearman_fully_reversed_rankings_is_negative_one():
    rank_a = {"a": 0, "b": 1, "c": 2}
    rank_b = {"a": 2, "b": 1, "c": 0}
    assert _spearman_rank_correlation(rank_a, rank_b) == -1.0


def test_spearman_undefined_for_fewer_than_two_keys():
    assert _spearman_rank_correlation({"a": 0}, {"a": 0}) is None


def test_compute_weight_sensitivity_report_basic_grouping_and_ranking():
    tool_rows_by_group = {
        ("TCK-A", 1): [{"tool": "Bash", "duration_ms": 1000}],
        ("TCK-A", 2): [{"tool": "Agent"}, {"tool": "Agent"}],
    }
    phase_of = {("TCK-A", 1): "Test", ("TCK-A", 2): "Implement"}
    agent_of = {("TCK-A", 1): "test-scoper", ("TCK-A", 2): "implementer"}

    report = compute_weight_sensitivity_report(
        tool_rows_by_group, phase_of, agent_of, _W_BASELINE, _W_CANDIDATE
    )

    assert report["n_groups_scored"] == 2
    phase_rows = {r["bucket"]: r for r in report["by_phase"]["rows"]}
    # Implement: 2 Agent calls -> baseline 50*2=100, candidate 100*2=200
    assert phase_rows["Implement"]["baseline_mean"] == 100.0
    assert phase_rows["Implement"]["candidate_mean"] == 200.0
    # Test: 1000ms Bash -> baseline 0.001*1000=1.0, candidate 0.01*1000=10.0
    assert phase_rows["Test"]["baseline_mean"] == 1.0
    assert phase_rows["Test"]["candidate_mean"] == 10.0
    # Both weight sets agree Implement > Test in relative terms here, so rank order unchanged.
    assert phase_rows["Implement"]["baseline_rank"] == 0
    assert phase_rows["Implement"]["candidate_rank"] == 0


def test_compute_weight_sensitivity_report_group_with_no_matching_event_is_skipped():
    # (run_id, seq) with tool rows but no corresponding event — must be silently excluded, not
    # crash on a missing phase_of/agent_of lookup.
    tool_rows_by_group = {
        ("TCK-A", 1): [{"tool": "Bash", "duration_ms": 1000}],
        ("TCK-A", 99): [{"tool": "Agent"}],  # no matching event
    }
    phase_of = {("TCK-A", 1): "Test"}
    agent_of = {("TCK-A", 1): "test-scoper"}

    report = compute_weight_sensitivity_report(
        tool_rows_by_group, phase_of, agent_of, _W_BASELINE, _W_CANDIDATE
    )

    assert report["n_groups_scored"] == 1
    assert {r["bucket"] for r in report["by_phase"]["rows"]} == {"Test"}


def test_compute_weight_sensitivity_report_empty_input_does_not_crash():
    report = compute_weight_sensitivity_report({}, {}, {}, _W_BASELINE, _W_CANDIDATE)

    assert report["n_groups_scored"] == 0
    assert report["by_phase"]["rows"] == []
    assert report["by_phase"]["spearman"] is None


def test_rank_delta_reflects_material_reordering_between_weight_sets():
    # A group that's cheap under baseline weights but expensive under candidate weights (heavy
    # Agent-spawn count, which candidate weights 2x more than baseline) must show a nonzero
    # rank_delta — the whole point of this tool is detecting exactly this kind of reordering.
    tool_rows_by_group = {
        ("TCK-A", 1): [{"tool": "Bash", "duration_ms": 100000}],  # baseline-dominant
        ("TCK-A", 2): [{"tool": "Agent"}],  # candidate-relatively-dominant
    }
    phase_of = {("TCK-A", 1): "Test", ("TCK-A", 2): "Implement"}
    agent_of = {("TCK-A", 1): "test-scoper", ("TCK-A", 2): "implementer"}
    w_baseline = {"bash": 0.001, "agent": 1, "edit": 1}
    w_candidate = {"bash": 0.0001, "agent": 1000, "edit": 1}

    report = compute_weight_sensitivity_report(
        tool_rows_by_group, phase_of, agent_of, w_baseline, w_candidate
    )

    rows = {r["bucket"]: r for r in report["by_phase"]["rows"]}
    # Under baseline: Test (0.001*100000=100) > Implement (1*1=1) -> Test rank 0.
    assert rows["Test"]["baseline_rank"] == 0
    # Under candidate: Implement (1000*1=1000) > Test (0.0001*100000=10) -> Implement rank 0.
    assert rows["Implement"]["candidate_rank"] == 0
    assert rows["Test"]["rank_delta"] != 0
    assert rows["Implement"]["rank_delta"] != 0


def test_weight_sensitivity_check_real_multi_week_tools_and_events_produce_nonzero_score(tmp_path, monkeypatch, capsys):
    # Cross-week regression test for the TOOLS_FILE/EVENTS_FILE ground-truth bug this ticket
    # names explicitly: week1 seeds one (run_id, seq) group, week2 seeds a distinct one — a
    # same-week-only fixture could pass a weaker version of this test while leaving the
    # cross-week case silently broken.
    week1 = tmp_path / "agent-monitoring" / "data" / "2026-W01"
    week1.mkdir(parents=True)
    _write_jsonl(week1 / "tools.jsonl", [
        {"run_id": "TCK-A", "seq": 1, "tool": "Bash", "duration_ms": 1000},
    ])
    _write_jsonl(week1 / "events.jsonl", [
        {"run_id": "TCK-A", "seq": 1, "phase": "Test", "agent": "test-scoper"},
    ])

    week2 = tmp_path / "agent-monitoring" / "data" / "2026-W02"
    week2.mkdir(parents=True)
    _write_jsonl(week2 / "tools.jsonl", [
        {"run_id": "TCK-B", "seq": 1, "tool": "Agent"},
    ])
    _write_jsonl(week2 / "events.jsonl", [
        {"run_id": "TCK-B", "seq": 1, "phase": "Implement", "agent": "implementer"},
    ])

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "weight_sensitivity_check.py",
        "--candidate-weights", '{"bash": 0.01, "agent": 100, "edit": 10}',
        "--baseline-weights", '{"bash": 0.001, "agent": 50, "edit": 1}',
    ])

    # Real CLI path — must exercise _load_tool_rows_and_events()'s real file-reading logic,
    # not compute_weight_sensitivity_report() called directly with hand-built dicts.
    _wsc.main()
    captured = capsys.readouterr()
    match = re.search(r"Groups scored \(real \(run_id,seq\) with a matching event\): (\d+)", captured.out)
    assert match is not None, captured.out
    assert int(match.group(1)) > 0, "n_groups_scored must be nonzero across a real multi-week corpus"

    tool_rows_by_group, phase_of, agent_of = _wsc._load_tool_rows_and_events(_wsc.TOOLS_FILE, _wsc.EVENTS_FILE)
    report = compute_weight_sensitivity_report(
        tool_rows_by_group, phase_of, agent_of,
        {"bash": 0.001, "agent": 50, "edit": 1}, {"bash": 0.01, "agent": 100, "edit": 10},
    )
    assert report["n_groups_scored"] == 2
    rows = {r["bucket"]: r for r in report["by_phase"]["rows"]}
    assert rows["Test"]["baseline_mean"] != 0
    assert rows["Implement"]["candidate_mean"] != 0
