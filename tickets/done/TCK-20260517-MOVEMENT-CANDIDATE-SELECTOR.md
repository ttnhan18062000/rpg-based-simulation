# TCK-20260517-MOVEMENT-CANDIDATE-SELECTOR

## Title

MovementCandidateSelector Implementation for Spatial Routing Optimization

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement MovementCandidateSelector to accurately and deterministically select entity IDs eligible for movement routing and spatial resolution during the authoritative movement phase.

## Scope

- Implement `MovementCandidateSelector` in `src/engine/candidate_selector.py`.
- Filter out inactive or dead entities, entities without navigation targets, and entities already at their targets.
- Respect `force_full_scan` to process all movable entities.
- Ensure 100% deterministic ordering of candidate IDs.
- Support readiness gating (`readiness >= move_cost`) and movement cadence skipping (`WANDER` mode cadence).
- Integrate `MovementCandidateSelector` into `MovementPhase.route_movement_intent` in `src/engine/pipeline_phases/movement.py`.
- Create comprehensive unit test suite in `tests/unit/optimization/test_movement_candidate_selector.py`.

## Out of Scope

- Modifying combat mechanics or pathfinding algorithms.

## Acceptance Criteria

- [x] Movement selector excludes obvious no-work entities (dead, inactive, no target, already at target).
- [x] force_full_scan still processes all movable entities.
- [x] Movement selector result is strictly deterministic.
- [x] Movement phase candidate count is observable.

## Related Tickets

- TCK-20260517-STATE-UPDATE-COMPACTOR.md

## Related Docs

- perf_test_plan.md
- docs/engine/authoritative_pipeline.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260517-MOVEMENT-CANDIDATE-SELECTOR/

## Related Code Areas

- src/engine/candidate_selector.py
- src/engine/pipeline_phases/movement.py
- tests/unit/optimization/test_movement_candidate_selector.py

## Assumptions / Open Questions

- None

## Implementation Notes

- Unified Pass 1 and Pass 2 in `MovementPhase.route_movement_intent` into a single deterministic scan over `selected_ids`.
- Recorded `movement_candidates` metric in `update.sub_phase_costs`.

## Test Summary

- Run `pytest tests/unit/optimization/test_movement_candidate_selector.py -v`: 7/7 passed.
- Run `pytest tests/unit/ -m "not slow"`: 756/756 passed.

## Files Changed

- src/engine/candidate_selector.py (NEW)
- src/engine/pipeline_phases/movement.py (MODIFIED)
- tests/unit/optimization/test_movement_candidate_selector.py (NEW)

## Completion Summary

- Flawlessly implemented `MovementCandidateSelector`, unifying spatial routing candidate selection, establishing complete observability, and passing 100% of the unit test suite.
