---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260518-READ-MODEL-CACHE
artifact_type: investigation
tags: [read, model, cache]
---

# Investigation: Read Model and API Projection Optimization

## Background
In `src/api/engine_manager.py`, `V2EngineManager` maintains `_latest_state` and recalculates `_latest_snapshot` (the minimal world view) at the end of every tick. When API endpoints query for entity details via `get_entity(id)` or `get_entities_paged(offset, limit)`, the engine manager invokes `StatePresenter.present_entity(e)` on demand.

While generating on demand avoids building full snapshots every tick, under frequent polling or large entity counts (e.g., 1000+ entities), generating deep nested dictionary DTOs (combat stats, inventory items, strategic blockers/leads/contracts, quests, social trust history) becomes a major CPU and memory allocation bottleneck.

## Analysis of Existing Mechanism
1. `StatePresenter`:
   - `present_minimal(state)`: Fast O(1) dictionary creation.
   - `present_entity(entity)`: Deep dictionary serialization. Involves iterating over inventory items, strategic blockers, leads, contracts, projects (filtering for quests), and social trust history.
2. `V2EngineManager`:
   - `get_entities_paged`: Slices entity IDs, then maps `StatePresenter.present_entity` across the page. Slicing 100 entities results in 100 deep DTO serializations every single request, even if none of those 100 entities changed since the last tick!
   - `get_full_snapshot`: Serializes all entities and regions in the world.

## Architectural Goal (Milestone 12)
Create `ReadModelCache` and `ReadModelInvalidationPolicy`:
1. `ReadModelCache`:
   - Stores `entity_dtos: Dict[int, Dict[str, Any]]`.
   - Stores `minimal_summary: Dict[str, Any]`.
   - Caches `paged_views` or serves pages directly from cached `entity_dtos`.
2. `ReadModelInvalidationPolicy`:
   - Accepts `DirtySet`.
   - Identifies which entity IDs are dirty across any domain (`movement_entities`, `inventory_entities`, `combat_entities`, `strategic_entities`, `social_entities`, `biological_entities`, `lifecycle_entities`, `attributes_entities`).
   - Marks those entity IDs for DTO regeneration or deletes them from `entity_dtos` cache so they are regenerated on next access or immediately post-tick.
3. Integration:
   - On each kernel tick, `V2EngineManager` passes `state` and `kernel.status.dirty_set` to `ReadModelCache.update(state, dirty_set)`.
   - `ReadModelCache` updates `minimal_summary` and invalidates/updates dirty entity DTOs.
   - API lookups (`get_entity`, `get_entities_paged`) return the pre-cached dictionaries in O(1) time.
