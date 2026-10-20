---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261019-CATALOG-ARENA-SMOKE-TICK-3-BUDGET-OVERRUN-AFTER-645
phase: open
date: 2026-10-19
tags: []
---

# TCK-20261019-CATALOG-ARENA-SMOKE-TICK-3-BUDGET-OVERRUN-AFTER-645

## Title
The catalog arena smoke fails its tick budget at tick 3 (479.5 ms > 150 ms) in the first slow run after #645

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
#390 W43 digest: `tests/integration/certification/test_catalog_arena_smoke.py::test_catalog_arena_small_can_tick` is new and unowned, first seen 2026-10-19 in slow run 39172879323 (job 117809466869). It is the first slow run after #645 (3597c08d3). The failure: `CATALOG_ARENA_SMALL failed after 3 ticks: failure_kind=FAILED_ENVELOPE, reason=Tick budget violation: 479.5ms > 150.0ms at tick 3`. That is a wall-clock budget, so it may be a real one-off cost (for example a cache warm-up that #645 added: terrain cost, route search or the event catalog) or host noise.

## Scope
- Reproduce locally on main (serially, quiet host), 3 repeats, and record each tick's compute time for ticks 1-10.
- If tick 3 is consistently over: profile that tick, name the cost and the #645 ticket it came from, and propose the fix (move the warm-up out of the budgeted tick, or make it cheaper). Measure the fix hash-identical.
- If it isn't reproducible: record it as a host-noise flake and say whether the certification envelope should exclude the first ticks. That is a certification-contract question, which goes to rpg-planner.

## Out of Scope
- Changing the 150 ms budget, unless the contract says the first ticks are excluded.

## Acceptance Criteria
- The cause is named with numbers, and the test passes 3/3 locally after the fix. Or the flake is classified with evidence.
- #390 is claimed with this ticket id.

## Related Tickets
- #390 (slow-regression digest), #645
- TCK-20261019-SOAK-WATCHDOG-BUDGET-OVERRUNS-NEED-A-QUIET-HOST-READING (a similar wall-clock symptom)

## Related Docs
- docs/engine/performance_contract.md
- contracts/certification_contract.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/integration/certification/test_catalog_arena_smoke.py
- the certification runner (tick budget envelope)

## Assumptions / Open Questions
- Only one slow run has failed so far.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
