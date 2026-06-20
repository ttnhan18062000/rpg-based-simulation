---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13B-MODULE-TYPES
phase: open
date: 2026-06-20
tags: [content, world-modules, terrain, population, phase-1]
---

# TCK-20260619-E13B-MODULE-TYPES

## Title
Epic 1.3B · New Module Types (Terrain + Population)

## Status
OPEN

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
- Keep module self-contained: it must be usable in any composition without additional setup.
- Use `grid_bounds` that don't overlap with typical module positions (use higher coordinates like [80, 80, 120, 120]).
- The `settled_quarter` module's healer/blacksmith services directly address the recipe activation gap (E13C).
- Run `make knowledge-index-update` after adding modules.

## Test Summary
```bash
python3 -c "from src.worldmodules.repository import WorldModuleRepository; r = WorldModuleRepository(); r.load_all(); print('OK')"
pytest tests/integration/worldassembly/test_e2e_smoke.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
