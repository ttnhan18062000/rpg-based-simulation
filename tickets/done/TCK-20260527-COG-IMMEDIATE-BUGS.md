# TCK-20260527-COG-IMMEDIATE-BUGS

## Title

Fix near-death panic threshold and TownScorer target ID strategic bridge

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement fixes for the two immediate, high-priority cognition bugs in Phase 0:
1. AppraisalSystem's near-death panic has an unreachable `< 0.1` HP percent branch because `< 0.2` is checked first.
2. TownScorer returns only `target_pos`, but the strategic intelligence intent evaluation skips all goal scores where `target_id` is None, making returning to town strategically impossible.

## Scope

- Modify `src/engine/cognition.py` to correct the near-death panic HP percent evaluation order and add a `< 0.4` intermediate panic threshold.
- Modify `src/ai/goals/scorers.py` to ensure `TownScorer` returns a canonical `target_id="town_center"`.
- Modify `src/systems/strategic_systems/intelligence.py` to support goal scores that provide either `target_id` or `target_pos` safely.
- Add regression tests verifying:
  - HP thresholds and panic progression scaling.
  - High utility town return goal successfully becomes a project and guides movement towards the town center.

## Out of Scope

- Implementing the rest of the tasks in `entity_cognition_fix_phase0.md` (e.g. authoritative brain path consolidation, enums, capacity enforcement, beliefs). Those will be handled in separate subsequent tickets.

## Acceptance Criteria

- Near-death panic levels scale correctly (panic is higher at 9% HP than at 15% HP, and higher at 15% HP than at 35% HP).
- `is_fleeing` is set to True when panic crosses the 0.4 threshold.
- `TownScorer` successfully bridges to project creation and movement to the town center works.
- Unit and regression tests added/updated and passing.

## Related Tickets

- None

## Related Docs

- [entity_cognition_fix_phase0.md](file:///home/vboxuser/Work/rpg-based-simulation/entity_cognition_fix_phase0.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/engine/cognition.py`
- `src/ai/goals/scorers.py`
- `src/systems/strategic_systems/intelligence.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Reversed HP bounds in `evaluate_emotional_state()` and added a 0.4 intermediate panic threshold.
- Aligned `TownScorer` to output a canonical `target_id="town_center"`.
- Loosened goal-scoring target check in strategic intent evaluation to allow position-only target resolution.
- Defined `candidate_ids` inside `resolve_blockers` to fix the `NameError`.
- Added full scan mode to the pipeline biological needs test to ensure it functions with high cadence and dirty set checks.

## Test Summary

- Added `tests/unit/strategic/test_cognition_immediate_fixes.py` with 2 tests verifying panic HP progression and TownScorer strategic project generation.
- Modified `tests/unit/strategic/test_biological_needs.py` to correctly test the pipeline with `force_full_scan=True` and `hunger=85.0`.
- All 110/110 unit tests in `tests/unit/strategic/` successfully passed.

## Files Changed

- `src/engine/cognition.py`
- `src/ai/goals/scorers.py`
- `src/systems/strategic_systems/intelligence.py`
- `tests/unit/strategic/test_biological_needs.py`
- `tests/unit/strategic/test_cognition_immediate_fixes.py`

## Completion Summary

- All issues successfully fixed, verified, and certified via unit/regression tests.
