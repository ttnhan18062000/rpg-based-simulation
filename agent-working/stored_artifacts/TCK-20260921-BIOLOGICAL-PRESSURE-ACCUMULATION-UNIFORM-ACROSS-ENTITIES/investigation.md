---
status: historical
layer: simulation
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES
phase: done
date: 2026-10-07
tags: [simulation-quality, progression]
---

# Investigation — biology follows the kind's need profile

## Findings
- `apply.py` added `0.1` hunger and `0.05` sleep debt per biological tick to every entity. Need profiles (`data/content/living/need_profiles.yaml`) are qualitative (`none/low/medium/high`); species carry a `need_profile` (13 species, 6 profiles). Wolf (`carnivore_survival`) and goblin (`goblin_survival`) declare no `sleep` key.
- Compiled corpus (24 worlds, 666 subjects): without a CompileContext (the 5k test and `engine_manager`) NO subject carries `species_id` (roles CITIZEN/WORKER/GUARD/HERO only); with context (`cli/entry.py`) 615 do. Hence the person fallback (`humanoid_survival`) must work without species, and `urban_political` through the 5k test is unchanged.
- `state.building_tiles` is empty in every compiled world: `town_resolution` REST/EAT could never match. Buildings are in `state.buildings`; own tile and orthogonal neighbours (MOV-07) are the service reach. `shop.py` / `blacksmith.py` have the same dead lookup; switching them on breaks a buy (separate ticket).
- `EatScorer` targeted `tavern`, which no world has; 20 of 24 worlds have an `inn`; 4 do not (`dungeon_crawl`, `wilderness_survival`, `mechanic_scenario_combat_judgement_withdrawal`, `quest_dense_frontier`).
- `CoreActions` REST only changed `rest_pressure`.

## Measured funnel (frontier_living_world, seed 42, audit_mode; probes/)
Before (main 0647a2eeb) -> after: alive at t=1100 2 -> 6 (undead/spirits no longer hunger). crowded_frontier identical. With Lane A #404 merged in a throwaway tree: hunger projects now target the inn (85-173 active per 100 ticks) but `CoreActions.execute_survival` is never called in 1000 ticks: the current project is STABILIZE/RESOLVE_BLOCKER until hunger is ~100 (decision-side arbitration, Lane A).

## Not done here
Compiled-subject profile assignment (child 2, Lane A); shop/blacksmith (separate ticket); the rough-sleep decision (Lane A).
