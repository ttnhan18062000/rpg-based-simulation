---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-PRESENT-MAP-STATIC
artifact_type: plan
tags: [api-design, world]
---

# Implementation Plan — TCK-20260821-PRESENT-MAP-STATIC

## Summary

Add two read-only `@staticmethod`s to `StatePresenter` (`src/api/presenters/state_presenter.py`):
`present_map(state)` (RLE-encoded terrain grid) and `present_static(state)` (buildings/resource
nodes/chests/regions), matching `frontend/src/types/api.ts`'s `MapData`/`StaticData` shapes.
Per investigation.md's key finding, region center/radius are derived from `RegionState.bounds`
(a real, already-populated durable field) rather than the ticket's stated `RegionRecipeSpec`
lookup — architecturally correct (presenters read state, not specs) and simpler.

## Steps

### Step 1 — `present_map(state)`

Add a helper `_terrain_code_map(state)` (module-private, not part of the public presenter surface)
that returns `{terrain_type_str: int_code}` — sorted-alphabetical distinct values of
`state.terrain.values()`, codes `0..n-1`. Pure function of `state.terrain`, deterministic, no
caching needed (cheap: one pass over the dict).

`present_map`: if `state.terrain` is empty, return `{"width": 0, "height": 0, "grid": []}`.
Otherwise: `width = max(x for x,_ in state.terrain) + 1`, `height = max(y for _,y in state.terrain) + 1`.
Build the code map. Walk `y in range(height): x in range(width)` (row-major, x fastest — matches
legacy's `_idx(x,y)=y*width+x`), looking up `state.terrain.get((x,y))` → code (default terrain code
`0` if a cell is genuinely absent — defensive only, should not happen given the dense-fill
invariant investigation.md confirmed, but cheaper than a KeyError crash for a read path). RLE-encode
with the standard value/count walk (identical algorithm to legacy's, ported directly).

### Step 2 — `present_static(state)`

One method, four sub-lists, using `_terrain_code_map(state)` computed once and threaded into the
resource-node/region terrain lookups (avoid recomputing the sort/dict-build 3 times).

- **buildings**: `[{"building_id": str(b.id), "name": b.kind.title(), "x": b.position[0], "y":
  b.position[1], "building_type": b.kind, "owner_entity_id": None} for b in state.buildings.values()]`
  — check exact attribute name for the buildings collection on `AuthoritativeState` before writing
  (likely `state.buildings`, confirm via grep, don't assume).
- **resource_nodes**: `{"node_id": n.id, "resource_type": n.kind, "name": n.kind.title(), "x":
  n.position[0], "y": n.position[1], "terrain": code_map.get(state.terrain.get(tile_of(n.position)),
  0), "yields_item": n.yields_item, "max_harvests": n.max_charges, "respawn_cooldown":
  n.respawn_cooldown, "harvest_ticks": n.required_ticks}` — `tile_of(position)` rounds/truncates the
  float position tuple to an int `(x,y)` tuple for the terrain dict lookup (positions are
  `tuple[float,float]`, terrain keys are `tuple[int,int]`).
- **treasure_chests**: `{"chest_id": c.id, "x": c.position[0], "y": c.position[1], "tier": 1,
  "looted": len(c.items) == 0, "guard_entity_id": None}`.
- **regions**: for each `region` in `state.regions.values()`: `min_x, min_y, max_x, max_y =
  region.bounds`; `center_x = (min_x + max_x) / 2`; `center_y = (min_y + max_y) / 2`; `radius =
  max(max_x - min_x, max_y - min_y) / 2`; `terrain = code_map.get(region.kind, 0)`; `{"region_id":
  region.id, "name": region.name, "terrain": terrain, "center_x": center_x, "center_y": center_y,
  "radius": radius, "difficulty": region.hazard_level, "locations": []}`.

Confirm exact collection attribute names (`state.buildings`, `state.resource_nodes`,
`state.chests`/`state.treasure_chests`) via grep on `AuthoritativeState`'s field list before
writing — do not guess from the ticket's prose alone.

### Step 3 — Tests

New file `tests/unit/api/test_state_presenter.py` (existing `tests/unit/api/` dir, 4 other files
already there for other `src/api/` modules). Cover all 8 items
investigation.md's Test Plan lists. Build a minimal synthetic `AuthoritativeState` via the same
construction pattern existing tests use (check `tests/unit/world/` or `tests/perf/
test_perf_api_snapshot.py` for the established fixture/factory pattern — reuse it, don't hand-roll a
new one if a helper already exists).

### Step 4 — Docs / Parity

None required (investigation.md confirmed no doc or parity-ledger entry references this method
surface).

## Acceptance Criteria Map

| AC | Step | Test |
|---|---|---|
| `present_map` RLE matches legacy algorithm on equivalent input | 1 | RLE round-trip test |
| `present_static` matches `StaticData` shape | 2 | shape/field tests |
| region center/radius derived from bounds midpoint/half-larger-dimension | 2 | region derivation test |
| read-only, no mutation | 1, 2 | frozen-dataclass mutation-guard test |
| chest guard / building name+owner / resource-node name each documented drop-or-derive | investigation.md | n/a (documentation AC) |
| new tests cover both methods directly | 3 | the new test file itself |

## Scope Guards

- Do not touch any REST route (`TCK-20260821-REST-MAP-STATIC-STATS`'s job, explicitly out of scope).
- Do not add interest-management/spatial filtering.
- Do not modify `RegionRecipeSpec` or any durable core-state schema — `region.bounds` already exists,
  no schema change needed.
- Do not build a terrain-type enum/registry — the deterministic sorted-string mapping is transient
  and local to each presenter call, not a stored schema addition.

## Anti-Drift Notes

- The terrain-code mapping MUST be recomputed fresh (not cached across calls) if `state.terrain`'s
  value set can change between presenter calls (it can, via world mutation) — no module-level
  memoization of `_terrain_code_map`.
- `region.kind` and `state.terrain` values are different vocabularies (ecological type vs. tile
  terrain type) — the region `terrain` field's `code_map.get(region.kind, 0)` fallback-to-0 is
  expected to miss for most regions (e.g. `kind="TOWN"` won't match any tile terrain string); this
  is a documented, accepted approximation per investigation.md, not a bug to "fix" by inventing a
  fake match.
