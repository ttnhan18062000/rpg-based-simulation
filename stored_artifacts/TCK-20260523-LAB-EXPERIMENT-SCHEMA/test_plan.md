---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-EXPERIMENT-SCHEMA
artifact_type: test_plan
tags: [lab, experiment, schema]
---

# Milestone 76 Test Plan

## Unit Tests

### `tests/unit/lab/test_experimentspec_schema.py`
- `test_valid_experimentspec_loads`: Verifies full compliant spec parses correctly.
- `test_missing_required_fields`: Verifies missing identifiers raise Pydantic errors.
- `test_invalid_types_or_budgets`: Checks negative values are rejected.
- `test_extra_fields_preserved`: Asserts unknown fields are kept under model extra properties.

### `tests/unit/lab/test_experimentspec_validator.py`
- `test_scenario_existence_checks`: Verifies target scenario is checked in `ScenarioRepository`.
- `test_same_seed_repeat_constraints`: Verifies repeat count > 1 is enforced.
- `test_baseline_comparison_constraints`: Verifies baseline_id presence is validated.
- `test_observability_modes_enforcement`: Verifies invalid observability modes are rejected.
- `test_validator_strict_mode`: Checks warnings are treated as errors.
- `test_no_execution_side_effects`: Confirms validation does not run or compile simulations.
