from __future__ import annotations
import pytest

from src.simulation_quality.pillar_accumulator import PillarAccumulator
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.quality_report import QualityReportBuilder, _assign_grade
from src.simulation_quality.score_record import ScoreRecord
from src.simulation_quality.weights import ScoringWeights


def _make_record(event_id: str, pillar: PillarId, delta: float) -> ScoreRecord:
    return ScoreRecord(
        tick=1,
        event_id=event_id,
        pillar=pillar,
        delta=delta,
        reason="test",
        event_type="test_event",
        entity_id=None,
        region_id=None,
        tags=(),
    )


def test_assign_grade_s(scoring_weights):
    assert _assign_grade(3.0, scoring_weights.grade_thresholds) == "S"


def test_assign_grade_a(scoring_weights):
    assert _assign_grade(1.0, scoring_weights.grade_thresholds) == "A"


def test_assign_grade_b(scoring_weights):
    assert _assign_grade(0.25, scoring_weights.grade_thresholds) == "B"


def test_assign_grade_c(scoring_weights):
    assert _assign_grade(-0.25, scoring_weights.grade_thresholds) == "C"


def test_assign_grade_d(scoring_weights):
    assert _assign_grade(-0.75, scoring_weights.grade_thresholds) == "D"


def test_assign_grade_f(scoring_weights):
    assert _assign_grade(-2.0, scoring_weights.grade_thresholds) == "F"


def test_assign_grade_boundary_exactly_s(scoring_weights):
    assert _assign_grade(2.0, scoring_weights.grade_thresholds) == "A"


def test_normalized_score_formula(scoring_weights):
    # All 10 events fire at tick=1; last_event_tick=1, floor=100//4=25, denom=max(25,1)=25
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    for i in range(10):
        acc.add(_make_record(f"e{i}", PillarId.ECONOMY, 10.0))
    accumulators = {PillarId.ECONOMY: acc}
    report = QualityReportBuilder.build(accumulators, current_tick=100, run_id="test", weights=scoring_weights)
    snap = report.pillars["ECONOMY"]
    # floor_tick = max(1, 100//4) = 25; last_event_tick=1 < 25; effective_denominator=25
    assert snap.normalized_score == pytest.approx(snap.raw_score / 25)


def test_normalized_score_tick_zero_uses_one(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    acc.add(_make_record("e1", PillarId.ECONOMY, 5.0))
    accumulators = {PillarId.ECONOMY: acc}
    report = QualityReportBuilder.build(accumulators, current_tick=0, run_id="test", weights=scoring_weights)
    snap = report.pillars["ECONOMY"]
    assert snap.normalized_score == pytest.approx(5.0 / 1)


def test_grade_reads_from_scoring_weights_not_hardcoded(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    for i in range(300):
        acc.add(_make_record(f"e{i}", PillarId.ECONOMY, 1.0))
    accumulators = {PillarId.ECONOMY: acc}
    report = QualityReportBuilder.build(accumulators, current_tick=100, run_id="test", weights=scoring_weights)
    snap = report.pillars["ECONOMY"]
    expected_grade = _assign_grade(snap.normalized_score, scoring_weights.grade_thresholds)
    assert snap.grade == expected_grade


def test_overall_score_weighted_average(scoring_weights):
    from collections import OrderedDict
    accumulators = {}
    for pillar in PillarId:
        acc = PillarAccumulator(pillar, weights=scoring_weights)
        accumulators[pillar] = acc
    report = QualityReportBuilder.build(
        accumulators, current_tick=10, run_id="test", weights=scoring_weights
    )
    weight_sum = sum(scoring_weights.pillar_weight(p.value) for p in PillarId)
    expected = sum(
        report.pillars[p.value].normalized_score * scoring_weights.pillar_weight(p.value)
        for p in PillarId
    ) / weight_sum
    assert report.overall_score == pytest.approx(expected)


def test_report_to_dict_is_json_serializable(scoring_weights):
    import json
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    acc.add(_make_record("e1", PillarId.ECONOMY, -5.0))
    report = QualityReportBuilder.build(
        {PillarId.ECONOMY: acc}, current_tick=10, run_id="r1", weights=scoring_weights
    )
    d = report.to_dict()
    serialized = json.dumps(d)
    assert "ECONOMY" in serialized


def test_report_has_correct_run_id(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    report = QualityReportBuilder.build({PillarId.ECONOMY: acc}, current_tick=5, run_id="my-run", weights=scoring_weights)
    assert report.run_id == "my-run"


# ---------------------------------------------------------------------------
# T-REP-01 through T-REP-07: last_event_tick normalization formula
# ---------------------------------------------------------------------------

def _make_record_at_tick(event_id: str, pillar: PillarId, tick: int, delta: float) -> ScoreRecord:
    return ScoreRecord(
        tick=tick,
        event_id=event_id,
        pillar=pillar,
        delta=delta,
        reason="test",
        event_type="test_event",
        entity_id=None,
        region_id=None,
        tags=(),
    )


def _make_acc_with_last_event_at(
    pillar: PillarId,
    scoring_weights,
    last_tick: int,
    raw_total: float,
) -> PillarAccumulator:
    """Build an accumulator with a single event delivering raw_total at last_tick."""
    acc = PillarAccumulator(pillar, weights=scoring_weights)
    acc.add(_make_record_at_tick("e1", pillar, tick=last_tick, delta=raw_total))
    return acc


def test_same_activity_same_normalized_score_at_different_tick_counts(scoring_weights):
    """T-REP-01: Same raw_score + same last_event_tick yields same normalized_score regardless
    of current_tick, as long as current_tick >= last_event_tick (floor does not activate)."""
    # last_event_tick=172 > floor at both 200 and 500 ticks
    # floor_200 = 200//4 = 50; floor_500 = 500//4 = 125; both < 172 so last_event_tick wins
    acc_200 = _make_acc_with_last_event_at(PillarId.COMBAT, scoring_weights, last_tick=172, raw_total=127.0)
    acc_500 = _make_acc_with_last_event_at(PillarId.COMBAT, scoring_weights, last_tick=172, raw_total=127.0)
    report_200 = QualityReportBuilder.build({PillarId.COMBAT: acc_200}, current_tick=200, run_id="r", weights=scoring_weights)
    report_500 = QualityReportBuilder.build({PillarId.COMBAT: acc_500}, current_tick=401, run_id="r", weights=scoring_weights)
    assert report_200.pillars["COMBAT"].normalized_score == pytest.approx(report_500.pillars["COMBAT"].normalized_score)


def test_combat_grade_stable_across_tick_counts_for_same_activity(scoring_weights):
    """T-REP-02: Core H2 regression — same 127.0 COMBAT raw at last_event_tick=172 earns A
    at both 200t and 401t (old formula gave B at 401t due to tick-dilution)."""
    acc_200 = _make_acc_with_last_event_at(PillarId.COMBAT, scoring_weights, last_tick=172, raw_total=127.0)
    acc_500 = _make_acc_with_last_event_at(PillarId.COMBAT, scoring_weights, last_tick=172, raw_total=127.0)
    report_200 = QualityReportBuilder.build({PillarId.COMBAT: acc_200}, current_tick=200, run_id="r", weights=scoring_weights)
    report_500 = QualityReportBuilder.build({PillarId.COMBAT: acc_500}, current_tick=401, run_id="r", weights=scoring_weights)
    assert report_200.pillars["COMBAT"].grade == "A"
    assert report_500.pillars["COMBAT"].grade == "A"


def test_zero_event_pillar_uses_current_tick_fallback(scoring_weights):
    """T-REP-03: Pillar with no events (last_event_tick=0) falls back to current_tick.
    raw_score=0.0 always yields 0.0 so grade stays C regardless."""
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)  # no events added
    report = QualityReportBuilder.build({PillarId.ECONOMY: acc}, current_tick=500, run_id="r", weights=scoring_weights)
    snap = report.pillars["ECONOMY"]
    assert snap.normalized_score == pytest.approx(0.0)
    assert snap.grade == "C"


def test_exact_normalized_score_when_last_event_tick_exceeds_floor(scoring_weights):
    """T-REP-04: When last_event_tick > floor_tick, normalized = raw / last_event_tick exactly.
    127.0 / 172 = 0.7384; floor = 500//4 = 125; 172 > 125 so last_event_tick wins."""
    acc = _make_acc_with_last_event_at(PillarId.COMBAT, scoring_weights, last_tick=172, raw_total=127.0)
    report = QualityReportBuilder.build({PillarId.COMBAT: acc}, current_tick=500, run_id="r", weights=scoring_weights)
    expected = 127.0 / 172
    assert abs(report.pillars["COMBAT"].normalized_score - expected) < 0.001
    assert report.pillars["COMBAT"].grade == "A"


def test_active_throughout_run_behavior_unchanged(scoring_weights):
    """T-REP-05: Pillar active throughout the run (last_event_tick ≈ current_tick) behaves
    the same as before — last_event_tick > floor so it is used as denominator."""
    # 400 events up to tick 400; last_event_tick=400, floor=401//4=100; 400 > 100 so 400 used
    acc = PillarAccumulator(PillarId.WORLD, weights=scoring_weights)
    for i in range(154):
        acc.add(_make_record_at_tick(f"e{i}", PillarId.WORLD, tick=min(i * 3 + 1, 400), delta=1.0))
    report = QualityReportBuilder.build({PillarId.WORLD: acc}, current_tick=401, run_id="r", weights=scoring_weights)
    snap = report.pillars["WORLD"]
    # last_event_tick will be ≤ 400; floor=100; denominator = last_event_tick
    let = acc.last_event_tick
    expected_norm = 154.0 / let
    assert abs(snap.normalized_score - expected_norm) < 0.001


def test_floor_damps_early_burst_inflation(scoring_weights):
    """T-REP-06: When all events fire at tick 1 (AGENCY-style initialization burst),
    the floor_tick (current_tick // 4) is used as denominator, not last_event_tick=1.
    Prevents S-grade inflation for initialization-burst pillars.
    raw=40.0, last_event_tick=1, current_tick=401 -> floor=100 -> norm=40/100=0.40 -> B"""
    acc = _make_acc_with_last_event_at(PillarId.AGENCY, scoring_weights, last_tick=1, raw_total=40.0)
    report = QualityReportBuilder.build(
        {PillarId.AGENCY: acc}, current_tick=401, run_id="r", weights=scoring_weights
    )
    expected_denom = 401 // 4  # = 100
    expected_norm = 40.0 / expected_denom
    assert abs(report.pillars["AGENCY"].normalized_score - expected_norm) < 0.001
    assert report.pillars["AGENCY"].grade == "B"


def test_floor_not_used_when_last_event_tick_exceeds_floor(scoring_weights):
    """T-REP-07: Normal case: last_event_tick=172, current_tick=401, floor=100.
    172 > 100, so last_event_tick=172 is used (not floor).
    127.0 / 172 = 0.7384 -> A."""
    acc = _make_acc_with_last_event_at(PillarId.COMBAT, scoring_weights, last_tick=172, raw_total=127.0)
    report = QualityReportBuilder.build(
        {PillarId.COMBAT: acc}, current_tick=401, run_id="r", weights=scoring_weights
    )
    expected = 127.0 / 172  # = 0.7384
    assert abs(report.pillars["COMBAT"].normalized_score - expected) < 0.001
    assert report.pillars["COMBAT"].grade == "A"
