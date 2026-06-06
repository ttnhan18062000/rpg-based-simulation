# TCK-20260523-LAB-SCENARIO-SCHEMA

## Title

Milestone 75 — ScenarioSpec Schema

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Define the test intent separately from the world. Create a file-based ScenarioSpec schema, pluggable rules validator (with metrics/signals/anomalies permissiveness), and a safe path-traversal-proof repository.

## Scope

- Create a new package `src/lab/`
- Implement `ScenarioSpec` Pydantic schema in `src/lab/schema.py`
- Implement validation rules in `src/lab/validator.py`
  - Verifies target `world_id` exists in `WorldRepository`.
  - Warns on unrecognized metrics, signals, and anomalies.
- Implement `ScenarioRepository` in `src/lab/repository.py`
  - Path traversal checks.
  - Indexing manifest under `data/scenarios/scenario_index.json`.
- Implement E2E unit testing suite in `tests/unit/lab/`

## Out of Scope

- Implementing `ExperimentSpec` or orchestrator logic (Milestone 76/78).

## Acceptance Criteria

- Schema successfully loads compliant YAML. (Passed)
- Validator identifies structural issues and cross-references. (Passed)
- Permissive validation issues warn correctly on unknown metrics. (Passed)
- 100% test coverage with zero failures. (Passed: 15/15 unit tests passing cleanly with no warnings)

## Related Tickets

- `TCK-20260523-WORLD-BUDGET-GUARDRAILS`

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

- Unrecognized expected metrics produce a `WARNING`, allowing custom telemetry extensions (Option B).
- Standard signals, events, cognition, and anomalies check against reference registries and warn on unrecognized strings (Option A).
- Verify target `world_id` exists against `WorldRepository` actively in the validator (Option A).

## Implementation Notes

- Implemented `timezone.utc` aware datetime indexer instead of deprecated `datetime.utcnow()` to prevent deprecation warnings in Python 3.13.

## Test Summary

- Added 3 comprehensive test suites:
  - `tests/unit/lab/test_scenariospec_schema.py` (5 tests)
  - `tests/unit/lab/test_scenariospec_validator.py` (6 tests)
  - `tests/unit/lab/test_scenario_repository.py` (4 tests)
- Verified E2E correctness with 15/15 tests passing, zero warnings.

## Files Changed

- `src/lab/__init__.py`
- `src/lab/schema.py`
- `src/lab/validator.py`
- `src/lab/repository.py`
- `tests/unit/lab/test_scenariospec_schema.py`
- `tests/unit/lab/test_scenariospec_validator.py`
- `tests/unit/lab/test_scenario_repository.py`

## Completion Summary

- Designed and implemented the complete `src.lab` domain package to establish Milestone 75's foundational data spec layer.
- Enabled test isolation by decoupling worlds and scenarios.
- Integrated path-traversal checks, manifest indexing manifests, and strict/permissive pluggable rules validations.
