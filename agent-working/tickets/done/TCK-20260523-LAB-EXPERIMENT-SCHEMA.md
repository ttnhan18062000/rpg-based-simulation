---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260523-LAB-EXPERIMENT-SCHEMA
phase: done
date: 2026-05-23
tags: [lab, experiment, schema]
---

# TCK-20260523-LAB-EXPERIMENT-SCHEMA

## Title

Milestone 76 — ExperimentSpec Schema

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Define how the scenarios should be executed. Create an ExperimentSpec schema, validation rules checking scenarios, parameters, budgets, and retention limits, and a safe traversal-proof repository.

## Scope

- Implement Pydantic models for experiment specifications in `src/lab/schema.py`.
- Implement pluggable rules in `src/lab/validator.py`:
  - `ScenarioExistenceRule` actively checking that target `scenario_id` exists in `ScenarioRepository`.
  - `ExperimentParameterRule` enforcing bounds and type constraints.
  - `ExperimentObservabilityRule` checking validity of the observability modes.
- Implement `ExperimentRepository` in `src/lab/repository.py` supporting path traversal checks and global manifest index compilation.
- Export all components in `src/lab/__init__.py`.
- Add unit test suites in `tests/unit/lab/` ensuring 100% coverage and zero warnings.

## Out of Scope

- Implementing the orchestrator runtime executor (Milestone 78).
- Implementing Observatory execution telemetry (Milestone 79).

## Acceptance Criteria

- Schema successfully loads compliant YAML experiment files.
- Validator identifies reference issues, parameter constraints, and invalid run modes.
- Enforces same-seed-repeat count limits and baseline reference checks.
- Traversal-proof repository prevents security violations.
- 100% test coverage with zero failures.

## Related Tickets

- `TCK-20260523-LAB-SCENARIO-SCHEMA`

## Related Docs

- `lab_phase12.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/schema.py`
- `src/lab/validator.py`
- `src/lab/repository.py`
- `src/lab/__init__.py`

## Assumptions / Open Questions

- We enforce explicit `experiment_type` at the root of `ExperimentSpec` (Option A).
- We actively inject `ScenarioRepository` into `ExperimentSpecValidator` to verify referenced scenario existence (Option A).
- The baseline reference `baseline_id` is specified inside `analysis` section and verified when `experiment_type` is `baseline_comparison` (Option A).

## Implementation Notes

- Fully leveraged frozen Pydantic models with `model_config = ConfigDict(frozen=True)` to prevent ad-hoc mutation of active runtime targets.

## Test Summary

- Complete pytest lab suite execution passing with 29 passed tests, zero errors, and zero warnings.
- Test coverage covers:
  - `tests/unit/lab/test_experimentspec_schema.py`: 4 tests
  - `tests/unit/lab/test_experimentspec_validator.py`: 6 tests
  - `tests/unit/lab/test_experiment_repository.py`: 4 tests

## Files Changed

- `src/lab/schema.py`
- `src/lab/validator.py`
- `src/lab/repository.py`
- `src/lab/__init__.py`
- `tests/unit/lab/test_experimentspec_schema.py`
- `tests/unit/lab/test_experimentspec_validator.py`
- `tests/unit/lab/test_experiment_repository.py`

## Completion Summary

- Successfully completed Milestone 76, closing out the structural data schemas, validations, and storage layers for scenario experiments. Fully verified security safety of repository logic and registered all exports, establishing a strong, solid base for executing and analyzing sandbox simulation runs.
