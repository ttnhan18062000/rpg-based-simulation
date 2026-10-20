from __future__ import annotations
import pytest

from src.simulation_quality.pillar_accumulator import PillarAccumulator
from src.simulation_quality.pillars import PILLAR_MIN_EVENTS, PillarId
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
    for i in range(3):
        acc.add(_make_record(f"e{i}", PillarId.ECONOMY, 5.0 / 3))
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
    for n, pillar in enumerate(PillarId):
        acc = PillarAccumulator(pillar, weights=scoring_weights)
        for i in range(PILLAR_MIN_EVENTS[pillar]):
            acc.add(_make_record(f"{pillar.value}{i}", pillar, float(n - 4)))
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
    """Build an accumulator with exactly the minimum event count, summing to raw_total, the last at last_tick."""
    acc = PillarAccumulator(pillar, weights=scoring_weights)
    n = PILLAR_MIN_EVENTS[pillar]
    for i in range(n):
        acc.add(_make_record_at_tick(f"e{i}", pillar, tick=last_tick, delta=raw_total / n))
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


def test_zero_event_pillar_is_no_data_not_a_grade(scoring_weights):
    """T-REP-03: a pillar with no events reports no-data: null score and grade, a reason, never a placeholder."""
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)  # no events added
    report = QualityReportBuilder.build({PillarId.ECONOMY: acc}, current_tick=500, run_id="r", weights=scoring_weights)
    snap = report.pillars["ECONOMY"]
    assert snap.status == "no-data"
    assert snap.normalized_score is None
    assert snap.grade is None
    assert snap.reason == "below_min_events"


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


# ---------------------------------------------------------------------------
# No-data below a minimum event count (PILLAR_MIN_EVENTS)
# ---------------------------------------------------------------------------

def _acc_with_events(pillar: PillarId, scoring_weights, count: int, delta: float) -> PillarAccumulator:
    acc = PillarAccumulator(pillar, weights=scoring_weights)
    for i in range(count):
        acc.add(_make_record_at_tick(f"{pillar.value}{i}", pillar, tick=10, delta=delta))
    return acc


def test_a_lone_plateau_penalty_is_no_data_and_not_a_grade(scoring_weights):
    acc = _acc_with_events(PillarId.PROGRESSION, scoring_weights, 1, -8.0)
    report = QualityReportBuilder.build({PillarId.PROGRESSION: acc}, current_tick=200, run_id="r", weights=scoring_weights)
    snap = report.pillars["PROGRESSION"]
    assert (snap.status, snap.grade, snap.normalized_score, snap.reason) == ("no-data", None, None, "below_min_events")
    assert snap.event_count == 1 and snap.min_events == PILLAR_MIN_EVENTS[PillarId.PROGRESSION]


def test_at_the_minimum_the_pillar_is_scored_as_before(scoring_weights):
    n = PILLAR_MIN_EVENTS[PillarId.PROGRESSION]
    below = QualityReportBuilder.build({PillarId.PROGRESSION: _acc_with_events(PillarId.PROGRESSION, scoring_weights, n - 1, 1.0)}, 200, "r", scoring_weights)
    at = QualityReportBuilder.build({PillarId.PROGRESSION: _acc_with_events(PillarId.PROGRESSION, scoring_weights, n, 1.0)}, 200, "r", scoring_weights)
    assert below.pillars["PROGRESSION"].status == "no-data"
    assert at.pillars["PROGRESSION"].status == "ok"
    assert at.pillars["PROGRESSION"].grade is not None and "reason" not in at.to_dict()["pillars"]["PROGRESSION"]


def test_overall_excludes_no_data_pillars_and_counts_both(scoring_weights):
    accs = {p: _acc_with_events(p, scoring_weights, PILLAR_MIN_EVENTS[p], 5.0) for p in list(PillarId)[:6]}
    accs.update({p: _acc_with_events(p, scoring_weights, 1, -50.0) for p in list(PillarId)[6:]})
    report = QualityReportBuilder.build(accs, current_tick=100, run_id="r", weights=scoring_weights)
    scored = [p for p in list(PillarId)[:6]]
    weight_sum = sum(scoring_weights.pillar_weight(p.value) for p in scored)
    expected = sum(report.pillars[p.value].normalized_score * scoring_weights.pillar_weight(p.value) for p in scored) / weight_sum
    assert report.overall_status == "ok" and report.overall_reason is None
    assert report.overall_score == pytest.approx(expected)
    assert (report.pillars_scored, report.pillars_no_data) == (6, 4)


def test_overall_is_no_data_below_half_the_pillars_scored(scoring_weights):
    accs = {p: _acc_with_events(p, scoring_weights, PILLAR_MIN_EVENTS[p], 5.0) for p in list(PillarId)[:4]}
    accs.update({p: PillarAccumulator(p, weights=scoring_weights) for p in list(PillarId)[4:]})
    report = QualityReportBuilder.build(accs, current_tick=100, run_id="r", weights=scoring_weights)
    assert (report.overall_status, report.overall_score, report.overall_grade, report.overall_reason) == (
        "no-data", None, None, "too_few_pillars_scored")
    assert (report.pillars_scored, report.pillars_no_data) == (4, 6)


def test_every_pillar_key_is_present_and_the_bytes_are_stable(scoring_weights):
    import json
    accs = {p: PillarAccumulator(p, weights=scoring_weights) for p in PillarId}
    d1 = QualityReportBuilder.build(accs, 100, "r", scoring_weights).to_dict()
    d2 = QualityReportBuilder.build(accs, 100, "r", scoring_weights).to_dict()
    for d in (d1, d2):
        d.pop("generated_at")
    assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)
    assert set(d1["pillars"]) == {p.value for p in PillarId}
    for pillar in d1["pillars"].values():
        assert {"status", "grade", "normalized_score", "event_count", "min_events"} <= set(pillar)
    assert d1["overall_score"] is None and d1["overall_grade"] is None
    assert {"overall_status", "overall_reason", "pillars_scored", "pillars_no_data"} <= set(d1)


def test_calibrate_prints_a_no_data_pillar_instead_of_crashing(scoring_weights):
    from tools.calibrate_simq import pillar_line
    acc = _acc_with_events(PillarId.PROGRESSION, scoring_weights, 1, -8.0)
    snap = QualityReportBuilder.build({PillarId.PROGRESSION: acc}, 200, "r", scoring_weights).pillars["PROGRESSION"]
    assert "no-data (1 events < 3)" in pillar_line("PROGRESSION", snap)
