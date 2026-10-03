# Plan: TCK-20260623-FIX-COMBAT-QUEST

## Fixes

| # | File | Change | Type |
|---|---|---|---|
| 1-3 | `tests/unit/combat/test_combat_reward_trace.py:58,72,106` | Update stale label strings | Test bug |
| 4-5 | `src/engine/combat_rewards.py:97-104` | After HOSTILE_CREATURE via relation_projection, set rebirth_eligible based on defender EntityRole | Production bug |
| 6 | `data/content/world/items.yaml` OR `src/core/registries.py` bootstrap | Add steel_sword to catalog or merge instead of replace | Production bug |
| 7 | `tests/unit/social/test_domain_7_social.py:107-126` | Replace "A"/"B" string factions with Faction.HERO_GUILD/MONSTER_HORDE | Test bug |

## Notes
- For fix 6: prefer adding `steel_sword` to the content catalog items YAML — cleaner than patching the bootstrap merge logic
- For fix 4-5: in `classify_defeated_target`, after the relation_projection HOSTILE_CREATURE path, check `defender.identity.role == EntityRole.HERO` and set `rebirth_eligible=True`
