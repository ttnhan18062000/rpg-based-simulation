---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13B-MODULE-TYPES
phase: done
date: 2026-06-20
tags: [content, world-modules, terrain, population, phase-1]
---

# TCK-20260619-E13B-MODULE-TYPES

## Title
Epic 1.3B · New Module Types (Terrain + Population)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
D07 F2: 0 terrain modules, 0 population modules (Gap Risk 10/15). World compositions are conflict + ecology + settlement only. Adding 2 terrain and 2 population modules enables geographic variety and distinct population distributions in future compositions.

## Scope

Author 4 new world module YAML files in `data/content/world_modules/`:

### Terrain modules (2 new files)

**1. `mountain_pass.yaml`** (module_type: "terrain")
- Traversal constraint: high movement cost
- Altitude pressure: stamina drain on entities without cold-resist
- Resource nodes: iron ore deposits, ancient relics
- 1-2 quest definitions: explore_mountain_route, hunt_mountain_predator
- No faction pressure (neutral terrain)

**2. `river_crossing.yaml`** (module_type: "terrain")
- Movement cost on crossing tiles
- Resource: freshwater fish (food source — addresses hunger block)
- Connects two land regions
- 1 quest definition: survey_river_route

### Population modules (2 new files)

**3. `nomadic_herd.yaml`** (module_type: "population")
- Migration pressure: herd moves region each 50 ticks
- Faction: nomadic_tribes (or neutral herd entity)
- Resource: wolf_pelt, beast_fang, travel_ration drops
- 1 quest definition: track_nomadic_herd

**4. `settled_quarter.yaml`** (module_type: "population")
- High service density: healer_service, merchant_service, inn_service
- Faction: merchant_league or frontier_guild alignment
- Enables crafting loops (has blacksmith_service)
- 2 quest definitions: fetch_settlement_supplies, escort_settled_trader

### Module YAML format (from existing modules)
```yaml
module_id: "<id>"
module_type: "<terrain|population>"
display_name: "<display>"
description: "<description>"
version: "1.0.0"
provides: [...]
observability_tags: [...]
biomes: [...]
ecologies: [...]
regions:
  - id: "<region_id>"
    type: "wilderness|settlement"
    grid_bounds: [x1, y1, x2, y2]
    terrain: "<terrain_type>"
    hazard_level: <float>
factions: [...]
populations: [...]
quest_definitions:
  - id: "..."
    ...
```

**CRITICAL first step:** Before authoring, verify that `src/content/validator.py` or `src/worldmodules/repository.py` accepts `module_type: "terrain"` and `module_type: "population"`. If a hardcoded allowlist exists, add these two values. This is the only code change in this ticket.

## Out of Scope
- Adding these modules to existing world compositions (E13D will author scenarios that reference them if needed)
- Dynamic terrain effects (requires separate physics work)
- New biome/ecology entries unless strictly required by the module

## Acceptance Criteria
- 4 new YAML files exist and load without errors
- `python3 -c "from src.worldmodules.repository import WorldModuleRepository; r = WorldModuleRepository(); r.load_all(); print('OK')"` passes
- `make world-validate` passes (or equivalent catalog validation)
- Module type distribution: terrain ≥ 2, population ≥ 2 (from 0/0)

## Related Tickets
- TCK-20260619-E13-CONTENT-FOUNDATION (parent epic)
- TCK-20260619-E21-RESOURCE-ECOLOGY (nomadic_herd module adds depleting resource pressure)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md` (module conformance rules)
- `docs/audits/D07_content_depth.md` (update F2 count on completion)

## Related Code Areas
- `data/content/world_modules/` (4 new YAML files)
- `src/content/validator.py` OR `src/worldmodules/repository.py` (may need to add terrain/population to type allowlist)
- `src/worldmodules/schema.py` (check for module_type enum/literal)

## Assumptions / Open Questions
- Does the module schema have a hardcoded `module_type` allowlist? Check `src/worldmodules/schema.py` or `WorldModuleRepository.load_all()` — **this is the first step**.
- What biome IDs are valid? See `data/content/world/biomes.yaml` — use existing biome IDs only.
- What population IDs are valid? See `data/content/entities/populations.yaml` — use existing IDs or leave `populations: []`.

## Implementation Notes
- `terrain` and `population` were already in `REGISTERED_MODULE_TYPES` in `src/worldmodules/schema.py` — no code change required.
- Region IDs in module YAML must exist in `data/content/world/runtime_regions.yaml` (resolver validates at assembly time). Added 4 new region entries there.
- Population spawn region validation: resolver checks that ALL preferred_regions of a population exist in the module's region set. `nomadic_herd` uses `wolf_pack_small` (prefers `near_forest` + `wolf_den`), so both region IDs are included in that module.
- `settled_quarter` uses `hometown` as region ID to match `frontier_village_population`'s preferred spawn region.
- The `nomadic_herd_range` and `settled_quarter_district` catalog entries were also added to runtime_regions.yaml for forward compatibility (future modules can reference them).
- `make world-validate` passes with one pre-existing warning (sandbox_world quests section — unrelated to this ticket).

## Test Summary
```bash
python3 -c "from src.worldmodules.repository import WorldModuleRepository; r = WorldModuleRepository(); r.load_all(); print('OK')"
pytest tests/integration/worldassembly/test_e2e_smoke.py -x -v
```

## Files Changed
- `data/content/world_modules/mountain_pass.yaml` — NEW: terrain module, 2 regions (mountain_pass_zone), resources iron_vein+frost_shard_cluster, 2 quests
- `data/content/world_modules/river_crossing.yaml` — NEW: terrain module, 1 region (river_ford), resource herb_patch, building watchtower, 1 quest
- `data/content/world_modules/nomadic_herd.yaml` — NEW: population module, 2 regions (near_forest+wolf_den), population wolf_pack_small, faction wild_beast_pack, 1 quest
- `data/content/world_modules/settled_quarter.yaml` — NEW: population module, 1 region (hometown), population frontier_village_population, faction merchant_league, 4 buildings, 2 quests
- `data/content/world/runtime_regions.yaml` — UPDATED: added 4 new region entries (mountain_pass_zone, river_ford, nomadic_herd_range, settled_quarter_district)
- `tests/integration/worldassembly/test_real_content_world_modules.py` — UPDATED: added 4 new module IDs to MODULE_MATRIX
- `docs/audits/D07_content_depth.md` — UPDATED: F2 marked RESOLVED, module count 14→19, type distribution terrain/population 0→2

## Completion Summary
Authored 4 new world module YAML files (mountain_pass, river_crossing, nomadic_herd, settled_quarter) covering 2 terrain and 2 population module types. No code changes were required — the type allowlist already included terrain and population. Added 4 corresponding region entries to runtime_regions.yaml to satisfy the resolver's catalog requirement. All 32 tests pass. Module type distribution is now terrain=2, population=2 (from 0/0). D07 audit F2 marked resolved. Total world modules: 19.
