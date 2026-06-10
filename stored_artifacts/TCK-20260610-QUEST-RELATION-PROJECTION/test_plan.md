# TCK-20260610-QUEST-RELATION-PROJECTION — Test Plan

## Test File

`tests/unit/quest/test_quest_relation_projection.py`

## Coverage

| Test | Pass condition |
|---|---|
| `test_hunt_by_archetype_id` | QuestUpdate emitted when archetype_id matches |
| `test_hunt_by_faction_id` | QuestUpdate emitted when faction_id matches |
| `test_hunt_by_projected_label_enemy` | QuestUpdate emitted via catalog projection (hero_guild vs goblin_warband = enemy) |
| `test_hunt_legacy_target_kind_fallback` | QuestUpdate emitted for target_kind match (victim_entity=None, legacy path) |
| `test_hunt_archetype_no_match` | No QuestUpdate when archetype_id doesn't match victim |
| `test_hunt_neutral_projected_label_no_match` | No QuestUpdate when projected label is neutral, not enemy |
| `test_hunt_no_victim_entity_legacy_only` | No victim_entity → only legacy target_kind path runs |

## Regression

Run `tests/unit/quest/` suite to confirm all existing quest tests still pass.
