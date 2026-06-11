---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260607-COMBAT-REWARD-SERVICE
artifact_type: test_plan
tags: [combat, reward, service]
---

# Test Plan — TCK-20260607-COMBAT-REWARD-SERVICE

## Test file to create

`tests/unit/combat/test_combat_rewards.py`

(Note: ticket says `tests/unit/engine/test_combat_rewards.py` but the existing combat test suite lives under `tests/unit/combat/`. Placing the new file there is consistent with repo patterns. The `tests/unit/engine/` path in the ticket was a reference error.)

---

## Unit tests for CombatRewardClassificationService

### test_monster_role_classify
- Input: `EntityRole.MONSTER`
- Assert: `category == RewardCategory.GOLD_DROP` (or `FULL_REWARD` if that's the chosen name)
- Assert: `xp_multiplier == 10`
- Assert: `gold_eligible == True`
- Assert: `rebirth_eligible == False`
- Assert: `source == "EntityRole.MONSTER"`

### test_hero_role_classify
- Input: `EntityRole.HERO`
- Assert: `xp_multiplier == 20`
- Assert: `gold_eligible == True`
- Assert: `rebirth_eligible == True`
- Assert: `source == "EntityRole.HERO"`

### test_unknown_role_returns_none_category
- Input: `EntityRole.SHOPKEEPER` (or CITIZEN or GUARD)
- Assert: `category == RewardCategory.NONE`
- Assert: `xp_multiplier == 0`
- Assert: `gold_eligible == False`
- Assert: `rebirth_eligible == False`
- Assert: `source` contains the role name string

### test_classification_carries_source_string
- Input: `EntityRole.MONSTER`
- Assert: `source` is a non-empty string
- Assert: `"MONSTER"` in `source`

### test_classification_is_frozen_dataclass
- Verify `RewardClassification` cannot be mutated (frozen=True enforcement)
- Attempt `classification.category = RewardCategory.NONE` and assert `FrozenInstanceError`

---

## Integration verification (existing test file)

`tests/unit/combat/test_combat_reward_hardening.py` — these tests must pass without modification after the refactor:

- `test_combat_reward_consolidation_xp_gold` — MONSTER lv5 → XP=50, gold=25
- `test_skill_reward_consolidation` — MONSTER lv2 → XP=20

Run command: `pytest tests/unit/combat/ -q`

---

## Regression check

`pytest tests/unit/combat/ -q` — full combat unit suite must pass with zero new failures.

---

## Coverage matrix

| Behavior | Test |
|---|---|
| MONSTER → XP*10, gold*5, no rebirth | test_monster_role_classify |
| HERO → XP*20, gold*50, rebirth eligible | test_hero_role_classify |
| Other roles → NONE category, no rewards | test_unknown_role_returns_none_category |
| source field is populated and correct | test_classification_carries_source_string |
| RewardClassification is immutable | test_classification_is_frozen_dataclass |
| End-to-end reward amounts unchanged | test_combat_reward_consolidation_xp_gold (existing) |
| Skill reward unchanged | test_skill_reward_consolidation (existing) |

---

## Out of scope for tests

- AoE reward formula (hardcoded in `resolve_aoe_attack`) — not touched by this ticket
- Lethality gating (`is_lethal` / HERO non-lethal) — not a reward check
- Wound kind classification (`SLASH` vs `CRUSH`) — not a reward check
