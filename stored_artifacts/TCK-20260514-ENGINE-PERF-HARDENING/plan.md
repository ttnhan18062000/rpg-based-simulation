# Implementation Plan: V2 RPG Engine Performance Hardening (Phase 3)

Further reduce compute time and object churn by optimizing the authoritative apply pipeline, focusing on lazy dictionary creation and reuse, and improving spatial lookup efficiency.

## Proposed Changes

### Core State Logic

#### [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- **Optimize `AuthoritativeState.to_readonly`**:
    - Introduce `_readonly_entities_cache` to store the `ReadOnlyDict` of frozen entities.
    - If `self.entities` is the same object as in the previous tick (which happens for many entities in the authoritative chain), reuse the cached `ReadOnlyDict` rather than rebuilding it.
- **Add `region_id` to `NavigationComponent`**:
    - Cache the current region ID on the entity to avoid repeated O(N_regions) spatial checks every tick.

### Engine Apply Pipeline

#### [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- **Optimize `ApplyPath.apply_partial`**:
    - Defer `new_entities = dict(state.entities)` until it is certain that updates or removals need to be applied.
- **Optimize `ApplyPath.apply_passive`**:
    - Utilize the cached `region_id` from `NavigationComponent` if `moved_recently` is False.
    - Centralize region lookup to use `LegalityServiceV2.get_region_for_position`.

### Legality & Spatial Services

#### [MODIFY] [legality.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/legality.py)
- **Optimize `has_line_of_sight`**:
    - Update the Bresenham check to use the `building_tiles` spatial index for O(1) obstruction checks instead of iterating over all buildings.

## Verification Plan

### Automated Tests
- Run `scripts/profile_engine.py` for `idle`, `movement`, and `strategic` scenarios.
- Verify that `IDLE_1000` compute time is < 40ms.
- Run `pytest tests/unit/core/test_authoritative_state_contract.py` to ensure immutability is preserved.
- Run `pytest tests/unit/engine/test_engine_integrity.py`.

### Manual Verification
- Inspect the generated profile reports to confirm reduction in `dict()` and `replace()` calls.
