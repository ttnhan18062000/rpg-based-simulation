---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260518-APPLY-PATH-REDESIGN
phase: done
date: 2026-05-18
tags: [apply, path, redesign]
---

# TCK-20260518-APPLY-PATH-REDESIGN

## Title

Milestone 14: ApplyPath Structural Redesign via ApplyPlan precomputation

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement `ApplyPlan` and `ApplyPlanBuilder` to precompute and structure state updates, replacing repeated branching and checking during state application in `ApplyPath`.

## Scope

- Create `ApplyPlan` dataclass representing a precomputed execution plan.
- Create `ApplyPlanBuilder` to group and precompute changes by domain (navigation, combat, inventory, strategic, biological, identity, lifecycle, world-object).
- Integrate `ApplyPlanBuilder` into `ApplyPath.apply_generation`.
- Implement unit tests for `ApplyPlanBuilder`, integration tests for parity against old `ApplyPath`, and performance tests.

## Out of Scope

- Changes to authoritative game rules or simulation mechanics.

## Acceptance Criteria

- `ApplyPlan` output is deterministic.
- `ApplyPlan` + `ApplyPath` gives exact same final state as old `ApplyPath`.
- Entity/component replacement count decreases or remains minimal.
- `ApplyPath` p95 latency decreases in movement/resource scenarios.

## Related Tickets

- TCK-20260518-OPTIMIZATION-PROOF-REPORT

## Related Docs

- perf_plan_v2.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260518-APPLY-PATH-REDESIGN/

## Related Code Areas

- `src/engine/apply.py`
- `src/engine/apply_plan.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Designed `ApplyPlan` and `ApplyPlanBuilder` to precompute dictionary slices of affected entities and world collections.
- Decoupled pure entity transformation logic into `_compute_entity_changes`.
- Handled spatial cache invalidation hints cleanly in `ApplyPlanBuilder`.
- Preserved fast dataclass replacement mechanisms (`_fast_replace_entity`).

## Test Summary

- `pytest tests/unit/optimization/test_apply_plan_builder.py` (2 tests, 100% pass)
- `pytest tests/integration/optimization/test_apply_plan_parity.py` (1 test, 100% pass across full 17-phase pipeline)
- `pytest tests/perf/test_optimization_proof_report.py` (1 test, 100% pass)
- `pytest tests/api/test_rest_parity.py` (2 tests, 100% pass)

## Files Changed

- `src/engine/apply.py`
- `src/engine/apply_plan.py`
- `tests/unit/optimization/test_apply_plan_builder.py`
- `tests/integration/optimization/test_apply_plan_parity.py`

## Completion Summary

- Replaced heavy O(N) loop with precomputed dictionary lookups and sets, achieving complete structural parity and exceptional performance.
