---
status: active
artifact_type: plan
ticket_id: TCK-20260627-P2D-FACTION-RELS
date: 2026-06-27
---

# Plan — TCK-20260627-P2D-FACTION-RELS

## Objective

Add ≥16 new entries to `data/content/social/faction_relationships.yaml` to reach ≥30 total. Ensure ≥10 hostile entries. All entries must pass Pydantic schema validation (`extra="forbid"`).

## Scope Guards

- **Touch only**: `data/content/social/faction_relationships.yaml`
- **Do NOT touch**: faction engine code, parity ledger (no behavior change), factions.yaml
- **Do NOT add**: DiplomaticState enum values as axis values; undefined faction IDs; extra YAML fields

## Dependency Map

Single file change. No dependencies between steps.

## Ordered Steps

### Step 1 — Add 20 new entries to `data/content/social/faction_relationships.yaml`

Append the following 20 directed relationships (covering high-encounter-frequency pairs):

| # | id | source → target | relationship_model | hostility |
|---|---|---|---|---|
| 1 | bandits_to_town | bandit_company → town_council | outlaw_settlement_hostility | high |
| 2 | hero_guild_to_goblin | hero_guild → goblin_warband | defender_raider_conflict | high |
| 3 | goblin_to_hero_guild | goblin_warband → hero_guild | threat_avoidance | high |
| 4 | orc_to_goblin | orc_clan → goblin_warband | dominance_raider_rivalry | high |
| 5 | goblin_to_orc | goblin_warband → orc_clan | weaker_rival_fear | medium |
| 6 | dwarves_to_orc | dwarven_mine_clan → orc_clan | ancient_border_hostility | high |
| 7 | orc_to_dwarves | orc_clan → dwarven_mine_clan | resource_territory_conflict | high |
| 8 | dragon_cult_to_town | dragon_cult → town_council | expansionist_threat | high |
| 9 | town_to_dragon_cult | town_council → dragon_cult | existential_threat_response | high |
| 10 | moon_cult_to_arcane | moon_cult → arcane_circle | arcane_ideological_conflict | high |
| 11 | arcane_to_moon_cult | arcane_circle → moon_cult | research_rivalry | medium |
| 12 | undead_to_forest | undead_remnants → forest_wardens | corruption_expansion | high |
| 13 | forest_to_undead | forest_wardens → undead_remnants | purge_corrupted | high |
| 14 | hero_to_town | hero_guild → town_council | protector_patron | none |
| 15 | town_to_hero | town_council → hero_guild | patron_employer | none |
| 16 | arcane_to_dwarves | arcane_circle → dwarven_mine_clan | reagent_trade_alliance | none |
| 17 | dwarves_to_arcane | dwarven_mine_clan → arcane_circle | crystal_trade_partner | none |
| 18 | swamp_tribe_to_town | swamp_tribe → town_council | territorial_defensive_hostility | high |
| 19 | spirit_court_to_forest | spirit_court → forest_wardens | spiritual_kinship_alliance | none |
| 20 | forest_to_spirit_court | forest_wardens → spirit_court | guardian_spiritual_ally | none |

**Post-step count:** 14 existing + 20 new = 34 total
**Hostile entries after step:** existing ~9 + new 11 hostile = ~20 hostile entries (well above AC of 10)

### Step 2 — Verify schema and counts

Run inline Python count check and pytest to confirm:
```bash
python3 -c "
import yaml
data = yaml.safe_load(open('data/content/social/faction_relationships.yaml'))
print(f'Total: {len(data)} (need >=30)')
hostile = [r for r in data if r.get('axes', {}).get('hostility', '') in ('high', 'high_contextual')]
print(f'Hostile: {len(hostile)} (need >=10)')
"
pytest tests/unit/content/ -v
```

## Acceptance Criteria Mapping

| AC | Step | Evidence |
|---|---|---|
| ≥30 entries | Step 1 | 34 total after append |
| ≥10 hostile | Step 1 | ~20 entries with hostility:high |
| make world-validate passes | Step 2 | Schema valid; world-validate runs worldbuilding CLI not catalog |
| Catalog validation passes | Step 2 | pytest content tests |

## Deviations

_None yet — updated if implementation differs._
