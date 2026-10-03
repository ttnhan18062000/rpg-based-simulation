---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-PRESENT-MAP-STATIC
artifact_type: investigation
tags: [api-design, world]
---

# Investigation — TCK-20260821-PRESENT-MAP-STATIC

## Search-Before-Grep Compliance

`mcp__knowledge-search__search_docs` and `graphify query` were attempted first for this ticket's
topic ("StatePresenter present_map present_static RLE terrain grid region bounds"). Both are
unavailable in this worktree (same as the two prior tickets this session: `search_docs` → "index
not found"; `graphify query` → no `graphify-out/graph.json` in this worktree). Fell through to
direct reads per the documented fallback.

## Key finding: the ticket's core premise is wrong — a real stored region shape already exists

The ticket's Scope and Assumptions repeatedly state "V2 has no stored spatial region shape at all"
and instructs deriving center/radius from `RegionRecipeSpec.grid_bounds` (a config/recipe object,
not durable state). This is factually incorrect: `RegionState` (`src/core/state.py:236-259`) already
has a `bounds: tuple[int, int, int, int]` field (`x_min, y_min, x_max, y_max`), and it is genuinely
populated at world-compile time from real values, not left as a dead/zero field — confirmed at
`src/worldbuilding/compiler.py:243-252`:
```
regions[r_spec.id] = RegionState(
    id=r_spec.id, name=r_spec.id.replace("_", " ").title(),
    bounds=(r_spec.bounds[0], r_spec.bounds[1], r_spec.bounds[2], r_spec.bounds[3]),
    kind=r_spec.type.upper(), ...
)
```
`RegionState.name` also already exists and is populated (title-cased region id) — the ticket's
Assumptions ask about a "name" re-source decision for regions, but no decision is needed there;
`region.name` is already the right, already-populated source.

**Architecture implication**: presenters must read authoritative state, not recipe/spec objects
(`docs/core/state.md`'s durable-state boundary). `region.bounds` is exactly the correct source —
reading `RegionRecipeSpec.grid_bounds` instead (as the ticket describes) would mean looking up a
config object at presentation time, which is both architecturally wrong (presenters read `state`,
not specs) and unnecessary, since the real durable equivalent already sits on the entity being
presented. This is a legitimate deviation from the ticket's stated approach, not a shortcut — same
derivation formula (grid_bounds midpoint / half the larger dimension), different (correct) source.

## Terrain grid — width/height and RLE encoding

`AuthoritativeState` has no direct `width`/`height` field. `state.terrain: Dict[tuple[int,int], str]`
(`src/core/state.py:1126`) is populated *densely* over the full world topology at compile time
(`src/worldbuilding/compiler.py:200-206`: every `(x, y)` in `range(width) × range(height)` gets a
`"PLAIN"` default before per-region painting overwrites it) — so despite the dict type, every cell
in the real world extent has an entry. Width/height can therefore be safely derived as
`max(x for x,_ in terrain) + 1` / `max(y for _,y in terrain) + 1` — the populated extent *is* the
real width/height, not an approximation.

Legacy's RLE source (`git show 677abbfb^:src_legacy/api/routes/map.py`): flattens `grid._tiles` in
index order `_idx(x,y) = y*width + x` (`src_legacy/core/world/grid.py:65-66`, i.e. **row-major, x
fastest**) and walks it once, emitting `[value, count]` pairs on each value change. Ported this exact
walk algorithm — same mechanics, same "byte-for-byte on equivalent input" AC — over V2's terrain
dict instead of a dense array, at the same `y*width+x` traversal order.

**Terrain type → int code**: legacy's `_tiles` already stored int-coded material values (`Material`
enum). V2's `terrain` dict stores free-form strings ("PLAIN", "GRASS", "WALL" per the field's own
comment, or whatever a recipe's `terrain`/`terrain_variants` declares) — there is no terrain-type
enum or fixed int-code table anywhere in this codebase (confirmed: no `TerrainType`/`Material` class
under `src/worldbuilding/` or `src/core/`). A codebase-wide fixed enum is out of this ticket's scope
("no other durable core-state schema" changes). Chose a **deterministic, computed-per-call mapping**:
sort the distinct terrain-type strings actually present in `state.terrain.values()` alphabetically,
assign codes `0, 1, 2, ...` in that sorted order. This is fully deterministic given identical terrain
content (same set of terrain-type strings always produces the same codes, independent of dict
iteration order), requires no schema/registry change, and is computed transiently (never stored —
satisfies the read-only constraint). The same mapping function is reused for `ResourceNode.terrain`
(see below) so a given terrain-type string always maps to the same code within one presenter call.

## Buildings / resource nodes / chests — drop-vs-derive decisions

Read the actual state classes (`src/core/state.py:908-1046`) against `frontend/src/types/api.ts`'s
`Building`/`ResourceNode`/`TreasureChest` interfaces (lines 225-297):

- **`BuildingState`** has `id, kind, position, hp, max_hp, functional, inventory,
  price_modifiers` — confirmed no `name`, no `owner_entity_id`, and (confirmed via grep) no
  name-resolution helper exists anywhere. **Decision: derive `name` from `kind`** (title-cased,
  e.g. `"BLACKSMITH"` → `"Blacksmith"`), matching the exact precedent already used for region names
  in `compiler.py:245`. **Decision: drop `owner_entity_id`** (return `None`) — V2 buildings have no
  ownership concept at all, matching the frontend's `owner_entity_id?: number | null` optional type.
- **`ResourceNodeState`** has `id, kind, position, yields_item, remaining_charges, max_charges,
  required_ticks, respawn_cooldown, cooldown_remaining, regen_rate_per_tick` — confirmed no `name`.
  **Decision: derive `name` from `kind`**, same title-case approach as buildings, for consistency.
  **`terrain` field** (required by `ResourceNode`, not previously flagged in the ticket's own
  Scope): no direct source exists on `ResourceNodeState` either — **derived by looking up the node's
  own `position` in `state.terrain` and mapping through the same terrain-code function used for
  `present_map`'s grid**, so a resource node's reported terrain code is always consistent with what
  `present_map` would show for that tile.
- **`ChestState`** has `id, position, items, respawn_tick, cooldown_remaining` — confirmed no
  `guard_entity_id`/guard-entity concept at all (matches ticket's own note). **Decision: drop**
  (`None`), matching the frontend's `guard_entity_id?: number | null` optional type.
  **`tier` field** (required, non-optional, by `TreasureChest` — not previously flagged in the
  ticket's own Scope, same gap class as resource-node `terrain`): no source exists on `ChestState`
  at all. **Decision: default to `1`** for every chest — the least-fabricated choice that keeps the
  shape valid without inventing fake per-chest differentiation from nothing. **`looted` field**
  (optional): **derived as `len(items) == 0`** — an emptied chest is the closest real-state proxy
  for "looted" that exists.

## Regions — remaining fields

`Region` (frontend) needs `region_id, name, terrain, center_x, center_y, radius, difficulty,
locations` beyond the already-covered center/radius derivation:
- `region_id` ← `region.id`, `name` ← `region.name` (both already real, populated fields — no
  decision needed, contra the ticket's Assumptions framing).
- `terrain` (int) ← `region.kind` mapped through the same terrain-code function as the grid, if
  `region.kind` matches a terrain-type string actually present in `state.terrain.values()`;
  **falls back to `0`** if not (region `kind` values like `"FOREST"`/`"TOWN"` are ecological-type
  labels from `RegionRecipeSpec.type`, not guaranteed to be literal terrain-type strings — grep
  confirms `region.kind = r_spec.type.upper()`, a different vocabulary than `r_spec.terrain`).
- `difficulty` (not flagged in the ticket's own Scope, same "found while implementing" gap class as
  chest `tier`/resource-node `terrain`) ← **`region.hazard_level`** directly (0.0-1.0 range on both
  sides conceptually; hazard is the closest existing durable signal for gameplay difficulty).
- `locations` ← **`[]`** always. No location/POI concept exists anywhere in V2's durable state
  (confirmed: no `LocationState` class in `src/core/state.py`). The ticket's own Assumptions section
  already flags that "even V1's own `to_static_data_response` never actually populated regions
  despite `RegionSchema` having the full shape" — i.e. this was already an unpopulated gap in V1,
  not a V2 regression. Dropping to empty list is consistent with that precedent, not a new gap.

## Mechanics / Engine Constraints

None. This is a pure API-presentation-layer change (`src/api/presenters/state_presenter.py`) — no
`docs/mechanics/` law or `docs/engine/` contract governs how state gets shaped for API consumption;
`docs/core/state.md`'s durable-state/read-model boundary is the relevant architecture doc (presenters
read state, never mutate it) and is respected: both new methods are `@staticmethod`s that only read
`state.*`, with no assignment to any state field.

## Docs Requiring Update

None. No `docs/` file describes `StatePresenter`'s method surface at this level of detail (checked
`docs/core/state.md`, `docs/architecture/`, `docs/guides/` — no hits for `present_map`,
`present_static`, or an enumerated list of `StatePresenter` methods). `docs/plans/
live_map_reconnection_epic.md` describes the target end-state at a design-doc level and doesn't need
per-ticket updates as each child ticket lands (confirmed by reading it: it's a roadmap doc, not a
living API reference).

## Parity Ledger Overlap

Grepped `docs/parity_ledger/` for `StatePresenter`, `present_map`, `present_static`,
`state_presenter.py` — no hits in any subsystem file. No existing entry governs this presenter's
method surface; nothing to update at Parity phase, and no P0 entry is affected.

## Test Plan

See `staging_artifacts/TCK-20260821-PRESENT-MAP-STATIC/test_plan.md` for the full required-coverage
list and scoped pytest command. Summary: no existing test targeted `present_map`/`present_static`
before this ticket; new coverage lands in `tests/unit/api/test_state_presenter.py` (existing
`tests/unit/api/` directory).
