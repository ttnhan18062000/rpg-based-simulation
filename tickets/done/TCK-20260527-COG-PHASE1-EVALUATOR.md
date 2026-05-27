# TCK-20260527-COG-PHASE1-EVALUATOR

## Title

Implement Phase 1 RequirementEvaluator Engine

## Status

DONE

## Request Summary

Implement the generic RequirementEvaluator engine that checks dynamic constraints (has_gold, has_item, knows_fact, near_service, inventory_space, target_alive, recipe_known) and translates failed requirements into structured BlockerState objects for strategic cognition.

## Scope

- Implement dataclass schemas and evaluator logic in `src/world/providers/requirements.py`.
- Support Phase 1 requirement evaluation predicates without side effects.
- Add comprehensive unit tests in `tests/unit/strategic/test_requirements.py`.

## Out of Scope

- Implementing the opportunity or information providers (Tasks 5-7).

## Acceptance Criteria

- Failed requirements return structured BlockerState components with resolutions.
- All evaluation results are deterministic and do not mutate state.
- Unit tests under `tests/unit/strategic/test_requirements.py` pass.

## Related Tickets

- None

## Related Docs

- `entity_enhance_phase1.md` (Task 4)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/world/providers/requirements.py`
- `tests/unit/strategic/test_requirements.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- None

## Test Summary

- Requirement validation unit tests pass successfully: `pytest tests/unit/strategic/test_requirements.py`.

## Files Changed

- `tickets/inprogress/TCK-20260527-COG-PHASE1-EVALUATOR.md`
- `src/world/providers/requirements.py`
- `tests/unit/strategic/test_requirements.py`

## Completion Summary

- Implemented pure evaluation engine `RequirementEvaluator` checking `has_gold`, `has_item`, `inventory_space`, `knows_fact`, `near_service`, `target_alive`, and `recipe_known`. Added resolution tags (`gather_for_gold`, `ask_information`, `harvest_resource`). Implemented unit tests test_requirements.py validating all predicates and blocker generations. All tests pass successfully!
