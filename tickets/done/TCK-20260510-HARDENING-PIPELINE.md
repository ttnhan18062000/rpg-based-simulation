---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260510-HARDENING-PIPELINE
phase: done
date: 2026-05-10
tags: [hardening, pipeline]
---

# TCK-20260510-HARDENING-PIPELINE

## Title
Hardening Authoritative Engine Pipeline and Audit

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Stabilize the RPG Authoritative Engine by resolving persistent regressions in quest progression, regional debuffs, and state reconciliation.

## Scope
- Re-order pipeline phases (Governance after Action Routing).
- Harden Authoritative Override logic (selective clearing).
- Implement rejection audit for economy transactions.
- Harmonize transaction trace strings.

## Out of Scope
- Major architectural changes to the ECS structure.

## Acceptance Criteria
- 100% pass rate in `tests/engine`, `tests/arena`, and `tests/replay`.
- Replay determinism verified for "FAIL" transactions.
- Regional debuffs apply correctly to authoritative action outcomes.

## Implementation Notes
- Law 300.2 (Authoritative Override) refined to preserve navigation while clearing readiness/combat/quest deltas.
- `ResourceTransactionSystem` now records `RejectionEvent` objects for audit traceability.
- `TownResolutionSystem` moved downstream of action re-execution to ensure environmental modifiers consume ground-truth states.

## Test Summary
- All 296 tests passed.
- Verified fix for `test_arena_conquest_and_debuff`.
- Verified fix for `test_partial_rejection_occupancy_vs_combat`.
- Verified fix for `test_rejection_audit_aggregation`.

## Files Changed
- `src/engine/pipeline.py`
- `src/engine/economy.py`
- `tests/replay/test_event_replay.py`

## Completion Summary
The authoritative engine has been successfully hardened. All known regressions from the V2 design shift have been resolved, and the pipeline now correctly enforces the "Law of Truth" where authoritative re-execution overrides worker proposals while maintaining partial rejection transparency for unrelated manual intents.
