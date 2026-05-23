# Compliance IDs: METAMORPHIC-INTEGRATION-001
import pytest
from src.lab.schema import ExpectedRelationshipSpec, ExperimentSpec
from src.lab.metamorphic import MetamorphicRuleEngine


def test_metamorphic_validation_flow():
    """
    Integration test validating that the MetamorphicRuleEngine correctly evaluates
    multiple rules representing real experiment design constraints.
    """
    # 1. Define relationships (normally loaded from experiment.yaml)
    rule_productivity = ExpectedRelationshipSpec(
        id="rel_production_rate_one_mut",
        type="monotonic_non_decreasing",
        metric="resource_production_rate",
        baseline_variant="base",
        compared_variant="var_one_mut_0"
    )
    rule_stuck = ExpectedRelationshipSpec(
        id="rel_stuck_entity_expected_worse",
        type="expected_worse",
        metric="stuck_entity_ratio",
        baseline_variant="base",
        compared_variant="var_one_mut_1"
    )
    rule_law = ExpectedRelationshipSpec(
        id="rel_no_law_violations",
        type="no_new_hard_law_violation",
        metric="hard_law_violations",
        baseline_variant="base",
        compared_variant="var_one_mut_0"
    )

    rules = [rule_productivity, rule_stuck, rule_law]

    # 2. Simulate metrics gathered from variant execution sweeps
    variant_metrics = {
        "base": {
            "run_count": 5,
            "resource_production_rate": 10.2,
            "stuck_entity_ratio": 0.05,
            "hard_law_violations": 0
        },
        "var_one_mut_0": {
            "run_count": 5,
            "resource_production_rate": 12.8,  # increased -> pass monotonic_non_decreasing
            "stuck_entity_ratio": 0.04,
            "hard_law_violations": 0  # same -> pass no_new_hard_law_violation
        },
        "var_one_mut_1": {
            "run_count": 5,
            "resource_production_rate": 9.5,
            "stuck_entity_ratio": 0.12,  # increased -> pass expected_worse
            "hard_law_violations": 1
        }
    }

    # 3. Evaluate rules
    results = MetamorphicRuleEngine.evaluate_rules(rules, variant_metrics)

    # 4. Assert all results evaluated and passed
    assert len(results) == 3
    assert all(r.status == "PASSED" for r in results)

    # Verify individual results match the logic
    prod_res = next(r for r in results if r.rule_id == "rel_production_rate_one_mut")
    assert prod_res.baseline_value == 10.2
    assert prod_res.compared_value == 12.8

    stuck_res = next(r for r in results if r.rule_id == "rel_stuck_entity_expected_worse")
    assert stuck_res.baseline_value == 0.05
    assert stuck_res.compared_value == 0.12

    law_res = next(r for r in results if r.rule_id == "rel_no_law_violations")
    assert law_res.baseline_value == 0.0
    assert law_res.compared_value == 0.0
