---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-REWARD-RELATION-CLASSIFY
artifact_type: plan
tags: [reward, relation, classify]
---

# Plan — TCK-20260610-REWARD-RELATION-CLASSIFY

## Step 1 — Rewrite classify_defeated_target (src/engine/combat_rewards.py)

Replace lines 83-95:
```python
# Step 1: relation projection via FactionSemanticsService
try:
    from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service
    from src.content_semantics.relation import RelationContext
    attacker_faction_id = get_faction_id_str(attacker)
    defender_faction_id = get_faction_id_str(defender)
    context = RelationContext(combat_engaged=True)
    svc = get_faction_semantics_service()
    if svc.is_hostile_compat(attacker_faction_id, defender_faction_id, context):
        return RewardClassification(
            category=RewardCategory.HOSTILE_CREATURE,
            xp_multiplier=10,
            gold_multiplier=5,
            gold_eligible=True,
            rebirth_eligible=False,
            source="relation_projection",
        )
except Exception:
    pass
# Step 2: Legacy EntityRole fallback
try:
    role = EntityRole(defender.identity.role)
except ValueError:
    return cls._NONE_CLASSIFICATION
return cls.classify(role)
```

## Step 2 — Update tests (tests/unit/combat/test_combat_rewards.py)

1. `test_classify_defeated_target_monster_horde_returns_hostile_creature`:
   Change assertion from `result.source == "hostile_relation"` to `result.source == "relation_projection"`.
   Update docstring to note source path.

2. `test_classify_defeated_target_hero_defender_returns_hero_kill`:
   Change attacker from `_make_entity(1, EntityRole.MONSTER, Faction.MONSTER_HORDE)` to
   `_make_entity(1, EntityRole.CITIZEN, Faction.NEUTRAL)` — NEUTRAL faction is not hostile to HERO_GUILD
   so relation projection returns False → EntityRole fallback → HERO_KILL still reachable.
   Update docstring.

3. Add `test_classify_defeated_target_monster_attacks_hero_gives_hostile_creature`:
   attacker=MONSTER_HORDE, defender=HERO_GUILD → relation_projection → HOSTILE_CREATURE, source="relation_projection"

4. Add `test_classify_defeated_target_source_is_relation_projection_for_hostile_factions`:
   Source field is "relation_projection" (not "hostile_relation") for any hostile pair.

## Step 3 — Update parity ledger (docs/parity_ledger/combat_movement.yaml)

COMB-280 entry:
- Update `v2_evidence` to mention FactionSemanticsService.is_hostile_compat() as primary step
- Add `divergence_note` for monster→hero classification change

## Files Changed
- `src/engine/combat_rewards.py`
- `tests/unit/combat/test_combat_rewards.py`
- `docs/parity_ledger/combat_movement.yaml`
