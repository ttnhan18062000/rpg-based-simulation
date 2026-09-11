---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDDAT-COMPOSE
phase: done
date: 2026-06-14
tags: [worldmodules, data, compositions, archetypes]
---

# TCK-20260614-WORLDDAT-COMPOSE

## Title
New world archetype compositions demonstrating distinct play patterns

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Create 3 new world composition YAMLs (`wilderness_survival`, `urban_political`, `dungeon_crawl`) demonstrating distinct play archetypes using new modules from TCK-20260614-WORLDDAT-NEWMODS. Add integration tests for each composition covering load + assemble + compile pipeline.

## Scope
- `data/content/world_compositions/wilderness_survival.yaml`
- `data/content/world_compositions/urban_political.yaml`
- `data/content/world_compositions/dungeon_crawl.yaml`
- Extend `tests/integration/worldassembly/test_real_content_world_compositions.py`

## Out of Scope
- Runtime simulation tuning
- Scenario definitions referencing these compositions
- 10-tick simulation smoke tests (TCK-20260614-WORLDGEN-E2E-SMOKE)

## Acceptance Criteria
- All 3 compositions load as valid `WorldCompositionSpec`
- All 3 assemble via `WorldAssemblyResolver.assemble()` to a valid `ResolvedWorldBundle`
- All 3 compile via `WorldCompiler.compile()` to a valid `AuthoritativeState`
- `dungeon_crawl` compiled world has at least 2 `QuestDefinition` entries in `world_spec.quest_definitions`
- `urban_political` compiled world has at least 2 resolved faction relationships in `CompileContext.factions`

## Related Tickets
- TCK-20260614-WORLDDAT-NEWMODS (prerequisite — new modules must exist)
- TCK-20260614-WORLDMOD-PARAMS (prerequisite — parametric module refs)
- TCK-20260614-WORLDSCEN-PERSPECTIVES (follows)
- TCK-20260614-WORLDGEN-E2E-SMOKE (follows)

## Related Docs
- `docs/architecture/world_repository_layout.md`
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260614-WORLDDAT-COMPOSE/`

## Related Code Areas
- `data/content/world_compositions/`
- `src/worldassembly/schema.py`
- `src/worldassembly/resolver.py`
- `tests/integration/worldassembly/test_real_content_world_compositions.py`

## Assumptions / Open Questions
- `urban_political` uses `namespace: "trading"` on `trading_company_hub` to avoid `hometown` region collision with `frontier_village_core`
- `dungeon_crawl` omits `undead_battlefield` to avoid `haunted_battlefield` region collision with `ruins_mystery_quest`
- Quest assertions use `bundle.world_spec.quest_definitions` (not AuthoritativeState which does not carry quest_definitions)
- Faction assertion uses `bundle.compile_context.factions` (all catalog factions are registered)

## Implementation Notes
See staging_artifacts/TCK-20260614-WORLDDAT-COMPOSE/investigation.md for full analysis.

## Test Summary
See staging_artifacts/TCK-20260614-WORLDDAT-COMPOSE/test_plan.md

## Files Changed
- `data/content/world_compositions/wilderness_survival.yaml` (new)
- `data/content/world_compositions/urban_political.yaml` (new)
- `data/content/world_compositions/dungeon_crawl.yaml` (new)
- `tests/integration/worldassembly/test_real_content_world_compositions.py` (extended)

## Completion Summary
Created 3 new world composition YAMLs (wilderness_survival, urban_political, dungeon_crawl) using module_refs structured form with parameter injection. Fixed WorldAssemblyValidator to use module default parameters when evaluating template fields during validation (was passing empty dict, causing AssemblyParameterError for parametric modules). Added 3 integration tests covering load + assemble + compile pipeline. All 13 tests in test_real_content_world_compositions.py pass; 38/38 worldassembly integration tests pass. Pre-existing strict matrix failures (15) unaffected.
