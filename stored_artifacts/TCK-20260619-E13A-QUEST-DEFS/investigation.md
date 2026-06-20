# Investigation — TCK-20260619-E13A-QUEST-DEFS

## Context

Ticket: Epic 1.3A · Quest Definitions Batch  
Date: 2026-06-20  
Depends on: TCK-20260614-WORLDMOD-QUEST-SCHEMA (DONE), TCK-20260614-WORLDMOD-QUEST-MOD (DONE)

## Findings

### Schema (src/worldbuilding/schema.py L94–118)

`QuestDefinition` is a frozen Pydantic model with:
- `id: str` (required, non-empty)
- `type: Literal["escort","hunt","fetch","explore","defend","investigate"]`
- `required_participant_tags: List[str]` (default [])
- `required_location_tags: List[str]` (default [])
- `reward_budget: int` (default 100, ge=0)
- `procedural_hints: Dict[str, Any]` (open dict — `difficulty` int 1–4, `escalation` bool)
- `tags: List[str]` (default [])
- `source_module: Optional[str]` — set by assembly resolver, NOT authored

`WorldSpec.quest_definitions` holds assembled quests from all modules. The `WorldModuleSpec` also accepts `quest_definitions` (passed through to assembly).

### WorldModuleRepository (src/worldmodules/repository.py)

Loads all YAML files under `data/content/world_modules/`. Validates each via `WorldModuleSpec(**item)`. If quest_definitions YAML keys do not conform to `QuestDefinition`, validation raises at load time.

### Existing Quest Definitions (4 total across 3 modules)

| Module | Quest IDs |
|---|---|
| ruins_mystery_quest | ruins_first_contact, spirit_source_trace |
| old_mine_resource_loop | mine_fetch_ore |
| forest_deep_ecology | forest_survey |

### Valid Entity Participant Tags (from entity_archetypes.yaml traits/race)

Confirmed tags in use:
- `"humanoid"` — goblins, bandits, orcs, village humans, merchants, guards, wardens
- `"undead"` — undead entities
- `"spiritual"` — spirit court entities
- `"beast"` — wolf/predator entities (race=wolf, traits include pack_hunter, territorial)
- `"opportunistic"` — goblins, bandits
- `"hostile"` — used in observability_tags (not entity traits), but thematically valid as participant tag given existing pattern
- `"merchant_minded"` — merchants

Note: `required_participant_tags` is a freeform list — the schema does not validate against a catalog. Tags are used as downstream hints for procedural generation. Using race/theme/trait values from entity archetypes is correct.

### Valid Location Tags (from terrain values + existing patterns)

Confirmed terrain types: `"forest"`, `"road"`, `"plain"`, `"cave"`, `"ruin"`, `"swamp"`
Confirmed location tags in use: `"ruins"`, `"wilderness"`, `"mine"`, `"underground"`
Additional semantically valid: `"road"`, `"forest"`, `"plain"`, `"cave"`, `"settlement"`, `"trade_route"`

### Modules Without Quest Definitions (10 target modules)

All 10 target modules lack `quest_definitions:` blocks:
1. goblin_camp_conflict — forest, hazard 3, goblin_warband
2. bandit_road_trade_pressure — road, hazard 2, bandit_company + merchant_league
3. orc_clan_territory — plain, hazard 3, orc_clan
4. scalable_bandit_camp — forest, hazard 2, bandit_company
5. moon_cult_ruins — cave, hazard 4, moon_cult + arcane_circle
6. undead_battlefield — ruin, hazard 4, undead_remnants + spirit_court
7. wolf_den_near_forest — forest, hazard 1-2, wild_beast_pack
8. forest_warden_grove — forest, hazard 1.5, forest_wardens + spirit_court
9. frontier_village_core — plain, hazard 0, town_council + merchant_league
10. trading_company_hub — plain, hazard 0.5, merchant_league + town_council

### D07 Audit

Gap Risk F1 score: 15/15 (critically thin). Ticket targets raising total from 4 to ≥34 by adding 30 definitions (3 per module × 10 modules). Audit file `docs/audits/D07_content_depth.md` must be updated on completion to reflect new count.

## Risk Assessment

- Low: Schema is fully defined and stable. No code changes needed — YAML authoring only.
- Low: `required_participant_tags` and `required_location_tags` are freeform — no catalog validation.
- Low: IDs must be unique across a single module (repository checks for duplicate module_ids, not quest IDs — but unique IDs per module is best practice).
- None: No parity ledger entries cover quest definition content counts.
