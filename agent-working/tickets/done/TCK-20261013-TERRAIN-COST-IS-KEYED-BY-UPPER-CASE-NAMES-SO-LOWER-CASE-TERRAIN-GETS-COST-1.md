---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1
phase: done
date: 2026-10-13
tags: []
---

# TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1

## Title
`TERRAIN_COST` is keyed by upper-case names, so lower-case terrain from content (`forest`, `swamp`, `road`, ...) misses it and costs 1.0.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
- `src/core/state.py:476` `TERRAIN_COST` has keys ROAD 0.5, PLAIN 1.0, FLOOR, GRASS, FOREST 1.5, SWAMP 3.0, HILL 2.0, MOUNTAIN 4.0, SAND 1.5.
- `src/engine/rpg_depth.py:279-280` looks up `TERRAIN_COST.get(terrain_type, 1.0)` with the raw string from `state.terrain`.
- Content terrain is lower-case (`data/content/world/terrain.yaml` ids: plain, forest, swamp, cave, mountain, ruin, road, snow, volcanic, river). The compiler's default fill is the upper-case `PLAIN`.
- So a lower-case `forest` tile costs 1.0 not 1.5, `swamp` 1.0 not 3.0, `mountain` 1.0 not 4.0, `road` 1.0 not 0.5. Only the compiler's own `PLAIN` hits its entry (and that one is 1.0 anyway).
- sandbox_world has 2292 forest and 754 swamp tiles (seed 42), so pathing and move cost in forest and swamp are cheaper than authored.


## Owner ruling D72 (2026-10-14, via rpg-designer) - SUPERSEDES the fix shape above
- Timing: BEFORE baseline v1, as its own measured step.
  - Order: metric module -> D70 -> id fix + D71 -> terrain cost -> v1.
  - Report path lengths and travel times, deaths per kind, and road use (paired protocol).
- Shape: each terrain in terrain content declares its movement cost. A terrain without one is a CONTENT ERROR at compile, never a silent 1.0.
  - TERRAIN_COST in state.py is retired. Code reads the declared value; there are no case-sensitive name keys (D56).
- Values:
  - kept: forest 1.5, swamp 3.0, mountain 4.0, road 0.5, plains/grass as today;
  - new D33 placeholders: cave 1.5, ruin 1.5, river 3.0. A river stays walkable.
- Out: movement styles per body (M1 body properties).

## Scope
- Decide the key space (case-fold the lookup, or move cost to content `terrain.yaml`), then fix the lookup.
- Measure alone, paired, after the v1 gate: move cost, path lengths, deaths, and state hashes (it changes pathing and replay hashes, so it is a rule change and needs a divergence entry and a parity row).

## Out of Scope
- The Live Map presenter's case fold (already done, presentation only).

## Acceptance Criteria
- A terrain's cost does not depend on the case of its string. A test pins forest, swamp, mountain and road costs from compiled content.
- A paired measurement is recorded.

## Related Tickets
TCK-20261011-LIVE-MAP-COLOURS-TERRAIN-BY-A-FIXED-CODE-TABLE-THE-API-DOES-NOT-USE.

## Related Docs
docs/mechanics/ (movement cost chapter); the parity ledger.

## Related Stored Artifacts
None.

## Related Code Areas
src/core/state.py; src/engine/rpg_depth.py; src/engine/legality.py (terrain_cost use at line ~190); src/worldbuilding/compiler.py (PLAIN fill); data/content/world/terrain.yaml.

## Assumptions / Open Questions
- Whether movement cost should come from content (terrain.yaml) rather than a code table.
- Any legacy parity row that assumes the current costs.

## Implementation Notes
- `TerrainDefinition.move_cost_multiplier` is required (no default); `terrain.yaml` carries the D72 values; `src/engine/terrain_cost.py` is the only reader (exact catalog id, raises on unknown); `TERRAIN_COST` in `state.py` is retired.
- `WorldCompiler` fills with the catalog id `plain` and refuses a world whose terrain holds an id the catalog does not declare. Schema and recipe defaults are `grass`; the procedural generator and the lab setup use catalog ids.
- Test worlds that used upper-case terrain ids now use catalog ids. One anchor moved (0.2316 to 0.2315): the base fill and `plain` regions are one histogram bucket now.
- Divergence 2.122, parity COMB-347, Bible ch02 section 8. The effect is only through the legality.py:190 pre-check; route choice stays unweighted and a consumer awaits a designer decision. Reported separately: the legality line-of-sight and wall checks compare raw terrain to upper-case names and never match lower-case terrain.

## Test Summary
New `tests/unit/engine/test_terrain_cost_from_content.py`; updated tests listed in the commit. Chunked non-slow run over every test directory, then re-run of each failing area: green. Paired measurement (seeds 42-46, 5000 ticks): urban_political byte-identical, frontier_living_world differs on all five seeds (see 2.122).

## Files Changed
src/content/schema.py, data/content/world/terrain.yaml, src/engine/terrain_cost.py, src/engine/rpg_depth.py, src/core/state.py, src/worldbuilding/{compiler,schema,recipe}.py, src/worldgeneration/generator.py, src/lab/workflows/generate_simulation_setup.py, docs (Bible ch02, parity COMB-347, divergence 2.122), tests.

## Completion Summary
Terrain cost is declared in content, required, and read by exact id. Measured as a behaviour change on frontier (drift, no direction), none on urban. Consumer for route choice is a separate designer decision.
