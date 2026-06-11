---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260527-COG-PHASE1-INTENTS
phase: done
date: 2026-05-27
tags: [cog, phase1, intents]
---

# TCK-20260527-COG-PHASE1-INTENTS

## Title

Implement Phase 1 ActionIntent Adapter Layer

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement ActionIntent schema and adapter to trace and adapt strategic intent choices into existing game loop updates/state actions without breaking core game systems.

## Scope

- Create `ActionIntent` schema under `src/engine/intent/action_intent.py`.
- Implement `ActionIntentAdapter` delegates translating to core actions.
- Implement intent trace recording.
- Verify through unit tests in `tests/unit/strategic/test_intents.py`.

## Out of Scope

- Implementing the route-family classifier or performance budget gates.

## Acceptance Criteria

- `ActionIntent` accurately represents all 11 required Phase 1 intents.
- Execution delegates correctly and creates the expected state/entity updates.
- Tracing is recorded with opportunity source and checked requirements.
- Unit tests pass.

## Related Tickets

- None

## Related Docs

- `entity_enhance_phase1.md` (Task 8)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/engine/intent/action_intent.py`
- `tests/unit/strategic/test_intents.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Designed `ActionIntent` and `IntentTrace` dataclasses with slots support.
- Built `ActionIntentAdapter` to support requirement-based honest gating and delegation to existing ActionRouter verbs.

## Test Summary

- Run `pytest tests/unit/strategic/test_intents.py` verifying MOVE_TO, BUY_ITEM, and REQUEST_CRAFT with requirements trace checks.
- All 4 tests pass successfully.

## Files Changed

- `src/engine/intent/action_intent.py`
- `tests/unit/strategic/test_intents.py`

## Completion Summary

- ActionIntent schema and ActionIntentAdapter fully implemented and tested. Verification proves requirement-gated routing works seamlessly on the substrate engine.

