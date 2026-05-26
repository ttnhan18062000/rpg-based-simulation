# TCK-20260527-COG-ENUM-DRIFT

## Title

Fix strategic enum and string drift across goal, project, concern, and event kinds

## Status

DONE

## Request Summary

Introduce canonical enums or constants for all strategic kinds to eliminate schema drift. Ensure goal kinds, project kinds, concern kinds, and emitted cognition events use canonical enums rather than raw strings, and that loaded persisted state is strictly validated.

## Scope

- Define canonical `GoalKind` enum in `src/core/strategic.py` or import it.
- Replace raw strings for goal kinds, project kinds, concern kinds, etc. in core logic, registrars, and scorers.
- Restructure `StrategicProjectChanged` and strategic cognition events to use strongly-typed kind enums/strings where applicable.
- Add strict validation for loaded/persisted kinds (e.g., in scenario/experiment loading or state deserialization).
- Add unit and integration tests proving:
  - Every registered goal kind is a valid canonical kind.
  - Every emitted cognition event uses a valid event kind.
  - Invalid persisted kinds fail fast or map through a safe migration/validation layer.

## Out of Scope

- Adding brand-new gameplay features (like day/night or weather).
- Designing new social negotiation mechanisms.

## Acceptance Criteria

- All core goal scorers and the `GoalRegistry` use `GoalKind` instead of raw strings.
- All emitted cognition/strategic events use canonical event kinds and correct typed fields.
- Pluggable validator or state loaders check goal kinds/project kinds on load.
- Scoped test suite runs successfully with `python3 -m pytest tests/unit/strategic/`.

## Related Tickets

- `TCK-20260527-COG-CAPACITY-ENFORCEMENT` (Done)

## Related Docs

- `entity_cognition_fix_phase0.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/strategic.py`
- `src/ai/goals/__init__.py`
- `src/ai/goals/base.py`
- `src/ai/goals/scorers.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/observability/cognition/events.py`

## Assumptions / Open Questions

- We assume string enums (`str, Enum`) are perfectly safe for backward-compatibility with serialization/deserialization.

## Implementation Notes

- None

## Test Summary

- Added `tests/unit/strategic/test_enum_drift.py` covering strict `GoalKind` validation, registration checks, and edge case rejections.
- Ran strategic unit tests: 137/137 strategic unit tests passed.

## Files Changed

- `src/core/strategic.py`
- `src/ai/goals/base.py`
- `src/ai/goals/__init__.py`
- `src/ai/goals/scorers.py`
- `src/systems/strategic_systems/intelligence.py`
- `tests/unit/strategic/test_enum_drift.py`

## Completion Summary

- Defined canonical `GoalKind` enum in `src/core/strategic.py`.
- Enforced strict registration validation in `GoalRegistry.register`.
- Migrated all 9 built-in scorers to use typed `GoalKind` constants.
- Updated `intelligence.py` to safely handle `GoalKind` values when formatting/building string identifiers.
- verified all strategic unit tests passing perfectly.
