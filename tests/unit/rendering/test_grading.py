"""Tests for src.rendering.grading's config loader, hard/soft rule evaluation,
combination, grade assignment, and multi-seed averaging.

TCK-20260821-VISUAL-GRADE-SCORER. Tests 2-4 write real temp .toml files (TOML syntax,
tomllib.load()'s binary-mode contract), never YAML, matching src/rendering/grading.py's
own stdlib-only config format (plan.md Decision 2). Test 14 is a real-corpus smoke test
against dungeon_crawl -- per plan.md's Anti-Drift Test Guards, it deliberately does NOT
pin a specific grade letter or combined-score value as a regression anchor, since this
ticket's illustrative thresholds are explicitly uncalibrated
(TCK-20260821-VISUAL-QUALITY-CALIBRATION's job).
"""
from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest

from src.rendering.connectivity import analyze_connectivity
from src.rendering.grading import (
    GradeConfig,
    HardRuleConfig,
    HardRuleResult,
    SoftRuleConfig,
    SoftRuleResult,
    assign_grade,
    average_scores,
    combine_rule_deltas,
    evaluate_hard_rule,
    evaluate_soft_rule,
    load_grade_config,
)
from src.rendering.shape import connected_components
from src.simulation_quality.pillars import PillarId
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

_GRADING_MODULE_PATH = Path(__file__).resolve().parents[3] / "src" / "rendering" / "grading.py"

_REAL_CONFIG_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "rendering" / "grade_thresholds.toml"
)


def _make_config(
    grade_thresholds: dict[str, float] | None = None,
    hard_rules: dict[str, HardRuleConfig] | None = None,
    soft_rules: dict[str, SoftRuleConfig] | None = None,
) -> GradeConfig:
    return GradeConfig(
        grade_thresholds=grade_thresholds
        if grade_thresholds is not None
        else {"S": 2.0, "A": 0.5, "B": 0.0, "C": -0.5, "D": -1.0},
        hard_rules=hard_rules
        if hard_rules is not None
        else {"fully_connected": HardRuleConfig(pass_delta=1.0, fail_delta=-1.0)},
        soft_rules=soft_rules
        if soft_rules is not None
        else {
            "fill_ratio_healthy_band": SoftRuleConfig(
                low=0.0, healthy_low=0.3, healthy_high=0.85, high=1.0,
                peak_delta=1.0, min_delta=-1.0,
            )
        },
    )


_BOUNDARY_CASES = [
    (2.0, "A"),
    (2.0001, "S"),
    (3.0, "S"),
    (0.5, "B"),
    (0.5001, "A"),
    (1.0, "A"),
    (0.0, "C"),
    (0.0001, "B"),
    (0.25, "B"),
    (-0.5, "D"),
    (-0.5001, "D"),
    (-0.25, "C"),
    (-0.75, "D"),
    (-1.0, "F"),
    (-1.0001, "F"),
    (-2.0, "F"),
]


@pytest.mark.parametrize("combined_score,expected_grade", _BOUNDARY_CASES)
def test_grade_assignment_boundaries(combined_score, expected_grade):
    config = _make_config()

    assert assign_grade(combined_score, config.grade_thresholds) == expected_grade


def test_config_sources_grade_thresholds_not_hardcoded(tmp_path):
    config_a_path = tmp_path / "config_a.toml"
    config_a_path.write_text(
        """
[grade_thresholds]
S = 2.0
A = 0.5
B = 0.0
C = -0.5
D = -1.0

[hard_rules.fully_connected]
pass_delta = 1.0
fail_delta = -1.0

[soft_rules.fill_ratio_healthy_band]
low = 0.0
healthy_low = 0.3
healthy_high = 0.85
high = 1.0
peak_delta = 1.0
min_delta = -1.0
""".strip()
    )

    config_b_path = tmp_path / "config_b.toml"
    config_b_path.write_text(
        """
[grade_thresholds]
S = 100.0
A = 50.0
B = 10.0
C = 0.0
D = -10.0

[hard_rules.fully_connected]
pass_delta = 1.0
fail_delta = -1.0

[soft_rules.fill_ratio_healthy_band]
low = 0.0
healthy_low = 0.3
healthy_high = 0.85
high = 1.0
peak_delta = 1.0
min_delta = -1.0
""".strip()
    )

    config_a = load_grade_config(config_a_path)
    config_b = load_grade_config(config_b_path)

    grade_a = assign_grade(0.25, config_a.grade_thresholds)
    grade_b = assign_grade(0.25, config_b.grade_thresholds)

    assert grade_a == "B"
    assert grade_b == "C"
    assert grade_a != grade_b


def test_config_load_fails_loud_on_missing_key(tmp_path):
    config_path = tmp_path / "missing_key.toml"
    config_path.write_text(
        """
[grade_thresholds]
S = 2.0
A = 0.5
B = 0.0
C = -0.5

[hard_rules.fully_connected]
pass_delta = 1.0
fail_delta = -1.0

[soft_rules.fill_ratio_healthy_band]
low = 0.0
healthy_low = 0.3
healthy_high = 0.85
high = 1.0
peak_delta = 1.0
min_delta = -1.0
""".strip()
    )

    with pytest.raises(KeyError):
        load_grade_config(config_path)


def test_config_load_fails_loud_on_non_numeric_value(tmp_path):
    config_path = tmp_path / "non_numeric.toml"
    config_path.write_text(
        """
[grade_thresholds]
S = 2.0
A = 0.5
B = 0.0
C = -0.5
D = "not-a-number"

[hard_rules.fully_connected]
pass_delta = 1.0
fail_delta = -1.0

[soft_rules.fill_ratio_healthy_band]
low = 0.0
healthy_low = 0.3
healthy_high = 0.85
high = 1.0
peak_delta = 1.0
min_delta = -1.0
""".strip()
    )

    with pytest.raises(ValueError):
        load_grade_config(config_path)


def test_hard_rule_binary_shape():
    config = _make_config()

    passed_result = evaluate_hard_rule("fully_connected", True, config)
    failed_result = evaluate_hard_rule("fully_connected", False, config)

    assert passed_result.delta == config.hard_rules["fully_connected"].pass_delta
    assert failed_result.delta == config.hard_rules["fully_connected"].fail_delta
    assert passed_result.delta != failed_result.delta


def test_soft_rule_non_monotonicity_three_point():
    config = _make_config()

    inside_band = evaluate_soft_rule("fill_ratio_healthy_band", 0.5, config)
    below_healthy_low = evaluate_soft_rule("fill_ratio_healthy_band", 0.05, config)
    above_healthy_high = evaluate_soft_rule("fill_ratio_healthy_band", 0.98, config)

    assert inside_band.delta > 0
    assert below_healthy_low.delta < 0
    assert above_healthy_high.delta < 0


def test_combination_step_produces_single_normalized_score():
    hard_results = [HardRuleResult(name="fully_connected", passed=True, delta=1.0)]
    soft_results = [SoftRuleResult(name="fill_ratio_healthy_band", raw_value=0.5, delta=0.5)]

    combined = combine_rule_deltas(hard_results, soft_results)
    assert isinstance(combined, float)
    assert combined == 1.5

    larger_soft_results = [
        SoftRuleResult(name="fill_ratio_healthy_band", raw_value=0.5, delta=2.0)
    ]
    larger_combined = combine_rule_deltas(hard_results, larger_soft_results)

    assert larger_combined > combined


def test_multi_seed_averaging_n1_identity():
    assert average_scores([2.5]) == 2.5


def test_multi_seed_averaging_n_gt_1_synthetic_mean():
    assert average_scores([1.0, 2.0, 3.0]) == 2.0


def test_grading_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline():
    tree = ast.parse(_GRADING_MODULE_PATH.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names = [
                base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                for base in node.bases
            ]
            assert "PillarScorer" not in base_names, "grading.py must not subclass PillarScorer"
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "simulation_quality" not in name, f"grading.py must not import {name}"
            assert "observability.events" not in name, f"grading.py must not import {name}"


def test_grading_module_does_not_register_new_pillar_id():
    expected_members = {
        "COGNITION", "AGENCY", "COMBAT", "FACTION", "ECONOMY",
        "PROGRESSION", "SOCIAL", "INFORMATION", "WORLD", "NARRATIVE",
    }

    assert {member.value for member in PillarId} == expected_members


def test_grading_module_has_zero_image_or_render_dependency():
    tree = ast.parse(_GRADING_MODULE_PATH.read_text())
    forbidden_substrings = ("png_writer", "rendering.render", "rendering.incremental", "PIL", "Pillow")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert not any(forbidden in name for forbidden in forbidden_substrings), (
                f"grading.py must not import {name} (image/render dependency)"
            )


def test_grading_does_not_mutate_inputs():
    config = _make_config()
    terrain = {
        (0, 0): "CAVE", (1, 0): "CAVE", (2, 0): "CAVE",
        (0, 1): "CAVE", (1, 1): "CAVE", (2, 1): "CAVE",
        (0, 2): "CAVE", (1, 2): "CAVE", (2, 2): "CAVE",
    }
    blocked_tiles: set[tuple[int, int]] = set()

    connectivity_result = analyze_connectivity(terrain, blocked_tiles)
    shape_components = connected_components(terrain, min_size=1, excluded_types=frozenset())

    connectivity_before = connectivity_result
    shape_components_before = list(shape_components)

    evaluate_hard_rule("fully_connected", connectivity_result.component_count == 1, config)
    for component in shape_components:
        evaluate_soft_rule("fill_ratio_healthy_band", component.fill_ratio, config)

    assert connectivity_result == connectivity_before
    assert shape_components == shape_components_before


def test_real_corpus_grading_smoke_test():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("dungeon_crawl")
    state, _report = WorldCompiler.compile(spec, seed=42)

    config = load_grade_config(_REAL_CONFIG_PATH)

    connectivity_result = analyze_connectivity(state.terrain, state.blocked_tiles)
    shape_components = connected_components(state.terrain)

    hard_result = evaluate_hard_rule(
        "fully_connected", connectivity_result.component_count == 1, config
    )
    soft_result = evaluate_soft_rule(
        "fill_ratio_healthy_band", shape_components[0].fill_ratio, config
    )

    combined_score = combine_rule_deltas([hard_result], [soft_result])
    grade = assign_grade(combined_score, config.grade_thresholds)

    assert grade in {"S", "A", "B", "C", "D", "F"}
    assert math.isfinite(combined_score)
