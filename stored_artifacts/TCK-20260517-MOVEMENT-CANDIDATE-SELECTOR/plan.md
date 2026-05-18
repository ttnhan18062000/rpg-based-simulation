# Implementation Plan: MovementCandidateSelector

## Goal

Optimize spatial routing by implementing `MovementCandidateSelector` to filter entity IDs prior to movement calculation.

## Proposed Changes

### 1. `src/engine/candidate_selector.py` [NEW]
Implement `MovementCandidateSelector` with:
- `select(state, update, candidates) -> tuple[int, ...]`
- Unconditional exclusion: inactive, dead, already moved this tick, no target, already at target.
- Inclusion bypass: `force_full_scan`, target changed in update, blocked current tile, interaction/strategic requirements.
- Readiness gating: `readiness >= move_cost`.
- Cadence skipping: WANDER mode cadence `(state.tick + e_id) % 3 != 0`.
- Deterministic output ordering: `tuple(sorted(selected))`.

### 2. `src/engine/pipeline_phases/movement.py` [MODIFY]
Refactor `MovementPhase.route_movement_intent` to:
- Call `selected_ids = MovementCandidateSelector.select(state, update, state.entities.keys())`.
- Record candidate count in phase metadata.
- Perform one unified pass over `selected_ids` instead of two separate passes.

## Verification

- Unit tests in `tests/unit/optimization/test_movement_candidate_selector.py`.
- Verify full test suite compliance with `pytest tests/unit/ -m "not slow"`.
