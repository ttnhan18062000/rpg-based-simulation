---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDDAT-NEWMODS
phase: open
date: 2026-06-14
tags: [worldmodules, data, content, new-modules]
---

# TCK-20260614-WORLDDAT-NEWMODS

## Title
New world modules demonstrating unified schema capabilities

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The existing 10 modules are all `conflict`, `settlement`, `terrain`, or `economy` types and mostly exercise recipe fields. After the unified schema is in place, new modules are needed to demonstrate and validate the full schema: ecology-first design, rich quest seeding, faction relationship networks, and parameterized entity scaling. These modules also become the test data that validates the procedural generator can select and score them correctly.

## Scope
Write 4 new modules in `data/content/world_modules/`:

1. **`forest_deep_ecology.yaml`** — type: `ecology`
   - No recipe fields; uses `biomes`, `ecologies` from catalog
   - High wilderness hazard context; no settlements
   - `provides: ["deep_wilderness", "ecology_module"]`
   - `tags: ["nature", "remote", "ecology"]`
   - `quest_definitions: [{id: forest_survey, type: explore, required_location_tags: ["wilderness"]}]`

2. **`ruins_mystery_quest.yaml`** — type: `danger_zone`
   - 1 region (ruins bounds), 1-2 hostile population recipes
   - `quest_definitions`: 2-3 entries of type `investigate`/`explore` with `procedural_hints: {difficulty: 2, escalation: false}`
   - `provides: ["dungeon", "quest_seeding"]`
   - `tags: ["ruins", "mystery", "quest"]`
   - `requires: []` — standalone

3. **`trading_company_hub.yaml`** — type: `settlement`
   - Settlement region, merchant population recipe, trading post building recipe
   - `relationships`: 2+ cross-faction relationship catalog IDs (validate they exist in catalog first)
   - `provides: ["trade_hub", "settlement", "trade_route"]`
   - `tags: ["trade", "urban", "economy"]`
   - `parameters: [{name: merchant_count, type: integer, default: 3, min_value: 1, max_value: 8}]`
   - Population recipe count references `"{merchant_count}"`

4. **`scalable_bandit_camp.yaml`** — type: `conflict`
   - 1 wilderness region, bandit/outlaw population recipe
   - `parameters: [{name: danger_scale, type: integer, default: 2, min_value: 1, max_value: 5, description: "Scales bandit count and hazard level"}]`
   - Population recipe: `count: "{danger_scale} * 3"`
   - Hazard level in region: `"{danger_scale} * 0.3"` (float expression)
   - `provides: ["conflict", "faction_pressure"]`
   - `tags: ["hostile", "conflict", "danger_zone", "scalable"]`

Each module must include `module_id`, `module_type`, `display_name`, `description`, `version: "1.0.0"`, `tags`, `provides`.

## Out of Scope
- Modifying existing modules (TCK-20260614-WORLDDAT-MIGRATE)
- New compositions (TCK-20260614-WORLDDAT-COMPOSE)
- Runtime behavior of quests or relationships

## Acceptance Criteria
- All 4 modules load via `WorldModuleRepository` without error
- `scalable_bandit_camp` assembles with `danger_scale=4` and produces a population with count=12
- `scalable_bandit_camp` assembles with `danger_scale=6` raises `AssemblyParameterError` (exceeds max_value=5)
- `ruins_mystery_quest` produces 2-3 `QuestDefinition` entries in compiled `WorldSpec.quest_definitions`
- `trading_company_hub` relationship references resolve via `RelationshipResolver` (or relationship IDs are confirmed in catalog before authoring)
- `forest_deep_ecology` assembles without recipe fields and produces non-empty ecology context in `CompileContext`
- All 4 modules are selectable by `ModuleScorer` based on their type and tags

## Related Tickets
- TCK-20260614-WORLDMOD-UNIFY (prerequisite)
- TCK-20260614-WORLDMOD-PARAMS (prerequisite — scalable_bandit_camp uses param expressions)
- TCK-20260614-WORLDMOD-QUEST-MOD (prerequisite — ruins_mystery_quest uses quest_definitions)
- TCK-20260614-WORLDDAT-MIGRATE (prerequisite — confirm catalog IDs available)
- TCK-20260614-WORLDDAT-COMPOSE (depends on these modules)

## Related Code Areas
- `data/content/world_modules/` — new YAML files
- `src/worldmodules/repository.py` — load validation
- `src/worldassembly/resolver.py` — assembly validation

## Test Summary
- Integration: extend `tests/integration/worldassembly/test_real_content_world_modules.py` to load all 4 new modules
- Unit: `scalable_bandit_camp` parameter test in `test_parameter_evaluator.py` (extends TCK-20260614-WORLDMOD-PARAMS tests)

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
