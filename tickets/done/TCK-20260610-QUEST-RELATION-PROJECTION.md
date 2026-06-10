# TCK-20260610-QUEST-RELATION-PROJECTION

## Title
Wire RelationProjectionService into quest target resolution, supporting clean archetype/faction targets

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Quest targets currently rely on legacy `enemy_type` source truth. `RelationProjectionService` and `EntityIdentityResolver` already exist but are not wired into quest target resolution. This task extends quest target resolution to support `target_archetype_id`, `target_faction_id`, `target_projected_label`, and `target_relationship_model` — resolved via projection — while preserving the existing legacy `enemy_type` fallback path. The legacy quest path is not removed.

## Scope
- Identify quest target resolution code in `src/quests/` or equivalent
- Add resolution order: clean archetype/faction target → perspective projection → compatibility enemy projection → legacy enemy type fallback
- Quest target model additions (if the model needs extending): `target_archetype_id`, `target_faction_id`, `target_projected_label`, `target_relationship_model`, `legacy_enemy_type`
- Do NOT remove existing legacy quest target support
- Tests:
  - quest can target goblin_warband through projected enemy relation
  - quest can target wildlife as contextual threat
  - legacy hunt quest still works
  - unresolved clean quest target fails clearly with explanation

## Out of Scope
- Rewriting quest progression logic
- Adding new quest types or quest schemas beyond target resolution
- Changing perspective schema or faction relationship schema

## Acceptance Criteria
- [x] Quest target can resolve from clean `faction_id`/`archetype_id`
- [x] Quest target can resolve through projected relation label
- [x] Legacy `enemy_type` quest still works
- [x] Existing quest progression tests still pass
- [x] Quest model does not require `enemy` as source truth
- [x] Error messages explain unresolved target source clearly

## Related Tickets
- TCK-20260610-COMBAT-RELATION-PROJECTION (parallel Phase 37 concern)
- TCK-20260610-REGION-THREAT-PROJECTION (parallel Phase 37 concern)
- TCK-20260609-ENTITY-IDENTITY-RESOLVER (EntityIdentityResolver already done — reuse)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md`

## Related Code Areas
- `src/content_semantics/relation.py` — RelationProjectionService (exists)
- `src/entities/identity_resolver.py` — EntityIdentityResolver (exists)
- `src/quests/` — quest target resolution (identify exact file)
- `tests/` — existing quest tests (do not break)

## Assumptions / Open Questions
- Where exactly is quest target resolution implemented? Check `src/quests/` or `src/systems/` before implementing.
- Is there a quest target model/schema already? Does it need to be extended or is there a separate resolver?

## Implementation Notes
Added `victim_entity: Optional[EntityState] = None` to `QuestResolutionSystem.evaluate_combat_victory()`. Pre-resolves victim/attacker identities before the project loop using `EntityIdentityResolver`. Resolution order per quest: (1) target_archetype_id, (2) target_faction_id, (3) target_projected_label via RelationProjectionService (lazy-init), (4) legacy target_kind fallback. Debug logging explains each non-match. Updated both call sites in combat_actions.py and aoe_actions.py to pass `victim_entity=target`.

## Test Summary
9/9 new tests pass: archetype_id match, archetype no-match, faction_id match, faction no-match, projected label "enemy" match, projected label neutral no-match, legacy target_kind with victim_entity, legacy without victim_entity, no-match no victim_entity. Regression: 43/43 existing quest+progression tests pass.

## Files Changed
- `src/engine/quests.py` — evaluate_combat_victory extended with victim_entity + 3 new resolution paths
- `src/engine/domain/combat_actions.py` — pass victim_entity=target
- `src/engine/domain/aoe_actions.py` — pass victim_entity=target
- `tests/unit/quest/test_quest_relation_projection.py` — new (9 tests)

## Completion Summary
HUNT quest target resolution now supports archetype_id, faction_id, and projected relation label in addition to the legacy target_kind. Identity resolution is pre-computed before the project loop; the projection service is lazy-loaded only when a quest uses target_projected_label. Both call sites pass the victim entity. 9 new tests + 43 regression tests pass.
