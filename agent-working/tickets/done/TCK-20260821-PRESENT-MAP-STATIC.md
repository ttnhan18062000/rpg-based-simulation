---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-PRESENT-MAP-STATIC
phase: done
date: 2026-08-21
tags: [api-design, world]
---

# TCK-20260821-PRESENT-MAP-STATIC

## Title
Add present_map and present_static StatePresenter methods

## Status
DONE

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
- [x] present_map(state) returns {width,height,grid} RLE-encoded matching src_legacy's ported logic byte-for-byte on equivalent input
- [x] present_static(state) returns buildings/resource_nodes/treasure_chests/regions matching frontend/src/types/api.ts's StaticData
- [x] region center_x/center_y derived as grid_bounds midpoint, radius as half the larger bound dimension -- not a stored-field lookup (sourced from RegionState.bounds, not RegionRecipeSpec -- see Implementation Notes)
- [x] present_map/present_static do not mutate state (read-only, matching existing StatePresenter methods)
- [x] chest guard field, building name/owner fields, and resource-node name field each have an explicit documented drop-or-derive decision (not silently omitted)
- [x] new tests cover present_map and present_static directly (no existing test targets these methods)

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

Added `present_map(state)` and `present_static(state)` as `@staticmethod`s on `StatePresenter`
(`src/api/presenters/state_presenter.py`), plus a private `_terrain_code_map(state)` helper.

**Key deviation from the ticket's stated approach (investigation.md has full detail)**: the ticket's
Scope says to derive region center/radius from `RegionRecipeSpec.grid_bounds` because "V2 has no
stored spatial region shape at all." This is incorrect — `RegionState.bounds` already exists on the
durable state (`src/core/state.py:240`) and is genuinely populated at world-compile time
(`src/worldbuilding/compiler.py:246`). Used `region.bounds` directly instead — architecturally
correct (presenters read state, not recipe/spec objects) and simpler (no spec lookup needed).
`region.name` similarly already exists and is populated; no re-sourcing decision was needed for it
either, despite the ticket's Assumptions framing it as open.

**Drop-vs-derive decisions** (all documented in investigation.md with full rationale):
- Building `name` ← `kind.title()`; `owner_entity_id` ← `None` (no ownership concept in V2 buildings).
- Resource-node `name` ← `kind.title()`; `terrain` ← the node's tile looked up in `state.terrain`,
  mapped through the same terrain-code function used for the grid.
- Chest `guard_entity_id` ← `None` (no guard concept); `tier` ← `1` (no source, least-fabricated
  default); `looted` ← `len(items) == 0`.
- Region `terrain` ← `region.kind` mapped through the terrain-code function (falls back to `0` if
  `kind` isn't a literal terrain-type string, which is the common case — `kind` is an ecological-type
  label, a different vocabulary than tile terrain strings); `difficulty` ← `region.hazard_level`;
  `locations` ← `[]` always (no location/POI concept exists in V2's durable state at all — V1 itself
  never populated this either, per the ticket's own Assumptions note).

**Terrain-type → int code**: no fixed terrain enum exists in this codebase. Used a deterministic,
computed-per-call mapping (alphabetically-sorted distinct terrain-type strings → codes `0..n-1`),
so the same terrain-type set always produces the same codes regardless of dict iteration order.
Never cached/stored — recomputed fresh on every `present_map`/`present_static` call.

**RLE encoding**: ported the exact walk algorithm from `src_legacy/api/routes/map.py` (value/count
pairs, row-major `y*width+x` order per `src_legacy/core/world/grid.py`'s `_idx`), applied over
`state.terrain`'s populated extent (width/height derived as `max(key)+1` since `AuthoritativeState`
has no stored width/height field, but `state.terrain` is populated densely over the full topology
at compile time, confirmed via `src/worldbuilding/compiler.py:200-206`).

Both methods are read-only: only `state.*` reads, no assignment to any state field.

## Test Summary

New file `tests/unit/api/test_state_presenter.py` (existing `tests/unit/api/` directory), 9 tests
covering: empty terrain, RLE round-trip correctness (manually decoded and compared), deterministic
terrain-code assignment independent of dict insertion order, width/height derivation, building
name/owner, resource-node name/terrain, chest guard/tier/looted, region center/radius/difficulty/
locations derivation, and a read-only/no-mutation guard.

Ran: `.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v`
— **31 passed** (9 new + 18 existing `tests/unit/api/` tests + the architecture read-model guard,
none of which reference `state_presenter.py` and all of which stayed green, confirming no regression
in the sibling API-layer test files).

## Files Changed
- `src/api/presenters/state_presenter.py` — added `present_map`, `present_static`,
  `_terrain_code_map`
- `tests/unit/api/test_state_presenter.py` — new, 9 tests

## Completion Summary

Implemented `StatePresenter.present_map` and `present_static` per the ticket's Scope, with one
significant, evidence-based correction to the ticket's own stated approach: region center/radius
are derived from the real, already-populated `RegionState.bounds` field rather than a
`RegionRecipeSpec` lookup, since the ticket's premise that "V2 has no stored spatial region shape"
was factually wrong (confirmed by reading `src/core/state.py` and `src/worldbuilding/compiler.py`
directly). All Scope-listed drop-vs-derive decisions (chest guard, building name/owner,
resource-node name) are made and documented, plus two additional gaps found during implementation
that the ticket's Scope didn't explicitly name (resource-node `terrain`, chest `tier`) — both
resolved and documented with the same rigor. All 9 new tests pass; the full `tests/unit/api/` +
architecture read-model guard suite (31 tests) stays green. Both methods are read-only, verified by
a dedicated mutation-guard test. No docs or parity-ledger entries required updating (investigation.md
confirmed no existing reference to this presenter's method surface anywhere in either).
