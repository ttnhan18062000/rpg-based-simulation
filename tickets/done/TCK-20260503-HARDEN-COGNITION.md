# TCK-20260503-HARDEN-COGNITION

## Title
Hardening RPG Strategic Cognition and Tactical Legality

## Status
DONE

## Request Summary
Complete the hardening of the RPG V2 engine by finalizing Domain 2 (Tactical Decision Boundedness) and Domain 3 (Strategic Cognition).

## Scope
- Enforce cognitive capacity limits and early exits for incapacitated entities in Strategic Cognition.
- Finalize staggered update frequency (10-tick) across all strategic entry points.
- Ensure robust legality guards for incapacitated entities in the tactical pipeline.
- Ratify Phase 9 ledger rows (moving from UNSUPPORTED to SUPPORTED).

## Out of Scope
- Implementation of new strategic behaviors (e.g., betrayal, rumors) beyond what is already present or needed for hardening.

## Acceptance Criteria
- Incapacitated entities (stunned/frozen) do not evaluate strategic concerns or intents.
- Strategic evaluation (concerns/intent) follows a strict 10-tick staggered frequency.
- Tactical decisions are rejected for incapacitated actors.
- All regression tests in `tests/engine/test_strategic_hardening.py` pass.
- New tests for status-based early exits pass.

## Related Tickets
- None

## Related Docs
- `docs/engine/phase9_entry_support_boundary.md`
- `docs/archive/resource_v2/logic_checklist_exhaustive.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/systems/strategic.py`
- `src/engine/tactical.py`
- `src/engine/legality.py`
- `src/strategy/cognition_capacity.py`

## Assumptions / Open Questions
- None

## Implementation Notes
- Use `(state.tick + entity.id) % 10 == 0` for staggering to ensure even distribution.

## Test Summary
- tests/engine/test_status_hardening.py (Status guards and frequency): 3/3 passed.
- tests/engine/test_strategic_hardening.py (Strategic logic): 6/6 passed.
- scripts/ledger_validator.py: 1015/1437 logic items (70.6%) verified.

## Files Changed
- src/systems/strategic.py
- src/core/enums.py
- docs/engine/phase9_entry_support_boundary.md
- docs/archive/resource_v2/logic_checklist_exhaustive.md

## Completion Summary
- Implemented incapacitated status guards (frozen/stunned) in strategic cycles.
- Enforced 10-tick staggered frequency for strategic processing.
- Fixed missing roles (WORKER, GUARD) in EntityRole enum.
- Updated documentation and exhaustive logic checklist with proof markers.
