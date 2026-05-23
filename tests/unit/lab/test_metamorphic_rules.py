# Compliance IDs: METAMORPHIC-TEST-001, METAMORPHIC-TEST-002, METAMORPHIC-TEST-003
import pytest
from src.lab.schema import ExpectedRelationshipSpec
from src.lab.metamorphic import MetamorphicRuleEngine, MetamorphicRule, MetamorphicComparisonResult


def test_monotonic_non_decreasing_passes_when_metric_increases():
    """Verify that monotonic_non_decreasing passes when compared metric increases or stays the same."""
    spec = ExpectedRelationshipSpec(
        id="rule_1",
        type="monotonic_non_decreasing",
        metric="resource_production_rate",
        baseline_variant="base",
        compared_variant="var_1"
    )

    metrics = {
        "base": {"run_count": 5, "resource_production_rate": 10.0},
        "var_1": {"run_count": 5, "resource_production_rate": 12.5}
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec], metrics)
    assert len(results) == 1
    assert results[0].status == "PASSED"
    assert results[0].baseline_value == 10.0
    assert results[0].compared_value == 12.5
    assert results[0].weak_evidence is False


def test_monotonic_non_decreasing_fails_when_metric_decreases():
    """Verify that monotonic_non_decreasing fails when compared metric decreases."""
    spec = ExpectedRelationshipSpec(
        id="rule_1",
        type="monotonic_non_decreasing",
        metric="resource_production_rate",
        baseline_variant="base",
        compared_variant="var_1"
    )

    metrics = {
        "base": {"run_count": 5, "resource_production_rate": 10.0},
        "var_1": {"run_count": 5, "resource_production_rate": 7.5}
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec], metrics)
    assert len(results) == 1
    assert results[0].status == "FAILED"


def test_monotonic_non_increasing_passes_when_metric_decreases():
    """Verify that monotonic_non_increasing passes when compared metric decreases or stays the same."""
    spec = ExpectedRelationshipSpec(
        id="rule_1",
        type="monotonic_non_increasing",
        metric="stuck_entity_ratio",
        baseline_variant="base",
        compared_variant="var_1"
    )

    metrics = {
        "base": {"run_count": 5, "stuck_entity_ratio": 0.15},
        "var_1": {"run_count": 5, "stuck_entity_ratio": 0.05}
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec], metrics)
    assert len(results) == 1
    assert results[0].status == "PASSED"


def test_monotonic_non_increasing_fails_when_metric_increases():
    """Verify that monotonic_non_increasing fails when compared metric increases."""
    spec = ExpectedRelationshipSpec(
        id="rule_1",
        type="monotonic_non_increasing",
        metric="stuck_entity_ratio",
        baseline_variant="base",
        compared_variant="var_1"
    )

    metrics = {
        "base": {"run_count": 5, "stuck_entity_ratio": 0.15},
        "var_1": {"run_count": 5, "stuck_entity_ratio": 0.25}
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec], metrics)
    assert len(results) == 1
    assert results[0].status == "FAILED"


def test_within_tolerance_handles_small_differences():
    """Verify that within_tolerance handles variations within and outside specified tolerance band."""
    spec_pass = ExpectedRelationshipSpec(
        id="rule_tol_pass",
        type="within_tolerance",
        metric="resource_production_rate",
        baseline_variant="base",
        compared_variant="var_1",
        tolerance=2.0
    )
    spec_fail = ExpectedRelationshipSpec(
        id="rule_tol_fail",
        type="within_tolerance",
        metric="resource_production_rate",
        baseline_variant="base",
        compared_variant="var_2",
        tolerance=1.0
    )

    metrics = {
        "base": {"run_count": 5, "resource_production_rate": 10.0},
        "var_1": {"run_count": 5, "resource_production_rate": 11.5},
        "var_2": {"run_count": 5, "resource_production_rate": 11.5}
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec_pass, spec_fail], metrics)
    assert results[0].status == "PASSED"
    assert results[1].status == "FAILED"


def test_expected_worse_passes_when_target_metric_worsens():
    """Verify expected_worse assertions pass when metric shifts in unfavorable direction."""
    # stuck_entity_ratio: worse is HIGHER
    spec_stuck = ExpectedRelationshipSpec(
        id="rule_stuck",
        type="expected_worse",
        metric="stuck_entity_ratio",
        compared_variant="var_1"
    )
    # resource_production_rate: worse is LOWER
    spec_resource = ExpectedRelationshipSpec(
        id="rule_resource",
        type="expected_worse",
        metric="resource_production_rate",
        compared_variant="var_1"
    )

    metrics = {
        "base": {
            "run_count": 5,
            "stuck_entity_ratio": 0.10,
            "resource_production_rate": 10.0
        },
        "var_1": {
            "run_count": 5,
            "stuck_entity_ratio": 0.20,  # higher -> worse
            "resource_production_rate": 8.0  # lower -> worse
        }
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec_stuck, spec_resource], metrics)
    assert results[0].status == "PASSED"
    assert results[1].status == "PASSED"


def test_no_new_hard_law_violation_fails_on_hard_law_violation():
    """Verify no_new_hard_law_violation fails if compared variant introduces violations."""
    spec = ExpectedRelationshipSpec(
        id="rule_law",
        type="no_new_hard_law_violation",
        metric="hard_law_violations",
        compared_variant="var_1"
    )

    metrics = {
        "base": {"run_count": 5, "hard_law_violations": 0},
        "var_1": {"run_count": 5, "hard_law_violations": 2}
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec], metrics)
    assert results[0].status == "FAILED"


def test_missing_metric_produces_insufficient_data():
    """Verify that a missing metric yields INSUFFICIENT_DATA cleanly instead of crash or false pass."""
    spec = ExpectedRelationshipSpec(
        id="rule_missing",
        type="monotonic_non_decreasing",
        metric="stuck_entity_ratio",
        compared_variant="var_1"
    )

    # Missing from compared variant
    metrics = {
        "base": {"run_count": 5, "stuck_entity_ratio": 0.1},
        "var_1": {"run_count": 5}
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec], metrics)
    assert len(results) == 1
    assert results[0].status == "INSUFFICIENT_DATA"
    assert "missing" in results[0].message


def test_missing_metric_is_not_treated_as_pass():
    """Verify anti-misdirection that missing metric does not result in PASSED."""
    spec = ExpectedRelationshipSpec(
        id="rule_missing",
        type="monotonic_non_decreasing",
        metric="non_existent",
        compared_variant="var_1"
    )

    metrics = {
        "base": {"run_count": 5},
        "var_1": {"run_count": 5}
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec], metrics)
    assert results[0].status == "INSUFFICIENT_DATA"
    assert results[0].status != "PASSED"


def test_weak_baseline_is_marked_as_weak_evidence():
    """Verify weak baseline/compared variant seed counts are flagged with weak_evidence."""
    spec = ExpectedRelationshipSpec(
        id="rule_weak",
        type="monotonic_non_decreasing",
        metric="stuck_entity_ratio",
        compared_variant="var_1"
    )

    metrics = {
        "base": {"run_count": 2, "stuck_entity_ratio": 0.1},  # weak (run_count < 3)
        "var_1": {"run_count": 5, "stuck_entity_ratio": 0.2}
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec], metrics)
    assert results[0].status == "PASSED"
    assert results[0].weak_evidence is True


def test_expected_worse_does_not_mean_engine_failure():
    """Verify failed expected worse does not raise an exception, but returns status='FAILED'."""
    spec = ExpectedRelationshipSpec(
        id="rule_worse",
        type="expected_worse",
        metric="stuck_entity_ratio",
        compared_variant="var_1"
    )

    metrics = {
        "base": {"run_count": 5, "stuck_entity_ratio": 0.20},
        "var_1": {"run_count": 5, "stuck_entity_ratio": 0.10}  # improved, so not worse!
    }

    results = MetamorphicRuleEngine.evaluate_rules([spec], metrics)
    assert results[0].status == "FAILED"
