---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDDAT-NEWMODS
phase: inprogress
date: 2026-06-14
tags: [worldmodules, data, content, new-modules]
---

# TCK-20260614-WORLDDAT-NEWMODS

## Title
New world modules demonstrating unified schema capabilities

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Create 4 new world modules in `data/content/world_modules/` to demonstrate and validate the full unified schema: ecology-first design, rich quest seeding, faction relationship networks, and parameterized entity scaling.

## Scope
- `forest_deep_ecology.yaml` — ecology type, biomes+ecologies catalog refs, explore quest
- `ruins_mystery_quest.yaml` — danger_zone type, catalog populations, investigate quests
- `trading_company_hub.yaml` — settlement type, parameterized merchant population, building, relationships
- `scalable_bandit_camp.yaml` — conflict type, danger_scale parameter, expression-based count

## Out of Scope
- Modifying existing modules
- New compositions
- Runtime behavior of quests or relationships

## Acceptance Criteria
- All 4 modules load via WorldModuleRepository without error
- scalable_bandit_camp assembles with danger_scale=4 → population count=12
- scalable_bandit_camp assembles with danger_scale=6 → AssemblyParameterError
- ruins_mystery_quest produces 2 QuestDefinition entries in compiled WorldSpec
- trading_company_hub relationship references resolve via RelationshipResolver
- forest_deep_ecology assembles without recipe fields
- All 4 modules selectable by ModuleScorer

## Related Tickets
- TCK-20260614-WORLDMOD-UNIFY (prerequisite)
- TCK-20260614-WORLDMOD-PARAMS (prerequisite)
- TCK-20260614-WORLDMOD-QUEST-MOD (prerequisite)
- TCK-20260614-WORLDDAT-MIGRATE (prerequisite)
- TCK-20260614-WORLDDAT-COMPOSE (depends on these modules)

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
- staging_artifacts/TCK-20260614-WORLDDAT-NEWMODS/

## Related Code Areas
- data/content/world_modules/ — new YAML files
- src/worldmodules/repository.py — load validation
- src/worldassembly/resolver.py — assembly validation
- tests/integration/worldassembly/test_real_content_world_modules.py
- tests/unit/worldmodules/test_parameter_evaluator.py

## Assumptions / Open Questions
- hazard_level field on RegionRecipeSpec is Optional[float] — string expressions not supported there
- population_recipes use faction/role/count/spawn_region (recipe approach) OR populations use catalog IDs
- Building recipes require building_type, count, region fields

## Implementation Notes
- All catalog IDs confirmed from catalog files before authoring
- observability_tags (not tags), provides (not provided_features)
- scalable_bandit_camp uses fixed hazard_level float; string expression only on population count

## Test Summary
- Integration: extend test_real_content_world_modules.py MODULE_MATRIX
- Unit: add scalable_bandit_camp danger_scale AC tests to test_parameter_evaluator.py

## Files Changed
- data/content/world_modules/forest_deep_ecology.yaml (new)
- data/content/world_modules/ruins_mystery_quest.yaml (new)
- data/content/world_modules/trading_company_hub.yaml (new)
- data/content/world_modules/scalable_bandit_camp.yaml (new)
- tests/integration/worldassembly/test_real_content_world_modules.py (extended)
- tests/unit/worldmodules/test_parameter_evaluator.py (extended)

## Completion Summary
Created 4 new world modules exercising the full unified schema: forest_deep_ecology (ecology-first, biomes+ecologies only, explore quest), ruins_mystery_quest (danger_zone, catalog populations, 2 investigate quests), trading_company_hub (settlement, parameterized merchant_count, building recipes, relationships), scalable_bandit_camp (conflict, danger_scale parameter, expression-based population count). Key finding: region IDs in module regions must be catalog-registered; used haunted_battlefield, hometown, bandit_road instead of invented region names. Extended integration test matrix and added 2 AC unit tests. 56/56 tests pass.
