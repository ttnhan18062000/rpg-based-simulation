---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13-CONTENT-FOUNDATION
phase: done
date: 2026-06-20
tags: [content, quest-definitions, crafting-recipes, world-modules, scenarios, epic, phase-1]
---

# TCK-20260619-E13-CONTENT-FOUNDATION

## Title
Epic 1.3 · Content Foundation Layer

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
D07 audit: 430 catalog entries critically skewed — 4 quest definitions (Gap Risk 15/15), 0 terrain/population module types, 8 crafting recipes for 34 items, 8 scenarios all frontier variants. E13 closes the content gap in four batches.

## Scope
Four child tickets scoped and sequenced below. No schema extensions — existing quest/recipe/module schemas are sufficient.

## Out of Scope
- Dynamic/procedural quest generation (Epic 2.3)
- Faction quest chains (Phase 5)
- Schema extensions (quest `expiry_ticks`, `faction_association` — existing schema sufficient)

## Acceptance Criteria
- 400-tick urban_political run produces at least one `quest_started` and `quest_completed` event
- At least one crafting chain completes in a 1000-tick run
- All world compositions have at least 2 scenarios
- Quest definitions catalog reaches ≥30 entries

## Related Tickets
- TCK-20260619-E13A-QUEST-DEFS (child — quest definitions batch)
- TCK-20260619-E13B-MODULE-TYPES (child — 4 new module types)
- TCK-20260619-E13C-RECIPES (child — recipe expansion)
- TCK-20260619-E13D-SCENARIOS (child — scenario authoring)
- TCK-20260619-E21-RESOURCE-ECOLOGY (unlocked when E13 done)
- TCK-20260619-E23-QUEST-GENERATION (unlocked when E13 done)

## Related Docs
- `docs/audits/D07_content_depth.md` (gap analysis source)
- `docs/mechanics/03_economic_laws.md` (crafting reference)
- `docs/mechanics/06_worldbuilding_foundation.md` (module conformance)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E13-CONTENT-FOUNDATION/` (plan, investigation, test_plan)

## Implementation Notes
Investigation findings:
- Quest schema: `id`, `type` (escort/hunt/fetch/explore/defend/investigate), `required_participant_tags`, `required_location_tags`, `reward_budget`, `procedural_hints`, `tags` — defined by TCK-20260614-WORLDMOD-QUEST-SCHEMA (done). No extensions needed.
- Recipe schema: `id`, `outputs`, `ingredients`, `required_service`, `gold_cost` — in `data/content/world/recipes.yaml`. No extensions needed.
- Scenario schema: `id`, `world_composition`, `focus_modules`, `perspective`, `initial_conditions`.
- Module type validator must accept `terrain` and `population` — check `CatalogValidator` before authoring E13B.
- 10 modules have 0 quest_definitions; 6 of 14 are conflict modules — priority targets for E13A.

## Test Summary
- `tests/integration/scenarios/test_content_foundation.py` (new in E13C/E13D):
  - `test_quest_starts_in_urban_political()` — after E13A adds quests to urban_political modules
  - `test_crafting_chain_completes()` — after E13C adds gather→craft chain
  - `test_all_world_compositions_have_two_scenarios()` — after E13D adds scenarios

## Files Changed
- `tickets/todos/TCK-20260619-E13A-QUEST-DEFS.md` (new)
- `tickets/todos/TCK-20260619-E13B-MODULE-TYPES.md` (new)
- `tickets/todos/TCK-20260619-E13C-RECIPES.md` (new)
- `tickets/todos/TCK-20260619-E13D-SCENARIOS.md` (new)
- `staging_artifacts/TCK-20260619-E13-CONTENT-FOUNDATION/plan.md` (new)
- `staging_artifacts/TCK-20260619-E13-CONTENT-FOUNDATION/investigation.md` (new)
- `staging_artifacts/TCK-20260619-E13-CONTENT-FOUNDATION/test_plan.md` (new)

## Completion Summary
EPIC_SCOPED 2026-06-20. Investigated D07 gap analysis (4 quest defs, 0 terrain/population modules, 8 recipes for 34 items, 8 frontier-only scenarios). Confirmed no schema extensions needed. Scoped into 4 child tickets (E13A/B/C/D) with detailed acceptance criteria, sequence, and a shared test plan for 3 integration tests. E13B has a CRITICAL validator check as first step. All child tickets placed in `tickets/todos/` and ready for standard-tier implementation.
