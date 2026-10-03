---
ticket_id: TCK-20260627-P1I-WORLD-BALANCE-FIX
phase: plan
date: 2026-06-27
---

# Plan: Balance dungeon_crawl entity count and add building to wilderness_survival

## Approach

Content-only YAML changes. Two goals, minimal file touches.

## Change 1 — dungeon_crawl entity count reduction

**File:** data/content/world_compositions/dungeon_crawl.yaml

Actions:
1. Remove module_ref entry for `goblin_camp_conflict` (order: 1)
   - saves 9 entities (goblin_raiding_party)
   - also removes a module with unmet `requires: frontier_village_core` dependency
2. Remove module_ref entry for `old_mine_resource_loop` (order: 2)
   - saves 5 entities (old_mine_spider_cluster)
   - also removes a module with unmet `requires: frontier_village_core` dependency
3. Change `danger_scale` parameter in `scalable_bandit_camp` from 4 to 2
   - saves 6 entities (12 → 6 bandits: danger_scale * 3 = 6)
4. Re-number remaining module_refs orders: ruins_mystery_quest=0, scalable_bandit_camp=1

Entity result: ruins_mystery_quest(6) + scalable_bandit_camp/danger_scale=2(6) = **12** ✓

## Change 2 — wilderness_survival building addition

**New file:** data/content/world_modules/survivor_camp_shelter.yaml

Contents:
- module_id: survivor_camp_shelter
- module_type: settlement
- display_name: Survivor Camp Shelter
- buildings: { healer_hut: 1 }
- A region: survivor_outpost (wilderness, forest terrain, low hazard)
- No population (not adding entity count pressure)

**File:** data/content/world_compositions/wilderness_survival.yaml

Action: Add module_ref for `survivor_camp_shelter` (order: 3)

Building result: 1 healer_hut (healer_service, service_type: healing, heal_amount: 50) ✓
near_service check will now have a valid building to match.

## Files Changed

| File | Change type |
|---|---|
| data/content/world_compositions/dungeon_crawl.yaml | Edit — remove 2 module_refs, change 1 param |
| data/content/world_modules/survivor_camp_shelter.yaml | New — minimal settlement module |
| data/content/world_compositions/wilderness_survival.yaml | Edit — add 1 module_ref |

## Unresolved Questions

None — investigation resolved all questions:
- Building types confirmed in buildings.yaml (healer_hut is valid)
- Module types confirmed in src/worldmodules/schema.py (settlement is valid)
- Shared module constraint confirmed — new module required for wilderness_survival
- Entity count arithmetic confirmed against resolved world YAML

## Deviations

None at plan stage.
