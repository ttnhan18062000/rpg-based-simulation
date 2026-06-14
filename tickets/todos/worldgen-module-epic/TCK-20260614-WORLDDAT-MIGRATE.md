---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDDAT-MIGRATE
phase: open
date: 2026-06-14
tags: [worldmodules, data, migration, yaml]
---

# TCK-20260614-WORLDDAT-MIGRATE

## Title
Migrate existing 10 world modules to unified schema with enriched fields

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
After the unified `WorldModuleSpec` schema is in place (TCK-20260614-WORLDMOD-UNIFY), all 10 existing modules in `data/content/world_modules/` still use `schema_version: "worldmodule.v1"` and only populate recipe fields. This ticket migrates their YAML and enriches selected modules with ecology, biome, relationship, and quest fields appropriate to their domain — making the unified schema non-trivially exercised by real data.

## Scope
- Remove `schema_version:` field from all 10 module YAML files (or update to the canonical single value if kept)
- Add appropriate ecology/biome/relationship/quest fields to at least 4 modules:
  - `frontier_village_core.yaml` — add `relationships: ["merchant_league_to_town_council"]` (if catalog has this); add `provided_features: ["settlement", "trade"]`
  - `goblin_camp_conflict.yaml` — ensure `relationships: ["town_to_goblin_warband", "goblin_warband_to_town"]` are wired to catalog; add `provided_features: ["conflict", "faction_pressure"]`
  - `old_mine_resource_loop.yaml` — add a `quest_definitions` entry of type `fetch` seeding an ore retrieval quest
  - `wolf_den_near_forest.yaml` — add `biomes: ["forest_edge"]` or equivalent catalog biome ID if it exists; add `provided_features: ["ecology", "wilderness"]`
- Verify all 10 modules still load via `WorldModuleRepository` after migration
- Do NOT change game-logic values (hazard levels, entity counts) — data migration only

## Out of Scope
- Adding entirely new modules (TCK-20260614-WORLDDAT-NEWMODS)
- New compositions (TCK-20260614-WORLDDAT-COMPOSE)
- Any code changes — YAML only, except to fix loading if the schema change requires it

## Acceptance Criteria
- All 10 modules in `data/content/world_modules/` load from `WorldModuleRepository` without error after migration
- At least 4 modules have non-empty `relationships`, `biomes`, or `ecology` fields
- At least 1 module has a `quest_definitions` entry
- `make lane-worldassembly` and `make lane-strict-matrix` pass
- `frontier_living_world.yaml` composition assembles correctly after module migration

## Related Tickets
- TCK-20260614-WORLDMOD-UNIFY (prerequisite — schema must be unified first)
- TCK-20260614-WORLDMOD-QUEST-MOD (prerequisite for quest_definitions field)
- TCK-20260614-WORLDDAT-NEWMODS (follows this)

## Related Code Areas
- `data/content/world_modules/*.yaml` — all 10 files
- `src/worldmodules/repository.py` — WorldModuleRepository (validation on load)
- `tests/integration/worldassembly/test_real_content_world_modules.py`

## Assumptions / Open Questions
- Catalog must have relationship IDs like `merchant_league_to_town_council` for modules to reference them — check catalog YAML before adding relationship refs. If absent, use only IDs already present in catalog.
- Biome IDs referenced by modules must exist in `data/content/*.yaml` catalog families

## Test Summary
- Existing: `tests/integration/worldassembly/test_real_content_world_modules.py` — must pass unchanged
- Existing: `tests/integration/content/test_strict_world_matrix.py` — must pass

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
