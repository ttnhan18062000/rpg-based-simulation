---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13A-QUEST-DEFS
phase: open
date: 2026-06-20
tags: [content, quest-definitions, world-modules, phase-1]
---

# TCK-20260619-E13A-QUEST-DEFS

## Title
Epic 1.3A · Quest Definitions Batch

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Only 4 quest definitions exist across all 14 world modules (Gap Risk 15/15 per D07 F1). 10 modules — including all 6 conflict modules — have zero quest definitions. This ticket authors 30+ quest definitions distributed across 10 modules, bringing the total to ≥34.

**Depends on:** None (schema already defined by TCK-20260614-WORLDMOD-QUEST-SCHEMA — DONE)

## Scope

Add `quest_definitions:` blocks to these 10 module YAML files (3 quests each = 30 total):

### Conflict modules (6 — highest priority per D07 F1)
1. `data/content/world_modules/goblin_camp_conflict.yaml` — 3 quests (hunt, fetch, defend)
2. `data/content/world_modules/bandit_road_trade_pressure.yaml` — 3 quests (escort, hunt, investigate)
3. `data/content/world_modules/orc_clan_territory.yaml` — 3 quests (hunt, escort, investigate)
4. `data/content/world_modules/scalable_bandit_camp.yaml` — 3 quests (hunt, fetch, defend)
5. `data/content/world_modules/moon_cult_ruins.yaml` — 3 quests (investigate, explore, defend)
6. `data/content/world_modules/undead_battlefield.yaml` — 3 quests (investigate, defend, hunt)

### Settlement/ecology modules (4 — secondary)
7. `data/content/world_modules/wolf_den_near_forest.yaml` — 3 quests (hunt, explore, fetch)
8. `data/content/world_modules/forest_warden_grove.yaml` — 3 quests (escort, defend, investigate)
9. `data/content/world_modules/frontier_village_core.yaml` — 3 quests (fetch, escort, defend)
10. `data/content/world_modules/trading_company_hub.yaml` — 3 quests (fetch, escort, investigate)

Quest schema per TCK-20260614-WORLDMOD-QUEST-SCHEMA:
```yaml
quest_definitions:
  - id: "<module_prefix>_<type>_<noun>"
    type: <escort|hunt|fetch|explore|defend|investigate>
    required_participant_tags: [<tag>, ...]
    required_location_tags: [<tag>, ...]
    reward_budget: <int 80-200>
    procedural_hints:
      difficulty: <1-4>
      escalation: <true|false>
    tags: [<theme>, ...]
```

Do NOT add `expiry_ticks` or `faction_association` — not in current schema.

## Out of Scope
- New module files (E13B)
- Schema extensions
- Dynamic quest generation (Epic 2.3)

## Acceptance Criteria
- `quest_definitions` count in all 14 modules ≥ 34 total
- Each added quest has a unique `id`, valid `type`, non-empty tags
- `python3 -c "from src.worldmodules.repository import WorldModuleRepository; r = WorldModuleRepository(); r.load_all(); print('OK')"` passes
- `pytest tests/integration/worldassembly/test_e2e_smoke.py -x` passes (all compositions still valid)

## Related Tickets
- TCK-20260619-E13-CONTENT-FOUNDATION (parent epic)
- TCK-20260619-E13D-SCENARIOS (consumer — scenario test uses urban_political quests)

## Related Docs
- `docs/audits/D07_content_depth.md` (update F1 count on completion)

## Related Code Areas
- `data/content/world_modules/*.yaml` (modified — 10 files)
- `src/worldmodules/repository.py` (validation reference)
- `src/worldbuilding/schema.py` (`QuestDefinition` model)

## Assumptions / Open Questions
- What `required_participant_tags` are valid? Check entity archetypes' tags in `data/content/entities/` for canonical values (e.g. "hostile", "humanoid", "undead", "spiritual", "beast").
- What `required_location_tags` are valid? Check `data/content/world/terrain.yaml` and region types.

## Implementation Notes
- Keep quest IDs namespaced by module: `goblin_<type>_<noun>`, `bandit_<type>_<noun>`, etc.
- Each module's quests should thematically fit the module's faction and terrain.
- Use `reward_budget: 100` as baseline; increase to 150-200 for difficulty ≥3.
- After authoring, run: `python3 tools/knowledge_search.py query "quest definitions" --top-k 3` to check docs index.
- Run `make knowledge-index-update` after any `docs/` changes.

## Test Summary
Post-authoring validation:
```bash
python3 -c "from src.worldmodules.repository import WorldModuleRepository; r = WorldModuleRepository(); r.load_all(); print('OK')"
pytest tests/integration/worldassembly/test_e2e_smoke.py -x -v
```
Count check: `grep -r "type:" data/content/world_modules/ | grep -E "escort|hunt|fetch|explore|defend|investigate" | wc -l` should be ≥ 34.

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
