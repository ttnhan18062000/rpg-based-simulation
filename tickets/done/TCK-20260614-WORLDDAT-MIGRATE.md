---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDDAT-MIGRATE
phase: done
date: 2026-06-14
tags: [worldmodules, data, migration, yaml]
---

# TCK-20260614-WORLDDAT-MIGRATE

## Title
Migrate existing 10 world modules to unified schema with enriched fields

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
After the unified `WorldModuleSpec` schema is in place (TCK-20260614-WORLDMOD-UNIFY), all 10 existing modules in `data/content/world_modules/` still use `schema_version: "worldmodule.v1"` and only populate recipe fields. This ticket migrates their YAML and enriches selected modules with ecology, relationship, and quest fields appropriate to their domain — making the unified schema non-trivially exercised by real data.

## Scope
- Remove `schema_version:` field from all 10 module YAML files
- Add `observability_tags` (the correct audit tag field — NOT `provided_features` which does not exist in schema)
- Add `relationships` to `frontier_village_core` using catalog-verified IDs `town_to_merchants`, `merchants_to_town`
- Add `quest_definitions` (fetch type) to `old_mine_resource_loop`
- Add `relationships: ["dwarves_to_goblins"]` to `old_mine_resource_loop`
- Enrich `observability_tags` on all 10 modules

## Out of Scope
- Adding entirely new modules (TCK-20260614-WORLDDAT-NEWMODS)
- New compositions (TCK-20260614-WORLDDAT-COMPOSE)
- Any code changes — YAML only
- Adding `provided_features` field (does not exist in WorldModuleSpec schema which has extra="forbid")

## Acceptance Criteria
- All 10 modules in `data/content/world_modules/` load from `WorldModuleRepository` without error after migration
- At least 4 modules have non-empty `relationships`, `biomes`, or `ecology` fields
- At least 1 module has a `quest_definitions` entry
- `tests/integration/worldassembly/test_real_content_world_modules.py` passes (5/5)
- `frontier_living_world.yaml` composition assembles correctly after module migration

## Related Tickets
- TCK-20260614-WORLDMOD-UNIFY (prerequisite — schema must be unified first)
- TCK-20260614-WORLDMOD-QUEST-MOD (prerequisite for quest_definitions field)
- TCK-20260614-WORLDDAT-NEWMODS (follows this)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`
- `docs/architecture/world_repository_layout.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260614-WORLDDAT-MIGRATE/`

## Related Code Areas
- `data/content/world_modules/*.yaml` — all 10 files
- `src/worldmodules/repository.py` — WorldModuleRepository (validation on load)
- `tests/integration/worldassembly/test_real_content_world_modules.py`

## Assumptions / Open Questions
- `merchant_league_to_town_council` ID does NOT exist in catalog — using `town_to_merchants`/`merchants_to_town` instead
- `forest_edge` biome does NOT exist in catalog — wolf_den_near_forest already has correct biome IDs
- `provided_features` is NOT a valid WorldModuleSpec field — using `observability_tags` instead
- Pre-existing 15 failures in `test_strict_world_matrix.py` are due to duplicate resource ID collision in resolver — not caused by this migration

## Implementation Notes
- All relationship IDs verified against `data/content/social/faction_relationships.yaml`
- All biome IDs verified against `data/content/world/biomes.yaml`
- `WorldModuleSpec` schema has `extra="forbid"` — no unknown fields permitted

## Test Summary
- `tests/integration/worldassembly/test_real_content_world_modules.py` — 5/5 pass
- `tests/integration/worldassembly/test_real_content_world_compositions.py` — must pass
- `tests/integration/content/test_strict_world_matrix.py` — 15 pre-existing failures unchanged

## Files Changed
- `data/content/world_modules/frontier_village_core.yaml`
- `data/content/world_modules/goblin_camp_conflict.yaml`
- `data/content/world_modules/old_mine_resource_loop.yaml`
- `data/content/world_modules/wolf_den_near_forest.yaml`
- `data/content/world_modules/bandit_road_trade_pressure.yaml`
- `data/content/world_modules/forest_warden_grove.yaml`
- `data/content/world_modules/moon_cult_ruins.yaml`
- `data/content/world_modules/orc_clan_territory.yaml`
- `data/content/world_modules/sunken_swamp_border.yaml`
- `data/content/world_modules/undead_battlefield.yaml`

## Completion Summary
Migrated all 10 world module YAML files to unified schema: removed `schema_version: "worldmodule.v1"` from all 10 modules; added `observability_tags` to all 10; enriched `frontier_village_core` with `relationships: ["town_to_merchants", "merchants_to_town"]`; enriched `old_mine_resource_loop` with `relationships: ["dwarves_to_goblins"]` and `quest_definitions` (fetch quest `mine_fetch_ore`); remaining modules enriched with observability_tags. All 5 worldassembly integration tests pass (5/5) and all 8 composition tests pass. 17 pre-existing strict matrix / swamp pack test failures unchanged from baseline. Updated SUBSTRATE-NEW-003 parity ledger entry to record the data migration.
