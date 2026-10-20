---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261014-REGIONS-STOP-TOPPING-UP-MONSTERS-TO-A-DENSITY-TARGET-D67-D70
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-REGIONS-STOP-TOPPING-UP-MONSTERS-TO-A-DENSITY-TARGET-D67-D70

## Title
Regions stop topping up monsters to a density target (SpawnService.process_spawns). Nothing comes from nothing, and the world isn't set by a target (D67/D70, designer application, 2026-10-14).

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`SpawnService.process_spawns` (spawn.py) is live, with no flag. Every 50 ticks it tops each region's monster count up to area x BASE_MONSTER_DENSITY x (1 + hazard), with a minimum of 2. It adds 1 per interval, then 2 after tick 500, from SPAWN_POOLS by region kind. The adds have no parent and no cost: the "topping up by spawning to a target" that D67 rejected.

## Scope
1. FIRST, report only: count its adds per world and per kind in the current baseline arms, for frontier_living_world and urban_political, seeds 42-46, 5000 ticks. If its pools never match the compiled region kinds, it is a no-op and rides with D70. Report it to rpg-planner before building.
2. Otherwise remove it. Measure it alone with the paired protocol against the main containing D70:
   - deaths and alive per kind;
   - region monster counts over time.
3. Docs: a divergence, the parity entry and a Bible 05 note.
4. Tests:
   - no region add without a source;
   - determinism.

## Out of Scope
- Camps (D70).
- M1 births.
- The V8 row (testing) and the SpawnSource tag (the metrics ticket).

## Acceptance Criteria
- The density top-up no longer runs.
- The measurement is disclosed.
- The population decline is reported, not graded.

## Related Tickets
TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70; the RPG gate metrics ticket (V8 SpawnSource).

## Related Docs
docs/mechanics/05_world_evolution.md; designer memo row 70; ECOL-03.

## Related Stored Artifacts
None.

## Related Code Areas
src/world/spawn.py (or its actual path); world_dynamics.py:260.

## Assumptions / Open Questions
Step 1 (report only), measured 2026-10-13: frontier_living_world and urban_political, seeds 42-46, 5000 ticks, pinned NORMAL, audit_mode: process_spawns was called on all 50 interval ticks of each of the 10 runs and added 0 entities per kind and in total. SPAWN_POOLS is keyed FOREST, PLAINS and MOUNTAIN and none of the 24 corpus worlds has a region of those kinds (TOWN, WILDERNESS, ROAD, SETTLEMENT), so it is a no-op. rpg-planner ruled: remove it anyway, no paired measurement (the 0-add evidence is the measurement). spawn_tables.yaml content is left alone; nothing in code reads it.

## Implementation Notes
Deleted src/world/spawn.py (SpawnService) and tests/unit/world/test_spawn_cadence.py; removed SPAWN_POOLS, BASE_MONSTER_DENSITY, SpawnConfig and DEFAULT_SPAWN_CONFIG from spawn_config.py (DIFFICULTY_TIERS and DIFFICULTY_ZONES stay, they are read); removed the call and the entities_add term in world_dynamics.py; retired the regional_monster_spawn mechanism and re-bound EntityGenerator to camp; the event extractor keeps its own 50-tick cadence. Divergence 2.122, parity WORLD-103 marked divergent.

## Test Summary
tests/unit/world/test_no_region_sourced_entity_adds.py (16): a monster-less region of each old pool kind and of WILDERNESS and TOWN adds nothing at ticks 0, 50 and 600, and the service and pool constants are gone (the tests fail on the old code). tests/unit/core/test_engine_integrity.py adapted. tests/unit/tools (mechanism pins and atlas list) and tests/unit/world pass.

## Files Changed
src/world/spawn.py (deleted); src/world/spawn_config.py; src/engine/world_dynamics.py; src/observability/event_extractor.py (comment); registries/mechanisms.yaml; docs/guidelines/intentional_divergences.md; docs/parity_ledger/world_dynamics.yaml; docs/brainstorm/mechanism_verification_view.md; tests as above.

## Completion Summary
Done: the density top-up is removed so it cannot wake under a world that declares those region kinds.
