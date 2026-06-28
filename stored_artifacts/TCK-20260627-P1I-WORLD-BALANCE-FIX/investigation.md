---
ticket_id: TCK-20260627-P1I-WORLD-BALANCE-FIX
phase: investigation
date: 2026-06-27
---

# Investigation: Balance dungeon_crawl entity count and add building to wilderness_survival

## Source Findings

D08 audit (docs/audits/D08_multi_scenario.md) F2 and F3 document two worlds that produce
near-total entity extinction before the behavioral adventure pipeline can activate (tick 201+).

## dungeon_crawl — Entity Count Breakdown

World composition: data/content/world_compositions/dungeon_crawl.yaml
Module_refs: ruins_mystery_quest, goblin_camp_conflict, old_mine_resource_loop, scalable_bandit_camp

Entity contributions per module (from data/content/entities/populations.yaml + module parameters):

| Module | Population ID | Members | Count |
|---|---|---|---|
| ruins_mystery_quest | undead_battlefield_patrol | undead_sentinel x6 | 6 |
| goblin_camp_conflict | goblin_raiding_party | scout x2, raider x4, archer x2, warlord x1 | 9 |
| old_mine_resource_loop | old_mine_spider_cluster | cave_spider x5 | 5 |
| scalable_bandit_camp (danger_scale=4) | population_recipe | scout x (4*3=12) | 12 |
| **Total** | | | **32** |

Confirmed by data/worlds/dungeon_crawl/resolved/world.resolved.yaml (entities block).

Confirmed cause of attrition: 32 entities across 4 regions with only 1 building (mine_entrance
from old_mine_resource_loop). Combat-saturated environment causes 94-97% death rate by tick 100.

### Dependency observation

goblin_camp_conflict has `requires: ["frontier_village_core"]`
old_mine_resource_loop has `requires: ["frontier_village_core"]`
dungeon_crawl does NOT include frontier_village_core.
These two modules have unmet dependencies in the dungeon_crawl composition.

### Minimal fix for dungeon_crawl (target: ≤12 entities)

Remove goblin_camp_conflict (saves 9 entities) and old_mine_resource_loop (saves 5 entities)
from dungeon_crawl.yaml, and reduce danger_scale from 4 to 2 (saves 6 entities, from 12 → 6).

Result: ruins_mystery_quest(6) + scalable_bandit_camp/danger_scale=2(6) = **12 entities** ✓

Changes: 1 file (dungeon_crawl.yaml) — remove 2 module_refs, change 1 parameter.
Also removes the 2 modules with unmet frontier_village_core dependencies.
Also removes the 1 building (mine_entrance) from dungeon_crawl — but the theme is "no
settlement / pure dungeon exploration" so that is consistent with the world description.

## wilderness_survival — Building Gap

World composition: data/content/world_compositions/wilderness_survival.yaml
Module_refs: forest_deep_ecology, wolf_den_near_forest, undead_battlefield

Building contributions: **0 buildings** (none of the 3 modules define a buildings dict).

Entity count: 5 wolves (wolf_pack_small) + 6 undead (undead_battlefield_patrol) = 11
Survival rate: 0.42–0.52 entities alive at tick 100 (near-extinction).

### Shared module constraint

wolf_den_near_forest, forest_deep_ecology, and undead_battlefield are all used by:
- frontier_extended.yaml
- swamp_border_world.yaml
- frontier_living_world.yaml
- wilderness_survival.yaml

Modifying any of these shared modules to add a building would affect all four worlds.
Therefore, a new module scoped to wilderness_survival is the correct approach.

### Fix for wilderness_survival (add ≥1 building)

Create new module: data/content/world_modules/survivor_camp_shelter.yaml
- module_type: "settlement" (valid per REGISTERED_MODULE_TYPES in src/worldmodules/schema.py)
- buildings: { healer_hut: 1 }
- healer_hut provides healer_service (service_type: "healing", heal_amount: 50)
  enabling the near_service requirement to pass

Add survivor_camp_shelter as a module_ref in wilderness_survival.yaml.

Changes: 1 new file (survivor_camp_shelter.yaml) + 1 line change in wilderness_survival.yaml.

## Available Building Types (from data/content/world/buildings.yaml)

Valid building IDs: shop, town_hall, blacksmith, inn, watchtower, healer_hut, mine_entrance,
shrine, mage_tower. All have service_profile_id → near_service compatibility.

## Parity Impact

Content-only change. No engine logic modified. No parity ledger entries affected.
No entries in substrate.yaml, world_dynamics.yaml, or infrastructure.yaml reference
dungeon_crawl or wilderness_survival entity counts or building configurations.

## Tests Available

- tests/integration/worldassembly/test_real_content_world_compositions.py
- tests/integration/worldassembly/test_real_content_world_modules.py
- make world-validate WORLD=dungeon_crawl
- make world-validate WORLD=wilderness_survival
