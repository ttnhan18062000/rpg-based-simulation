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
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    for i in range(10):
        acc.add(_make_record(f"e{i}", PillarId.ECONOMY, 10.0))
    accumulators = {PillarId.ECONOMY: acc}
    report = QualityReportBuilder.build(accumulators, current_tick=100, run_id="test", weights=scoring_weights)
    snap = report.pillars["ECONOMY"]
    assert snap.normalized_score == pytest.approx(snap.raw_score / 100)


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
