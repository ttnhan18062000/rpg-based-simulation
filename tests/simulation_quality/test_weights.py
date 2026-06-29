from __future__ import annotations
import os
import pytest
from pydantic import ValidationError

from src.simulation_quality.pillars import PillarId
from src.simulation_quality.weights import ScoringWeights

_WEIGHTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../config/simulation_quality/scoring_weights.yaml",
)
_GRADE_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../config/simulation_quality/grade_thresholds.yaml",
)
_DETECTION_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../config/simulation_quality/detection_params.yaml",
)


def test_load_from_real_config(scoring_weights):
    assert scoring_weights is not None


def test_all_10_pillars_present(scoring_weights):
    for pillar in PillarId:
        assert pillar.value in scoring_weights.pillar_rules, (
            f"Pillar '{pillar.value}' missing from scoring_weights.yaml"
        )


def test_grade_thresholds_load(scoring_weights):
    assert "S" in scoring_weights.grade_thresholds
    assert "A" in scoring_weights.grade_thresholds
    assert "B" in scoring_weights.grade_thresholds
    assert "C" in scoring_weights.grade_thresholds
    assert "D" in scoring_weights.grade_thresholds


def test_grade_thresholds_values(scoring_weights):
    assert scoring_weights.grade_thresholds["S"] == pytest.approx(2.0)
    assert scoring_weights.grade_thresholds["A"] == pytest.approx(0.5)
    assert scoring_weights.grade_thresholds["B"] == pytest.approx(0.0)
    assert scoring_weights.grade_thresholds["C"] == pytest.approx(-0.5)
    assert scoring_weights.grade_thresholds["D"] == pytest.approx(-1.0)


def test_getitem_known_key(scoring_weights):
    value = scoring_weights["harvest_active"]
    assert isinstance(value, float)
    assert value == pytest.approx(3.0)


def test_getitem_raises_on_missing_key(scoring_weights):
    with pytest.raises(KeyError, match="nonexistent_key_xyz"):
        _ = scoring_weights["nonexistent_key_xyz"]


def test_int_param_known_key(scoring_weights):
    value = scoring_weights.int_param("stasis_gate_ticks")
    assert isinstance(value, int)
    assert value == 5


def test_int_param_raises_on_missing_key(scoring_weights):
    with pytest.raises(KeyError, match="nonexistent_gate"):
        scoring_weights.int_param("nonexistent_gate")


def test_pillar_weight_default_profile_is_one(scoring_weights):
    for pillar in PillarId:
        assert scoring_weights.pillar_weight(pillar.value) == pytest.approx(1.0)


def test_detection_params_load(scoring_weights):
    assert scoring_weights.detection.loop_threshold == pytest.approx(0.70)
    assert scoring_weights.detection.window_size == 200
    assert scoring_weights.detection.max_worst_events == 100


def test_dungeon_crawl_profile_overrides():
    weights = ScoringWeights.load(
        weights_path=_WEIGHTS_PATH,
        grade_path=_GRADE_PATH,
        detection_path=_DETECTION_PATH,
        profile="dungeon_crawl",
    )
    assert weights.pillar_weight("COMBAT") == pytest.approx(2.0)
    assert weights.pillar_weight("FACTION") == pytest.approx(0.1)
    assert weights.pillar_weight("AGENCY") == pytest.approx(1.0)


def test_urban_political_profile_overrides():
    weights = ScoringWeights.load(
        weights_path=_WEIGHTS_PATH,
        grade_path=_GRADE_PATH,
        detection_path=_DETECTION_PATH,
        profile="urban_political",
    )
    assert weights.pillar_weight("FACTION") == pytest.approx(1.5)
    assert weights.pillar_weight("ECONOMY") == pytest.approx(1.5)
    assert weights.pillar_weight("COMBAT") == pytest.approx(0.3)
    assert weights.pillar_weight("AGENCY") == pytest.approx(1.0)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ScoringWeights.load(
            weights_path=str(tmp_path / "nonexistent.yaml"),
            grade_path=_GRADE_PATH,
            detection_path=_DETECTION_PATH,
        )
