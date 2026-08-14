from __future__ import annotations
import os
import pytest
import yaml

from src.simulation_quality.pillars import PillarId
from src.simulation_quality.weights import DetectionParams, PillarWeightsView, ScoringWeights

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
    # TCK-20260713-SIMQ-SCORE-CEILING-FIX raised ECONOMY's positive weights x4 (3.0 -> 12.0)
    assert value == pytest.approx(12.0)


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


def _make_synthetic_weights(pillar_rules: dict[str, dict[str, float]]) -> ScoringWeights:
    return ScoringWeights(
        pillar_rules=pillar_rules,
        grade_thresholds={"S": 2.0, "A": 0.5, "B": 0.0, "C": -0.5, "D": -1.0},
        detection=DetectionParams(
            loop_threshold=0.70,
            window_size=200,
            max_worst_events=100,
            time_gates={},
        ),
    )


@pytest.mark.parametrize(
    "pillar_rules",
    [
        {
            "PILLAR_A": {"shared_key": 1.0, "a_only": 9.0},
            "PILLAR_B": {"shared_key": 2.0, "b_only": 8.0},
        },
        {
            "PILLAR_B": {"shared_key": 2.0, "b_only": 8.0},
            "PILLAR_A": {"shared_key": 1.0, "a_only": 9.0},
        },
    ],
)
def test_pillar_scoped_lookup_resolves_independently_of_declaration_order(pillar_rules):
    weights = _make_synthetic_weights(pillar_rules)
    assert weights.for_pillar("PILLAR_A")["shared_key"] == pytest.approx(1.0)
    assert weights.for_pillar("PILLAR_B")["shared_key"] == pytest.approx(2.0)
    assert isinstance(weights.for_pillar("PILLAR_A"), PillarWeightsView)
    with pytest.raises(KeyError):
        _ = weights["shared_key"]


_SEVEN_KNOWN_COLLISIONS = [
    ("belief_active", "COGNITION", 2.0, "INFORMATION", 10.0),
    ("subjective_divergence", "COGNITION", 5.0, "INFORMATION", 30.0),
    ("knowledge_rot", "COGNITION", -3.0, "INFORMATION", -2.0),
    ("omniscience_collapse", "COGNITION", -20.0, "INFORMATION", -20.0),
    ("ecology_cycling", "ECONOMY", 8.0, "WORLD", 6.0),
    ("ecology_broken", "ECONOMY", -25.0, "WORLD", -20.0),
    ("knowledge_economy_active", "ECONOMY", 8.0, "INFORMATION", 15.0),
]


@pytest.mark.parametrize(
    "key,pillar_a,value_a,pillar_b,value_b", _SEVEN_KNOWN_COLLISIONS
)
def test_real_config_seven_known_collisions_resolve_per_pillar(
    scoring_weights, key, pillar_a, value_a, pillar_b, value_b
):
    assert scoring_weights.for_pillar(pillar_a)[key] == pytest.approx(value_a)
    assert scoring_weights.for_pillar(pillar_b)[key] == pytest.approx(value_b)
    with pytest.raises(KeyError):
        _ = scoring_weights[key]


def test_missing_key_raises_validation_error(tmp_path):
    with open(_DETECTION_PATH, "r", encoding="utf-8") as fh:
        detection_raw = yaml.safe_load(fh)
    del detection_raw["loop_threshold"]
    detection_path = tmp_path / "detection_params.yaml"
    with open(detection_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(detection_raw, fh)

    # ScoringWeights.load()'s `raw_detection["loop_threshold"]` access raises a bare
    # KeyError for a missing top-level key today, not pydantic.ValidationError as
    # INFRA-234/this ticket's AC #3 originally assumed (architecture-review correction,
    # see plan.md's Plan Amendment) — asserting the real exception type here rather
    # than the wrong one.
    with pytest.raises(KeyError, match="loop_threshold"):
        ScoringWeights.load(
            weights_path=_WEIGHTS_PATH,
            grade_path=_GRADE_PATH,
            detection_path=str(detection_path),
        )


def test_malformed_value_raises_validation_error(tmp_path):
    with open(_WEIGHTS_PATH, "r", encoding="utf-8") as fh:
        weights_raw = yaml.safe_load(fh)
    weights_raw["ECONOMY"]["harvest_active"] = "not_a_number"
    weights_path = tmp_path / "scoring_weights.yaml"
    with open(weights_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(weights_raw, fh)

    # `load()`'s `float(v)` conversion raises a bare ValueError for a non-numeric rule
    # value today, not pydantic.ValidationError as INFRA-234/this ticket's AC #3
    # originally assumed — asserting the real exception type here rather than the
    # wrong one (see plan.md's Step 3 for the verified-first-before-asserting rule).
    with pytest.raises(ValueError, match="not_a_number"):
        ScoringWeights.load(
            weights_path=str(weights_path),
            grade_path=_GRADE_PATH,
            detection_path=_DETECTION_PATH,
        )
