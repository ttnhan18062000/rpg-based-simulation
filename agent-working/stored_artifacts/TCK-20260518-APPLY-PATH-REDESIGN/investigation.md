---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260518-APPLY-PATH-REDESIGN
artifact_type: investigation
tags: [apply, path, redesign]
---

# Investigation - ApplyPath Execution Analysis

## Current Flow
1. `AuthoritativeApplyPipeline.refine` runs 17 phases on `StateUpdate`.
2. It calls `StateUpdateCompactor.compact` at the beginning.
3. The refined `StateUpdate` is passed to `ApplyPath.apply_generation`.
4. In `ApplyPath.apply_generation`:
   - Non-entity world updates (groups, regions, nodes, chests, buildings, corpses, storage, scars, camps) are processed by copying dictionaries and modifying items.
   - For entities: it loops over `prior_state.entities.items()`.
   - If passive=True and entity is active/due for passive decay, it computes passive biological/lifecycle/stamina changes.
   - It retrieves `update.entity_updates.get(e_id)`. If present, it calls `_apply_entity_update_to_dict`, which executes 18 separate `if update.X is not None` blocks to populate the `changes` dictionary.
   - It performs derived stat recalculations if any combat/attribute/equipment/wound stats were touched.
   - If `changes` is non-empty, it reconstructs the entity via `_fast_replace_entity`.

## Opportunity
By prebuilding an `ApplyPlan`, we can pre-group entity updates into exact component change dictionaries before the entity loop in `ApplyPath`.
Furthermore, `ApplyPlanBuilder` can pre-determine cache invalidation hints (like `world_indexes`, `movement_cache`, `read_model_cache`) and list exactly which entities require intentional updates, ensuring `ApplyPath` does no wasted branching.
