---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260608-CLASSIFY-DEFEATED-TARGET
artifact_type: investigation
tags: [classify, defeated, target]
---

# Investigation — TCK-20260608-CLASSIFY-DEFEATED-TARGET

## Current Behavior
CombatRewardClassificationService only exposed classify(EntityRole). All three combat resolution
call sites (resolve_attack, resolve_skill_usage, resolve_multi_attack) passed defender.identity.role directly.
EntityState.identity.faction is an int (Faction enum). Faction.MONSTER_HORDE = 1.

## New Method
classify_defeated_target(attacker, defender, state):
1. If defender.identity.faction == Faction.MONSTER_HORDE → HOSTILE_CREATURE (new category)
2. Else → classify(EntityRole(defender.identity.role)) — legacy fallback

## No circular import risk: combat_rewards.py imports from src.core.enums, TYPE_CHECKING guards EntityState/AuthoritativeState.

## Parity: COMB-280 updated.
