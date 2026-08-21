---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-PRESENT-MAP-STATIC
phase: open
date: 2026-08-21
tags: [api-design, world]
---

# TCK-20260821-PRESENT-MAP-STATIC

## Title
Add present_map and present_static StatePresenter methods

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The live map renderer needs a map payload (terrain grid, RLE-encoded) and a static-objects payload (buildings, resource nodes, chests, ground items) that no current StatePresenter method produces, even though the underlying AuthoritativeState already carries this data live. This includes deriving spatial region data (center/radius) from RegionRecipeSpec.grid_bounds since V2 has no stored spatial region shape at all, and deciding whether to drop or re-source locations/difficulty/name fields from the ported schema.

## Scope
- Add StatePresenter.present_map(state) returning {width,height,grid} RLE-encoded terrain, ported from src_legacy's map presenter logic (git show 677abbfb^:src_legacy/api/routes/map.py, src_legacy/api/presenters/world_presenter.py)
- Add StatePresenter.present_static(state) returning buildings/resource_nodes/treasure_chests/regions matching frontend/src/types/api.ts's StaticData shape
- Derive region center_x/center_y as the RegionRecipeSpec.grid_bounds midpoint and radius as half the larger bound dimension, computed at presentation time (no stored region shape exists in V2)
- Resolve chest guard field: ChestState has no guard_id/guard-entity concept -- decide drop vs. derive, document the decision
- Resolve BuildingState missing name/owner_entity_id fields -- decide drop vs re-source, document the decision (no existing name-resolution helper)
- Resolve ResourceNodeState missing 'name' field -- same drop/re-source decision
- Both methods are read-only: no mutation of AuthoritativeState

## Out of Scope
- Wiring these methods into any REST route (that's TCK-20260821-REST-MAP-STATIC-STATS, hard-dependent)
- Building any interest-management/spatial-subscription filtering
- Modifying RegionRecipeSpec or any other durable core-state schema to add a stored region shape

## Acceptance Criteria
- [ ] present_map(state) returns {width,height,grid} RLE-encoded matching src_legacy's ported logic byte-for-byte on equivalent input
- [ ] present_static(state) returns buildings/resource_nodes/treasure_chests/regions matching frontend/src/types/api.ts's StaticData
- [ ] region center_x/center_y derived as grid_bounds midpoint, radius as half the larger bound dimension -- not a stored-field lookup
- [ ] present_map/present_static do not mutate state (read-only, matching existing StatePresenter methods)
- [ ] chest guard field, building name/owner fields, and resource-node name field each have an explicit documented drop-or-derive decision (not silently omitted)
- [ ] new tests cover present_map and present_static directly (no existing test targets these methods)

## Related Tickets
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
- docs/plans/live_map_reconnection_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/presenters/state_presenter.py
- src/core/state.py
- src/worldbuilding/recipe.py
- frontend/src/types/api.ts
- src_legacy/api/routes/map.py
- src_legacy/api/presenters/world_presenter.py
- src_legacy/api/schemas.py
- tests/perf/test_perf_api_snapshot.py
- tests/perf/test_api_projection_perf.py

## Assumptions / Open Questions
- Even V1's own to_static_data_response never actually populated regions despite RegionSchema having the full shape -- region derivation here is genuinely new logic, not a straightforward port
- Exact drop-vs-derive choice for chest guard / building name-owner / resource-node name is left to implementation-time judgment, not pre-decided by this investigation
- No "api" layer is registered in registries/layer_registry.jsonl; layer assigned as "world" (closest registered fit for map/region/static-object presentation work) rather than force-fitting "misc" -- flagged here per CLAUDE.md guidance rather than unilaterally registering a new layer during ticket formatting

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
