---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT

## Title
Each terrain declares in content whether it gives cover and whether it is high ground; the code stops naming terrain (designer application of D33/D56/D72).

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
check_cover (legality.py ~498-507, COMB-262) gives cover when the tile behind the defender is one of {"WALL","FOREST","MOUNTAIN"}, and check_high_ground (~428-437) gives the attacker the edge on {"HILL","MOUNTAIN"}. Terrain is lower-case catalog ids, so neither ever fires: cover and high ground have never worked. Designer: declare both in content, missing = compile error, no names in code.

## Scope
- Add required `gives_cover: bool` and `high_ground: bool` to TerrainDefinition; a terrain missing either is a compile error.
- Values (D33 placeholders): gives_cover true for forest, mountain, ruin and cave; high_ground true for mountain only. plain, grass, road, swamp, river, snow and volcanic: neither.
- check_cover and check_high_ground read the declared flags through the same content accessor pattern as terrain_cost.py. Remove "WALL", "HILL", "FOREST" and "MOUNTAIN" from these checks.
- Check the parity ledger (COMB-262 and any high-ground row) and ch02's tactical modifiers. If they say verified/working, correct them as stale in this ticket.
- Measure alone, paired (frontier_living_world, urban_political, plus one mountain world such as highland_traverse; seeds 42-46; 5000 ticks): cover hits, high-ground hits, perception, flight and pursuit counts per world, deaths by kind. Report as drift.

## Out of Scope
- Chokepoints (its own step after this).
- The walk check (its own hash-identical ticket).
- Any change to the cover or high-ground modifier sizes.

## Acceptance Criteria
- Both flags are required in content; a missing one fails compile (test).
- Ruled values per terrain (test by catalog id).
- No terrain name literal remains in check_cover or check_high_ground.
- Divergence entry with the paired measurement and the per-world hit counts; parity rows and ch02 corrected.

## Related Tickets
- TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1 (D72, divergence 2.124: the same pattern, content-declared terrain property)
- TCK-20261014-THE-WALK-CHECK-READS-ONLY-BLOCKED-TILES (dead WALL branch)
- TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT
- TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES

## Related Docs
- docs/mechanics/02_combat_laws.md (tactical modifiers, section 8 terrain)
- docs/parity_ledger/combat_movement.yaml (COMB-262 cover)
- Designer applications of D33/D56/D72, recorded in MOV-04 after D75 (rpg-designer-m0-evidence, local)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT/

## Related Code Areas
- src/engine/legality.py (check_high_ground ~428, check_cover ~488-507)
- src/engine/pipeline_phases/movement.py:449, src/engine/candidate_selector.py:415 (_is_static_position_blocked)
- src/engine/positioning.py:64-80 (chokepoints)
- src/worldbuilding/compiler.py:638-669 (blocked_tiles from buildings)
- data/content/world/terrain.yaml, src/content/schema.py (TerrainDefinition)

## Assumptions / Open Questions
- The catalog terrain kinds are plain, forest, swamp, cave, mountain, ruin, road, snow, volcanic, river and grass. No catalog terrain is "WALL" or "HILL", so every check that names them is dead today (checked on rpg-next 56cefc2f4).

## Implementation Notes
See plan.md and divergence 2.129. Rebased onto the post-route rpg-next 05c49ac05; the ticket asked for highland_traverse as the mountain world, the standard command measures crowded_frontier instead (disclosed in 2.129).

## Test Summary
tests/unit/engine, tests/unit/combat, tests/unit/world: 1311 passed, 3 skipped. Paired run: 30 runs, no drift, identical to base; probe shows both reads reached and always false.

## Files Changed
terrain.yaml, schema.py, terrain_cost.py, legality.py, scenarios.py, tests, Bible 02, combat_movement.yaml, divergence 2.129.

## Completion Summary
Done; divergence 2.129. The change is dormant in the gate worlds (no moved run), proved by unit tests.
