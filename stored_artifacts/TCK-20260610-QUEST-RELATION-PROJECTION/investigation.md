# TCK-20260610-QUEST-RELATION-PROJECTION — Investigation

## Key Files

- `src/engine/quests.py` — `QuestResolutionSystem.evaluate_combat_victory(attacker, victim_kind)`:
  - Called by `combat_actions.py:72` with `(entity, target.kind)` and `aoe_actions.py:91` with `(entity, target.kind)`
  - Currently matches `project.metadata["target_kind"] == victim_kind` (entity.kind string comparison)
  - No faction_id, archetype_id, or relation projection support
- `src/core/models/quests.py` — `QuestState` has a free-form `metadata: Dict[str, Any]` field — no model extension needed
- `src/entities/identity_resolver.py` — `EntityIdentityResolver` resolves `archetype_id`, `faction_id`
- `src/content_semantics/relation.py` — `RelationProjectionService.project_relation()` returns `RelationProjection.label`
- `src/content_semantics/faction.py` — `get_faction_semantics_service()` provides singleton with `.repo` holding catalog

## Call Sites

- `src/engine/domain/combat_actions.py:72`: `q_updates = QuestResolutionSystem.evaluate_combat_victory(entity, target.kind)` — `target` entity is available
- `src/engine/domain/aoe_actions.py:91`: Same pattern — `target` entity is available at call site

## Resolution

No new model needed — `QuestState.metadata` accepts arbitrary keys. New resolution paths read:
- `metadata["target_archetype_id"]` — matched against `EntityIdentityResolver.resolve(victim).archetype_id`
- `metadata["target_faction_id"]` — matched against `EntityIdentityResolver.resolve(victim).faction_id`
- `metadata["target_projected_label"]` — matched against `RelationProjectionService.project_relation(...).label` from attacker perspective
- `metadata["target_kind"]` — existing legacy fallback (unchanged)
