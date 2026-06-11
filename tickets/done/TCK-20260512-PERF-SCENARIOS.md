---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260512-PERF-SCENARIOS
phase: done
date: 2026-05-12
tags: [perf, scenarios]
---

# TCK-20260512-PERF-SCENARIOS

## Title
Implement performance scenario builders

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement scenario builders to construct various simulation states for performance testing, as specified in `performance_implementation.md`.

## Scope
- [x] Create `src/perf/scenarios.py`.
- [x] Implement builders for Idle, Resource, Movement, Combat, Strategic, and Mixed states.

## Out of Scope
- Enhancement of BenchHarness.

## Acceptance Criteria
- `src/perf/scenarios.py` exists and contains all required builders.
- Builders return a valid `AuthoritativeState`.
- Entities are constructed using `V2EntityBuilder`.
- Scenarios are deterministic (respect the `seed` argument).

## Related Tickets
- TCK-20260512-PERF-INVESTIGATION (Done)
- TCK-20260512-PERF-PROFILES (Done)

## Related Docs
- [performance_implementation.md](file:///home/vboxuser/Work/rpg-based-simulation/performance_implementation.md)

## Related Code Areas
- `src/perf/`
- `src/core/builder.py`
- `src/core/state.py`

## Implementation Notes
- Use `range(1, entity_count + 1)` for IDs.
- Ensure entities are marked as `active=True`.

## Test Summary
- Verify that each builder can produce a state that can be ticked once by a Kernel.

## Files Changed
- [NEW] src/perf/scenarios.py

## Completion Summary
- N/A
