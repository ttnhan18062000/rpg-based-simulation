# Implementation Plan: Fix Phase 2 Performance Regressions

## Objective
Restore 100% unit test compliance (fixing 82 failing tests) while maintaining the sub-100ms fused apply architecture introduced in Phase 2.

## Proposed Changes

### `src/engine/legality.py`
- Update `verify_occupancy` to safeguard against `None`: `claims = getattr(state_or_context, 'transient_claims', None) or []`.

### `src/core/state.py`
- In `EntityState.to_readonly()`, remove the in-place attribute mutations (`object.__setattr__(self, "identity", id_comp)`, etc.) and the early return of `self`. Construct a new `EntityState` view and cache it on `_readonly_cache`.

### `src/engine/apply.py`
- In `ApplyPath.apply_generation`, restore corpse spawning when an entity transitions from alive to dead.
- In `ApplyPath._apply_entity_update_to_dict`, add complete handling for:
  - `update.lifecycle`
  - `update.biological`
  - `update.equipment`
  - `update.wound_update`
  - `update.reward` (leveling)
  - Missing `update.strategic` collections (`contracts`, `directives`, `concerns`, `candidate_zones`, `hypotheses`, `turning_points`, `boredom_delta`).
- Restore the robust PH8 Derived Stats Recalculation Gate using `SkillScalingService.get_effective_stats`.

## Verification Plan
- Run `pytest tests/unit` and ensure 0 failed tests.
- Verify determinism and CI checks.
