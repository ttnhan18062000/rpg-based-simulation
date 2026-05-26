# TCK-20260527-COG-GOAL-REGISTRY

## Title

Expand Goal Registry and Validate Personality Claims

## Status

DONE

## Request Summary

Expand the `GoalRegistry` with four new goal scorers (`combat_engage`, `combat_retreat`, `recover`, and `resolve_blocker`) to validate personality claims (bravery, greed, industry) and ensure deterministic tie-breaking and updated observability.

## Scope

- Create and register 4 new goal scorers in `src/ai/goals/scorers.py` and `src/ai/goals/__init__.py`:
  - `combat_engage`: Bravery/aggression biases combat intent when threats are present.
  - `combat_retreat`: Fear/panic/low HP biases retreat intent.
  - `recover`: Low HP, wounds, or low stamina biases recovery/safety behavior.
  - `resolve_blocker`: Bridges strategic blockers to detour goals.
- Implement deterministic tie-breaking in `GoalRegistry.get_all_scores` or project selection.
- Support downstream project/action generation for these new goal kinds in `fused_strategic_pass()`.
- Add comprehensive unit tests, integration tests, and personality-difference tests.
- Update observability events to trace selected goals and rejected alternatives.

## Out of Scope

- Implementing recursive multi-step planning beyond direct blocker-to-goal/detour mapping.
- Adding other new belief categories or emotion fields.

## Acceptance Criteria

- All 4 new scorers are registered and fully functional.
- High utility goals successfully translate into projects and tactical intents.
- Personality traits (bravery, greed, industry) measurably bias goal scores.
- Deterministic tie-breaking ensures no oscillation or drift.
- Observability logs both selected goal and rejected alternatives.
- The entire strategic unit test suite runs and passes.

## Related Tickets

- `TCK-20260527-COG-AUTHORITATIVE-PATH.md`

## Related Docs

- `entity_cognition_fix_phase0.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260527-COG-GOAL-REGISTRY/`

## Related Code Areas

- `src/ai/goals/scorers.py`
- `src/ai/goals/__init__.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/ai/goals/base.py`

## Assumptions / Open Questions

- We assume personality traits are in the [0.0, 1.0] range but can be any positive value.
- We assume standard target IDs and positions are available or resolved for combat/blocker tasks.

## Implementation Notes

- Designed and implemented 4 new goal scorers (`CombatEngageScorer`, `CombatRetreatScorer`, `RecoverScorer`, `ResolveBlockerScorer`) in `src/ai/goals/scorers.py`.
- Registered all 4 scorers in `src/ai/goals/__init__.py`.
- Enabled personality modification in `src/ai/personality.py` for `combat_engage`, `combat_retreat`, and `resolve_blocker`.
- Refactored `fused_strategic_pass` in `src/systems/strategic_systems/intelligence.py` to sort goal scores deterministically via `(-x.utility, x.kind)` and added debug-trace observability logging for chosen and rejected goals.

## Test Summary

- Added 7 robust unit and integration tests in `tests/unit/strategic/test_expanded_goals.py`.
- All 119 strategic unit tests are passing successfully.

## Files Changed

- `src/ai/goals/scorers.py`
- `src/ai/goals/__init__.py`
- `src/ai/personality.py`
- `src/systems/strategic_systems/intelligence.py`
- `tests/unit/strategic/test_expanded_goals.py`

## Completion Summary

- Goal Registry has been expanded successfully. Personality traits and blockers now have tangible influence over final strategic goal selection. Deterministic tie-breaking is fully enforced, and observability logging traces choices thoroughly.
