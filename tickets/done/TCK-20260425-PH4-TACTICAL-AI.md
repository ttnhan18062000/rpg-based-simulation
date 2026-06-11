---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260425-PH4-TACTICAL-AI
phase: done
date: 2026-04-25
tags: [ph4, tactical, ai]
---

# TCK-20260425-PH4-TACTICAL-AI

## Title

Tactical AI Recovery and Cognitive Capacity Hardening

## Status

INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Phase 4 of the V2 Engine roadmap: Tactical AI roles, melee/ranged behavior differences, and enforce strategic cognition capacity limits (max projects/leads/concerns).

## Scope

- Implement `TacticalRole` enum/logic in `CombatComponent`.
- Implement role-based positioning (Vanguard: Close, Skirmisher: Kite).
- Enforce `CognitionProfile` limits in `StrategicIntelligenceSystem`.
- Add bit-identical parity tests for tactical behavior.

## Out of Scope

- Advanced chokepoint detection (Task 4.3).
- Social contract implementation (Phase 9).

## Acceptance Criteria

- [x] `TacticalRole` field exists in `CombatComponent`.
- [x] `Vanguard` role closes distance to target.
- [x] `Skirmisher` role kites target when within range.
- [x] `StrategicUpdate` is suppressed if `max_active_projects` is reached.
- [x] All tactical parity tests pass.

## Related Tickets

- TCK-20260424-PH0-TASK0-1 (Closed)

## Related Docs

- resource_v2_e_phases.md

## Related Code Areas

- src/core/state.py
- src/engine/tactical.py
- src/systems/strategic.py

## Implementation Notes

- Divergence: V2 uses `tactical_role` field instead of legacy implicit role logic to ensure determinism.

## Test Summary

- tests/parity/test_tactical_roles.py (Passed)

## Files Changed

- src/core/state.py
- src/core/builder.py
- src/engine/tactical.py
- src/systems/strategic.py
- resource_v2_e_phases.md

## Completion Summary

- Basic tactical AI roles and capacity limits implemented and verified.
