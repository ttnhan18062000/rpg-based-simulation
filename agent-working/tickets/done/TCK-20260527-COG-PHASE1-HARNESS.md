---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260527-COG-PHASE1-HARNESS
phase: done
date: 2026-05-27
tags: [cog, phase1, harness]
---

# TCK-20260527-COG-PHASE1-HARNESS

## Title

Create Scenario-Driven TDD Test Harness for Phase 1

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the scenario runner that parses scenario specification files, executes synchronous ticks deterministically, captures route traces, and compiles diagnostic scorecards/metrics outputs. The test suite must verify the harness loading and scoring, showing initial TDD failures before world registries are added.

## Scope

- Implement YAML parser and model mappings under `src/testing/scenario_runner.py`.
- Capture lifepath execution traces, timing metrics, and scorecard logs (`scenario_scorecard.json`, `route_trace.jsonl`).
- Add comprehensive unit tests in `tests/unit/strategic/test_scenario_runner.py` verifying harness capabilities.
- Proactively use TDD, ensuring scenarios fail legally before the backend capabilities exist.

## Out of Scope

- Implementing the production data registries or providers (these belong to Tasks 2-8).

## Acceptance Criteria

- `scenario_runner.py` compiles and correctly evaluates scorecard PASS/FAIL status.
- Scorecard tracks route families, ticks, provider metrics, and logs.
- Automated TDD tests under `tests/unit/strategic/test_scenario_runner.py` run and pass.

## Related Tickets

- None

## Related Docs

- `entity_enhance_phase1.md` (Task 1)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/testing/scenario_runner.py`
- `tests/unit/strategic/test_scenario_runner.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Use native Python `PyYAML` loader to read `.yaml` specs.

## Test Summary

- Automated tests successfully implemented and passing: `pytest tests/unit/strategic/test_scenario_runner.py`.

## Files Changed

- `tickets/inprogress/TCK-20260527-COG-PHASE1-HARNESS.md`
- `src/testing/scenario_runner.py`
- `tests/unit/strategic/test_scenario_runner.py`

## Completion Summary

- Implemented `ScenarioRunner` successfully supporting YAML loading, deterministic synchronous loop execution, trace logging, and JSON scorecards generation. Added test suite validating loading and reports. All tests pass successfully!
