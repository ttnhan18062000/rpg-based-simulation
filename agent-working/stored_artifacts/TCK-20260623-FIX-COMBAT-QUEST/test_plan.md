---
ticket_id: TCK-20260623-FIX-COMBAT-QUEST
phase: test_plan
---

# Test Plan: TCK-20260623-FIX-COMBAT-QUEST

## Verification Command (full scope)

```bash
python3 -m pytest tests/unit/combat/ tests/unit/quest/ tests/unit/social/ -q --tb=short -m "not slow"
```

Expected: 0 failures, 313 tests pass.

---

## Per-Fix Verification

### Fix Group A — Stale string/enum constants (failures 1, 2, 3)
File: `tests/unit/combat/test_combat_reward_trace.py`

```bash
python3 -m pytest tests/unit/combat/test_combat_reward_trace.py -v --tb=short
```

Tests to verify:
- `test_resolve_attack_monster_kill_reward_source_is_hostile_relation` (line 58: `"relation_projection"`)
- `test_resolve_attack_hero_defeat_has_hero_kill_category` (line 72: `RewardCategory.HOSTILE_CREATURE.value`)
- `test_resolve_skill_usage_kill_reward_source_value` (line 106: `"relation_projection"`)
- Regression guard: `test_resolve_attack_monster_kill_reward_category` must still pass (asserts `HOSTILE_CREATURE`, not changed)
- Regression guard: `test_resolve_attack_no_kill_no_reward_keys` must still pass

### Fix Group B — rebirth_eligible for HERO defenders (failures 4, 5)
File: `src/engine/combat_rewards.py`

```bash
python3 -m pytest tests/unit/combat/test_rpg_core_recovery.py -v --tb=short
```

Tests to verify:
- `test_hero_mortality_rebirth` (hero generation increments from 3 → 4)
- `test_hero_permadeath` (hero at gen=4 gets `is_permadeath=True`)
- Regression guard: `test_combat_progression_rewards` must still pass (monster kill still gives XP/gold)
- Regression guard: `test_quest_lifecycle` must still pass (monster kill + quest completion)

Also run full combat suite:
```bash
python3 -m pytest tests/unit/combat/ -v --tb=short -m "not slow"
```

### Fix Group C — steel_sword in ItemRegistry / bootstrap merge (failure 6)
File: `src/engine/combat_rewards.py` or catalog or `src/core/items.py`

```bash
python3 -m pytest tests/unit/social/test_town_contract.py -v --tb=short
```

Tests to verify:
- `test_blacksmith_material_consumption` (crafting produces steel_sword, gold_delta=-60)
- Regression guards: all other `test_blacksmith_*` tests must still pass
- `test_shop_sell_price_enforcement` must still pass (different item path)

Quick isolation check — run in isolation to confirm fix:
```bash
python3 -m pytest tests/unit/social/test_town_contract.py::test_blacksmith_material_consumption -v --tb=long
```

### Fix Group D — tactical faction setup (failure 7)
File: `tests/unit/social/test_domain_7_social.py`

```bash
python3 -m pytest tests/unit/social/test_domain_7_social.py -v --tb=short
```

Tests to verify:
- `test_tactical_trust_obedience` (member targets hostile_close id=98 over group target id=99)
- Regression guard: `test_protector_guarding` must still pass
- Regression guard: all other domain 7 social tests must still pass

---

## Post-Fix Full Regression

After all fixes applied:

```bash
python3 -m pytest tests/unit/combat/ tests/unit/quest/ tests/unit/social/ -q -m "not slow"
```

Expected: 313 passed, 0 failed.

Also run parity tests touching combat rewards:
```bash
python3 -m pytest tests/ -k "reward" -q --tb=short -m "not slow" 2>/dev/null | tail -5
```
