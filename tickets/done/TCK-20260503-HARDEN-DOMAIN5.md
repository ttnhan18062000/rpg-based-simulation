---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260503-HARDEN-DOMAIN5
phase: done
date: 2026-05-03
tags: [harden, domain5]
---

# TCK-20260503-HARDEN-DOMAIN5

## Title
Hardening Navigation and Ecology (Domain 5)

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Close specialized navigation and anchored-world behavior not covered by basic movement. Finalize Flow Field logic, tactical movement integration, arena stop conditions, and mob ecology.

## Scope
- Implement robust Flow Field navigation for long-distance targets.
- Ensure tactical movement modes (RETREAT, PURSUE, etc.) are fully integrated into navigation execution.
- Finalize arena stop conditions (WIPE, TIMEOUT, WATCHDOG) in a centralized manner.
- Complete mob ecology (leash/camp/hunt) logic and verify with tests.

## Acceptance Criteria
- FlowFieldService provides deterministic, non-linear vectors for long-range targets.
- NavigationSystem respects MovementMode from TacticalDecisionSystem.
- CertificationHarness successfully terminates on WIPE, TIMEOUT, and WATCHDOG.
- Mobs correctly return to camp when beyond leash/chase limits.
- All tests in `tests/engine/test_flow_field_navigation.py`, `test_arena_stop_conditions.py`, `test_watchdog.py`, and `test_mob_leashing.py` pass.

## Related Code Areas
- `src/systems/navigation.py`
- `src/engine/tactical.py`
- `src/engine/movement.py`
- `src/certification/harness.py`
- `src/engine/rpg_depth.py`

## Implementation Notes
- I will implement a multi-anchor flow field for better global navigation.
- I will integrate movement speed scaling based on MovementMode.

## Test Summary
- TBD

## Files Changed
- TBD
