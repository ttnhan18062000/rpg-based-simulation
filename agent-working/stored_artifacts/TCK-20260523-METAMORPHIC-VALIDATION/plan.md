---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-METAMORPHIC-VALIDATION
artifact_type: plan
tags: [metamorphic, validation]
---

# Metamorphic Validation Rules - Implementation Plan

We will implement **Milestone 87: Metamorphic Validation Rules** by designing a dedicated metamorphic testing module, integrating it with the lab schemas, and writing a comprehensive test suite.

---

## Proposed Changes

### Lab Component

#### [NEW] [metamorphic.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/metamorphic.py)
Create a modular domain file defining:
1. `MetamorphicComparisonResult`: A typed Pydantic model for carrying assertion outcomes:
   - `rule_id`: unique relationship ID
   - `status`: `"PASSED"` | `"FAILED"` | `"INSUFFICIENT_DATA"`
   - `weak_evidence`: bool
   - `baseline_value`: float (optional)
   - `compared_value`: float (optional)
   - `message`: string description
2. `MetamorphicRule`: Evaluation class wrapping `ExpectedRelationshipSpec` and containing validation logic for:
   - `monotonic_non_decreasing`
   - `monotonic_non_increasing`
   - `within_tolerance`
   - `expected_worse`
   - `expected_better`
   - `no_new_hard_law_violation`
3. `MetamorphicRuleEngine`: Central orchestrator providing a static `.evaluate_rules(rules, variant_metrics)` method.

#### [MODIFY] [schema.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/schema.py)
- Import `MetamorphicComparisonResult` from `src.lab.metamorphic`.

#### [MODIFY] [__init__.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/__init__.py)
- Import and export `MetamorphicRule`, `MetamorphicRuleEngine`, and `MetamorphicComparisonResult` in the package public API.

---

## Verification Plan

### Automated Tests
We will add two testing modules:
1. Unit Tests: `tests/unit/lab/test_metamorphic_rules.py` verifying all rules under positive, negative, missing telemetry, and weak evidence scenarios.
2. Integration Tests: `tests/integration/lab/test_metamorphic_validation_flow.py` checking complete sweep outcome validation.

Run command:
```bash
pytest tests/unit/lab/test_metamorphic_rules.py tests/integration/lab/test_metamorphic_validation_flow.py -v
```
