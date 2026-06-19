---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13-CONTENT-FOUNDATION
phase: open
date: 2026-06-19
tags: [content, quest-definitions, crafting-recipes, world-modules, scenarios, epic, phase-1]
---

# TCK-20260619-E13-CONTENT-FOUNDATION

## Title
Epic 1.3 · Content Foundation Layer

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
430 catalog entries exist but critically skewed: only 4 quest definitions (Gap Risk 15/15), 0 terrain/population module types, 8 crafting recipes for 34 items, and all 8 scenarios are frontier-world variants. Without content depth, quest generation, crafting loops, and world variety cannot produce meaningful runs.

Score: 9/10 · Effort: M · Source: `docs/audits/D07_content_coverage.md`

## Scope

**Quest definitions (primary — Gap Risk 15/15):**
- Author 30+ quest definitions covering at least 8 world modules (currently only 3 have any)
- Categories: resource_fetch (10), investigation (5), escort (5), elimination (5), exploration (5), diplomatic (5+)
- Each quest: trigger_condition, objective_chain, reward_spec, faction_association, expiry_ticks
- Extend at least 4 of the 6 conflict modules — conflict without quest objective produces pure combat loops

**Module types (secondary — Gap Risk 10/15):**
- `mountain_pass` module: traversal constraint, altitude pressure
- `river_crossing` module: movement cost, resource source
- `nomadic_herd` population module: migration pressure, seasonal density
- `settled_quarter` population module: service density, faction alignment

**Crafting recipes (tertiary — Gap Risk 10/15):**
- Expand from 8 to 25+ recipes; at least one per item category
- Complete at least one gather→craft→upgrade chain: raw material → refined → item → improved item

**Scenario coverage:**
- Add scenarios for `dungeon_crawl`, `urban_political`, `wilderness_survival` — all 8 existing are frontier-world variants

**Child tickets:** (a) quest definitions batch, (b) module types, (c) crafting recipe expansion, (d) scenario authoring

## Out of Scope
- Dynamic/procedural quest generation (Epic 2.3)
- Faction quest chains (Phase 5)
- Authored faction storylines

## Acceptance Criteria
- 400-tick `urban_political` run produces at least one `quest_started` and `quest_completed` event
- At least one crafting chain completes in a 1000-tick run
- All world compositions have at least 2 scenarios
- Quest definitions catalog reaches ≥30 entries

## Related Tickets
- TCK-20260619-E21-RESOURCE-ECOLOGY (unlocked: ecology needs resources to deplete)
- TCK-20260619-E23-QUEST-GENERATION (unlocked: pressure-driven gen uses authored templates as fallbacks)

## Related Docs
- `docs/audits/D07_content_coverage.md` (update content counts on completion)
- `docs/mechanics/03_economic_laws.md` (update crafting recipe documentation if schema extended)
- `docs/plans/long_term_development_roadmap.md` § Epic 1.3
- `docs/simulation/domains/world_emergence_contract.md` (quest extension pattern)
- `docs/quests/quest_contract.md` (update if quest schema gains new fields)
- `docs/parity_ledger/town_resource.yaml` (crafting/harvesting entries — add quest and recipe counts as `v2_evidence`)
- `docs/parity_ledger/progression.yaml` (quest reward entries)

## Related Stored Artifacts
- (none specific — fresh content authoring)

## Related Code Areas
- `data/content/quest_definitions/` (or equivalent content directory)
- `data/content/crafting_recipes/`
- `data/content/modules/`
- `data/scenarios/`
- `src/systems/world_systems/quests.py` (quest generation from strategic blockers — pattern reference)

## Assumptions / Open Questions
- Where are quest definitions currently stored? Check `data/content/` or world module YAML for existing pattern
- Does the quest schema support `expiry_ticks` and `faction_association`? If not, extend the schema first as a child ticket
- Which schema validates world module YAML? Check `src/worldassembly/` or `src/worldgeneration/schema.py:L8`

## Implementation Notes
Content-authoring epic. Each child ticket is a batch of authored data files. Keep the existing schema conventions established by done work (`TCK-20260425-PH8-M2` for quest generation, `TCK-20260614-WORLDDAT-NEWMODS` for world modules). Don't extend schemas in this epic unless essential — prefer fitting content into existing schemas.

After each content batch: update `docs/audits/D07_content_coverage.md` gap counts. After adding quest definitions, update `docs/quests/quest_contract.md` if new fields were needed. Update `docs/parity_ledger/town_resource.yaml` crafting/quest entries. Run `make knowledge-index-update` after any docs/ file changes.

## Test Summary
- New file `tests/integration/scenarios/test_content_foundation.py`:
  - `test_quest_starts_in_urban_political()` — 400-tick run; assert ≥1 `quest_started` event in `simulation_events.jsonl`
  - `test_crafting_chain_completes()` — 1000-tick run; assert at least one full gather→craft→item chain produces a final item
  - `test_all_world_compositions_have_two_scenarios()` — schema check; assert each composition has ≥2 scenario entries
- Regression: run existing `src/lab/validator.py` (ScenarioValidator) and `src/worldbuilding/validator.py` (WorldValidator) against all new content files — must pass with zero errors

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
