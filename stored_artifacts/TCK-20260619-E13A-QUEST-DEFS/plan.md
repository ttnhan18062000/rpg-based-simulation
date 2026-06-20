# Plan — TCK-20260619-E13A-QUEST-DEFS

## Objective

Add `quest_definitions:` blocks (3 quests each) to 10 world module YAML files.
Total added: 30. Total in repo after: ≥34.

## Scope Guards

- Do NOT add `expiry_ticks` or `faction_association` (not in schema)
- Do NOT add `source_module` (set by assembly resolver, not authored)
- Do NOT create new module files (E13B scope)
- Do NOT modify src/ code files
- Do NOT modify schema or repository code

## Quest ID Convention

`{module_prefix}_{type}_{noun}` — all lowercase, underscores.

## Steps

### Step 1: goblin_camp_conflict.yaml
File: `data/content/world_modules/goblin_camp_conflict.yaml`
Add 3 quests: hunt (clear camp), fetch (loot), defend (protect village)
Participant tags: `["humanoid", "opportunistic"]` (goblins)
Location tags: `["wilderness", "forest"]`

### Step 2: bandit_road_trade_pressure.yaml
File: `data/content/world_modules/bandit_road_trade_pressure.yaml`
Add 3 quests: escort (caravan), hunt (bandit leader), investigate (ambush source)
Participant tags: `["humanoid", "opportunistic"]` (bandits), `["humanoid", "merchant_minded"]` (merchants)
Location tags: `["road", "wilderness"]`

### Step 3: orc_clan_territory.yaml
File: `data/content/world_modules/orc_clan_territory.yaml`
Add 3 quests: hunt (orc patrol), escort (settler), investigate (orc expansion)
Participant tags: `["humanoid"]` (orcs)
Location tags: `["wilderness", "plain"]`

### Step 4: scalable_bandit_camp.yaml
File: `data/content/world_modules/scalable_bandit_camp.yaml`
Add 3 quests: hunt (clear camp), fetch (stolen goods), defend (checkpoint)
Participant tags: `["humanoid", "opportunistic"]` (bandits)
Location tags: `["wilderness", "forest"]`

### Step 5: moon_cult_ruins.yaml
File: `data/content/world_modules/moon_cult_ruins.yaml`
Add 3 quests: investigate (ritual site), explore (cave network), defend (arcane circle)
Participant tags: `["humanoid", "magic_sensitive"]` (cultists)
Location tags: `["cave", "wilderness"]`

### Step 6: undead_battlefield.yaml
File: `data/content/world_modules/undead_battlefield.yaml`
Add 3 quests: investigate (source of undead), defend (survivors), hunt (wraith patrol)
Participant tags: `["undead"]`, `["spiritual"]`
Location tags: `["ruins", "wilderness"]`

### Step 7: wolf_den_near_forest.yaml
File: `data/content/world_modules/wolf_den_near_forest.yaml`
Add 3 quests: hunt (wolf pack), explore (forest trail), fetch (herb gathering)
Participant tags: `["beast"]`
Location tags: `["wilderness", "forest"]`

### Step 8: forest_warden_grove.yaml
File: `data/content/world_modules/forest_warden_grove.yaml`
Add 3 quests: escort (warden patrol), defend (sacred grove), investigate (spirit disturbance)
Participant tags: `["humanoid"]` (wardens), `["spiritual"]`
Location tags: `["wilderness", "forest"]`

### Step 9: frontier_village_core.yaml
File: `data/content/world_modules/frontier_village_core.yaml`
Add 3 quests: fetch (supply run), escort (merchant), defend (village gate)
Participant tags: `["humanoid"]`
Location tags: `["plain", "settlement"]`

### Step 10: trading_company_hub.yaml
File: `data/content/world_modules/trading_company_hub.yaml`
Add 3 quests: fetch (trade goods), escort (merchant convoy), investigate (trade sabotage)
Participant tags: `["humanoid", "merchant_minded"]`
Location tags: `["plain", "trade_route"]`

### Step 11: Update D07 audit
File: `docs/audits/D07_content_depth.md`
Update F1 entry: change count from 4 to 34, update status.

### Step 12: Run verification
```bash
python3 -c "from src.worldmodules.repository import WorldModuleRepository; r = WorldModuleRepository(); r.load_all(); print('OK')"
grep -r "type:" data/content/world_modules/ | grep -E "escort|hunt|fetch|explore|defend|investigate" | wc -l
pytest tests/integration/worldassembly/test_e2e_smoke.py -x -v
pytest tests/unit/worldbuilding/test_quest_definition.py -v
```

## Acceptance Criteria Mapping

| Criterion | Step |
|---|---|
| ≥34 total quest_definitions | Steps 1–10 |
| Each quest has unique id, valid type, non-empty tags | Steps 1–10 (enforced by schema) |
| Repository load passes | Step 12 |
| E2E smoke tests pass | Step 12 |
| D07 F1 count updated | Step 11 |

## Deviations

_None yet._
