---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260614-WORLDDAT-NEWMODS
artifact_type: plan
tags: [worldmodules, data, content, new-modules]
---

# Plan — TCK-20260614-WORLDDAT-NEWMODS

## Objective
Create 4 new YAML world modules that exercise the full unified schema: ecology-first design, quest seeding, parameterized scaling, and faction relationship networks.

## Files to Create

### data/content/world_modules/forest_deep_ecology.yaml
- type: ecology
- No recipe fields — biomes+ecologies catalog refs only
- One explore quest

### data/content/world_modules/ruins_mystery_quest.yaml
- type: danger_zone
- Catalog populations (undead), ruins biome
- 2 investigate quests

### data/content/world_modules/trading_company_hub.yaml
- type: settlement
- population_recipes with `count: "{merchant_count}"`
- building_recipes for trading post
- relationships catalog refs

### data/content/world_modules/scalable_bandit_camp.yaml
- type: conflict
- parameters: danger_scale (integer, 1–5)
- population_recipes with `count: "{danger_scale} * 3"`
- hazard_level: fixed float (NOT string expression — schema is Optional[float])

## Files to Modify
- tests/integration/worldassembly/test_real_content_world_modules.py — add 4 new modules to MODULE_MATRIX
- tests/unit/worldmodules/test_parameter_evaluator.py — add scalable_bandit_camp AC tests

## Constraints
- WorldModuleSpec has extra="forbid"; use only confirmed field names
- observability_tags (NOT tags), provides (NOT provided_features)
- hazard_level on regions is float only
- String expressions only valid for count fields
- All catalog IDs confirmed in investigation.md
