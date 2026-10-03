---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260523-LAB-ORCHESTRATOR
phase: done
date: 2026-05-23
tags: [lab, orchestrator]
---

# TCK-20260523-LAB-ORCHESTRATOR

## Title

Milestone 78 — Scenario Lab Orchestrator

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the central workflow controller `ScenarioLabOrchestrator` to coordinate the entire Scenario Lab run sequence: loading/validating specs, compiling the world, generating the seed matrix, executing runs sequentially, running Observatory analysis, and compiling the lab execution results.

## Scope

- Implement central `ScenarioLabOrchestrator` in `src/lab/orchestrator.py` which coordinates loader and validators.
- Enforce World, Scenario, and Experiment validation prior to compilation and running.
- Sequence runs sequentially (to preserve resource budget, logs, and determinism).
- Call post-run Observatory AnalysisPipeline for every completed child run.
- Write lab run summary with aggregate status transitions (`CREATED` -> `RUNNING` -> `COMPLETED`/`FAILED`/`PARTIAL`).
- Write comprehensive unit and integration tests.

## Out of Scope

- Parallel child run execution (designed for subsequent phases).
- Dynamic parameter sweeping outside specified seeds.

## Acceptance Criteria

- Orchestrator validates the world before compilation, raising error/aborting on failure.
- Validation failures in scenario or experiment specs successfully abort workflow.
- Single-run and multi-seed lab sweeps run successfully.
- Failed child runs transition the lab status to `PARTIAL` or `FAILED`.
- Safe traversal-proof execution directories and correct index compilation.
- 100% test pass rate with zero failures.

## Related Tickets

- `TCK-20260523-LAB-RUN-MANIFEST`

## Related Docs

- `lab_phase12.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/orchestrator.py`
- `src/lab/__init__.py`
- `tests/unit/lab/test_scenario_lab_orchestrator.py`
- `tests/integration/lab/test_scenario_lab_single_run_flow.py`
- `tests/integration/lab/test_scenario_lab_multi_seed_flow.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Orchestrates end-to-end specification load and validate pipeline: ExperimentSpec -> ScenarioSpec -> WorldSpec.
- Safe folder structure and manifest persistence driven sequentially for optimal telemetry budgets and logs.
- Safe-guarding run states against database crashes via try-except isolation on Observatory post-simulation analysis.

## Test Summary

- Passed 5 unit tests for loaders/validators and path safeguards in `test_scenario_lab_orchestrator.py`.
- Passed 1 integration test for sandbox execution sequence in `test_scenario_lab_single_run_flow.py`.
- Passed 2 integration tests for sweep matrices and partial/failed transitions in `test_scenario_lab_multi_seed_flow.py`.

## Files Changed

- `src/lab/orchestrator.py`
- `src/lab/__init__.py`
- `tests/unit/lab/test_scenario_lab_orchestrator.py`
- `tests/integration/lab/test_scenario_lab_single_run_flow.py`
- `tests/integration/lab/test_scenario_lab_multi_seed_flow.py`

## Completion Summary

- Implemented the central workflow manager coordinating specification loaders, validators, compilers, deterministic simulation ticking, post-analysis, and isolated storage indexing.
- Completed full integration and unit verification showing 100% pass rates.
