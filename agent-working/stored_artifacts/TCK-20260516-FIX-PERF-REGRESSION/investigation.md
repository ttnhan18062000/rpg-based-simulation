---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260516-FIX-PERF-REGRESSION
artifact_type: investigation
tags: [fix, perf, regression]
---

# Investigation: Phase 2 Performance Regressions

## Background
Commit `4daf36f` implemented Phase 2 of the engine performance hardening plan, focusing on sub-100ms apply generation cycles. While achieving performance targets, it resulted in 82 unit test regressions.

## Findings
1. **`verify_occupancy` in `src/engine/legality.py`**:
   The check `if target_grid_pos in claims:` crashes with `TypeError` when `transient_claims` on `AuthoritativeState` is `None`.
2. **`EntityState.to_readonly()` in `src/core/state.py`**:
   The method overwrote internal components (`self.identity`, `self.inventory`, etc.) on the mutable entity instance with frozen tuples/ReadOnlyDicts and returned `self` directly. This broke mutability assumptions in callers and shared references across boundaries.
3. **`ApplyPath._apply_entity_update_to_dict` in `src/engine/apply.py`**:
   During the rewrite to fuse passive and intentional updates, several fields on `EntityUpdate` were completely omitted: `lifecycle`, `biological`, `equipment`, `wound_update`, `reward`, and several `strategic` sub-collections (`contracts`, `directives`, `concerns`, `candidate_zones`, `hypotheses`, `turning_points`).
4. **Pillar 8 Derived Stats Recalculation**:
   The derived stats gate was replaced with a placeholder `speed = 5.0 + agility*0.1`, breaking all scaling from traits, gear, and wounds.
5. **Combat Corpse Generation**:
   The logic to spawn a `CorpseState` when an entity transitions from alive to dead was omitted from `apply_generation`.
