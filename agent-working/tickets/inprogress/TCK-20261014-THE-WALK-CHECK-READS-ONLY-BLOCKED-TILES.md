---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261014-THE-WALK-CHECK-READS-ONLY-BLOCKED-TILES
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-THE-WALK-CHECK-READS-ONLY-BLOCKED-TILES

## Title
The walk check reads only blocked_tiles; the dead WALL terrain branch is removed (hash-identical).

## Status
INPROGRESS

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
`_is_static_position_blocked` (pipeline_phases/movement.py:449 and candidate_selector.py:415) blocks a tile whose terrain == "WALL" or that is in `state.blocked_tiles`. No catalog terrain is "WALL", so the first branch never fires; buildings register their tiles in blocked_tiles at compile time, which is the real blocker. Designer (D56 application): drop the dead branch, read only blocked_tiles.

## Scope
- Remove the "WALL" terrain branch from both _is_static_position_blocked copies (and fold the two copies into one if they are identical).
- Prove it hash-identical: paired runs, frontier_living_world and urban_political, seeds 42-46, 5000 ticks, byte-identical state hashes. If any differs, stop and report.

## Out of Scope
- Chokepoints (positioning.py), its own measured step.
- Cover and high ground, their own measured step.
- Rendering's WALL colour and connectivity check (presentation, separate cleanup).

## Acceptance Criteria
- No code under src/engine reads a "WALL" terrain name for walking.
- A test: a tile in blocked_tiles is refused, and a tile with any catalog terrain not in blocked_tiles is not.
- The paired runs are byte-identical, and that result is recorded in the ticket. No divergence entry is needed if they are identical; otherwise stop.

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
- none yet

## Related Code Areas
- src/engine/legality.py (check_high_ground ~428, check_cover ~488-507)
- src/engine/pipeline_phases/movement.py:449, src/engine/candidate_selector.py:415 (_is_static_position_blocked)
- src/engine/positioning.py:64-80 (chokepoints)
- src/worldbuilding/compiler.py:638-669 (blocked_tiles from buildings)
- data/content/world/terrain.yaml, src/content/schema.py (TerrainDefinition)

## Assumptions / Open Questions
- The catalog terrain kinds are plain, forest, swamp, cave, mountain, ruin, road, snow, volcanic, river and grass. No catalog terrain is "WALL" or "HILL", so every check that names them is dead today (checked on rpg-next 56cefc2f4).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
