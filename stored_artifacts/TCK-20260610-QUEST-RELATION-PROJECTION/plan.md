---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-QUEST-RELATION-PROJECTION
artifact_type: plan
tags: [quest, relation, projection]
---

# TCK-20260610-QUEST-RELATION-PROJECTION — Plan

## Changes

### `src/engine/quests.py` — `evaluate_combat_victory`

Add `victim_entity: Optional[EntityState] = None` parameter. Before the project loop, pre-resolve:
- `_victim_archetype_id` and `_victim_faction_id` via `EntityIdentityResolver.resolve(victim_entity)`
- `_attacker_faction_id` via `EntityIdentityResolver.resolve(attacker)`

Resolution order inside project loop:
1. `target_archetype_id` in metadata → compare to `_victim_archetype_id`
2. `target_faction_id` in metadata → compare to `_victim_faction_id`
3. `target_projected_label` in metadata → call `RelationProjectionService.project_relation(...)` lazily; compare label
4. `target_kind` legacy fallback (existing behavior, unchanged)

Projection service init is lazy (only when a quest has `target_projected_label`).

### `src/engine/domain/combat_actions.py`

Line 72: add `victim_entity=target` to `evaluate_combat_victory` call.

### `src/engine/domain/aoe_actions.py`

Lines 91-94: add `victim_entity=target` to `evaluate_combat_victory` call.

### Tests — `tests/unit/quest/test_quest_relation_projection.py`

| Test | Scenario |
|---|---|
| `test_hunt_by_archetype_id` | quest with target_archetype_id matches victim with that archetype |
| `test_hunt_by_faction_id` | quest with target_faction_id matches victim with that faction |
| `test_hunt_by_projected_label_enemy` | quest with target_projected_label="enemy" matches via catalog projection |
| `test_hunt_legacy_target_kind_fallback` | quest with target_kind matches via legacy path |
| `test_hunt_archetype_no_match` | wrong archetype → quest not advanced |
| `test_hunt_neutral_projected_label_no_match` | target_projected_label="enemy" but victim is neutral → no advance |
| `test_hunt_no_victim_entity_legacy_only` | victim_entity=None → falls back to target_kind |
