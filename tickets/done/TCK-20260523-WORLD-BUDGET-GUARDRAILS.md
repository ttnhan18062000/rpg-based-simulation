# TCK-20260523-WORLD-BUDGET-GUARDRAILS

## Title

Milestone 74 — Resource and Storage Guardrails

## Status

DONE

## Request Summary

Implement robust budget specifications and runtime/compile guardrails to restrict entity populations, regional area, and forecasted telemetry storage size, avoiding huge accidental workloads under various execution profiles (`local_dev`, `ci`, `long_run_lab`).

## Scope

- Extend `WorldSpec` schema to support an optional `budgets` section:
  - `max_entities`, `max_regions`, `max_resource_nodes`, `max_buildings`, `max_expected_artifact_mb`
- Implement profile configurations with custom default thresholds:
  - `local_dev`: Max 1000 entities
  - `ci`: Max 500 entities
  - `long_run_lab`: Max 10,000 entities
- Implement a pluggable rules validator checking budget limits:
  - Validates overall entity populations, resource nodes, regions, buildings, map area, and estimated artifact size.
  - Limits elevated to `ERROR` or `WARNING` depending on profile and strictness settings.
- Implement an artifact storage size estimator:
  - Estimates output artifact log sizes using ticks and counts to prevent runaways.
- Include a comprehensive suite of unit tests in `tests/unit/worldbuilding/test_world_budget_guardrails.py`.

## Out of Scope

- Implementing real-time dynamic memory/disk limit monitors in OS system processes.

## Acceptance Criteria

- Budget constraints successfully modeled in `WorldSpec`.
- Validator correctly enforces constraints and profiles.
- Oversized worlds successfully blocked in local dev and CI.
- 100% test coverage with all new guardrail tests passing.

## Related Tickets

- `TCK-20260523-WORLD-TEST-STRATEGY`

## Related Docs

- `world_phase11.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260523-WORLD-BUDGET-GUARDRAILS/`

## Related Code Areas

- `src/worldbuilding/schema.py`
- `src/worldbuilding/validator.py`
- `tests/unit/worldbuilding/test_world_budget_guardrails.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Added `BudgetSpec` class in `schema.py`.
- Added default `BUDGET_PROFILES` map and integrated `BudgetGuardrailRule` validation logic inside `validator.py`.
- Enforces strict constraints on entities and regions (`ERROR`) and sanity warnings on resource nodes, buildings, area size, and telemetry footprints (`WARNING`).

## Test Summary

- Added 7 unit tests in `tests/unit/worldbuilding/test_world_budget_guardrails.py`, passing with 100% success rate.

## Files Changed

- `src/worldbuilding/schema.py`
- `src/worldbuilding/validator.py`
- `tests/unit/worldbuilding/test_world_budget_guardrails.py`

## Completion Summary

- Delivered robust, profile-aware resource limits and telemetry storage forecast guardrails, verifying absolute protection against out-of-bound layouts or runaway log files.
