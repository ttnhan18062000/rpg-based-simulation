---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260607-COMBAT-REWARD-SERVICE
artifact_type: plan
tags: [combat, reward, service]
---

# Plan — TCK-20260607-COMBAT-REWARD-SERVICE

## Decision Summary

All questions resolved from investigation. No unresolved questions.

---

## Step 1 — Create `src/engine/combat_rewards.py`

New file. Contains:

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from src.core.enums import EntityRole


class RewardCategory(Enum):
    NONE = "none"
    MONSTER_KILL = "monster_kill"
    HERO_KILL = "hero_kill"


@dataclass(frozen=True)
class RewardClassification:
    category: RewardCategory
    xp_multiplier: int      # Multiplier against evolution_level; MONSTER=10, HERO=20, else=0
    gold_multiplier: int    # Multiplier against evolution_level; MONSTER=5, HERO=50, else=0
    gold_eligible: bool
    rebirth_eligible: bool
    source: str             # e.g. "EntityRole.MONSTER"


class CombatRewardClassificationService:
    """
    Owns all entity-role → reward-category mapping.
    Reads entity role. Does not mutate any state.
    Logic IDs: COMB-279, COMB-280, PROG-004, PROG-064
    """

    _CLASSIFICATIONS: dict[EntityRole, RewardClassification] = {
        EntityRole.MONSTER: RewardClassification(
            category=RewardCategory.MONSTER_KILL,
            xp_multiplier=10,
            gold_multiplier=5,
            gold_eligible=True,
            rebirth_eligible=False,
            source="EntityRole.MONSTER",
        ),
        EntityRole.HERO: RewardClassification(
            category=RewardCategory.HERO_KILL,
            xp_multiplier=20,
            gold_multiplier=50,
            gold_eligible=True,
            rebirth_eligible=True,
            source="EntityRole.HERO",
        ),
    }

    _NONE_CLASSIFICATION = RewardClassification(
        category=RewardCategory.NONE,
        xp_multiplier=0,
        gold_multiplier=0,
        gold_eligible=False,
        rebirth_eligible=False,
        source="EntityRole.NONE",
    )

    @classmethod
    def classify(cls, entity_role: EntityRole) -> RewardClassification:
        return cls._CLASSIFICATIONS.get(entity_role, cls._NONE_CLASSIFICATION)
```

### Design decisions
- `xp_multiplier` and `gold_multiplier` are `int` (not float) because the existing formulas are integer arithmetic (`LVL * 10`, `LVL * 5`).
- `_CLASSIFICATIONS` is a class-level dict — no instance state, consistent with `CombatResolutionSystem` all-static pattern.
- `_NONE_CLASSIFICATION` has `source="EntityRole.NONE"` to avoid empty-string ambiguity in telemetry.
- `RewardCategory` uses three values: `NONE`, `MONSTER_KILL`, `HERO_KILL`. The ticket suggested `GOLD_DROP`/`FULL_REWARD`/`XP_ONLY` as illustrative; the final design uses semantically clearer names that match the Mechanics Bible role table.

---

## Step 2 — Update `src/engine/combat.py`

### 2a — `resolve_attack` (lines 175-187)

Replace:
```python
if defender.identity.role == EntityRole.MONSTER:
    xp_gain = defender.identity.evolution_level * 10
    gold_gain = defender.identity.evolution_level * 5
elif defender.identity.role == EntityRole.HERO:
    xp_gain = defender.identity.evolution_level * 20
    gold_gain = defender.identity.evolution_level * 50
    
    if defender.lifecycle.generation < 4:
        gen_delta = 1
        outcome = "REBIRTH"
    else:
        perma_set = True
        outcome = "PERMADEATH"
```

With:
```python
from src.engine.combat_rewards import CombatRewardClassificationService
classification = CombatRewardClassificationService.classify(defender.identity.role)
xp_gain = defender.identity.evolution_level * classification.xp_multiplier
gold_gain = defender.identity.evolution_level * classification.gold_multiplier

if classification.rebirth_eligible:
    if defender.lifecycle.generation < 4:
        gen_delta = 1
        outcome = "REBIRTH"
    else:
        perma_set = True
        outcome = "PERMADEATH"
```

The `ResourceTransferIntent` emissions that follow remain unchanged. Add `classification.source` to the `trace` dict:
```python
trace["REWARD_SOURCE"] = classification.source
```

### 2b — `resolve_skill_usage` (line 277)

Replace:
```python
if not alive:
    if defender.identity.role == EntityRole.MONSTER:
        xp_gain = 10 * defender.identity.evolution_level
        gold_gain = 5 * defender.identity.evolution_level
```

With:
```python
if not alive:
    from src.engine.combat_rewards import CombatRewardClassificationService
    classification = CombatRewardClassificationService.classify(defender.identity.role)
    xp_gain = classification.xp_multiplier * defender.identity.evolution_level
    gold_gain = classification.gold_multiplier * defender.identity.evolution_level
```

Note: `resolve_skill_usage` previously only rewarded MONSTER kills. After refactor, a HERO kill via skill will also grant the HERO-tier reward. This is correct per Mechanics Bible Ch02 (role-based reward table has no skill exception). The existing `test_skill_reward_consolidation` uses a MONSTER target so it will pass unchanged.

### 2c — `resolve_multi_attack` (lines 383-388)

Replace:
```python
if defender.identity.role == EntityRole.MONSTER:
    xp_gain = defender.identity.evolution_level * 10
    gold_gain = defender.identity.evolution_level * 5
elif defender.identity.role == EntityRole.HERO:
    xp_gain = defender.identity.evolution_level * 20
    gold_gain = defender.identity.evolution_level * 50
```

With:
```python
from src.engine.combat_rewards import CombatRewardClassificationService
classification = CombatRewardClassificationService.classify(defender.identity.role)
xp_gain = defender.identity.evolution_level * classification.xp_multiplier
gold_gain = defender.identity.evolution_level * classification.gold_multiplier
```

Add to `full_trace`:
```python
full_trace["REWARD_SOURCE"] = classification.source
```

### 2d — AoE (resolve_aoe_attack)

**Not touched.** AoE uses hardcoded `evolution_level * 10` / `* 5` with no role check. This is a separate architectural gap — excluded from this ticket per scope decision.

---

## Step 3 — Add tests

Create `tests/unit/combat/test_combat_rewards.py` per test_plan.md.

Five unit tests for `CombatRewardClassificationService.classify()`:
1. `test_monster_role_classify`
2. `test_hero_role_classify`
3. `test_unknown_role_returns_none_category`
4. `test_classification_carries_source_string`
5. `test_classification_is_frozen_dataclass`

---

## Step 4 — Parity ledger updates

No parity entry `status` needs to change — COMB-279, COMB-280, PROG-004, PROG-064 are already `verified`/`legacy_verified`. However, update `v2_evidence` for PROG-064 and COMB-280 to reference the new service and test path:

- **PROG-064**: add `v2_evidence` reference to `src/engine/combat_rewards.py` and `tests/unit/combat/test_combat_rewards.py`.
- **COMB-280**: add `test_path` pointing to `tests/unit/combat/test_combat_rewards.py`.

---

## Files changed

| File | Change |
|---|---|
| `src/engine/combat_rewards.py` | New file |
| `src/engine/combat.py` | Replace 3 reward check sites (lines ~175, ~277, ~383) |
| `tests/unit/combat/test_combat_rewards.py` | New file, 5 tests |
| `docs/parity_ledger/combat_movement.yaml` | Update COMB-280 test_path |
| `docs/parity_ledger/progression.yaml` | Update PROG-064 v2_evidence and test_path |

---

## Unresolved questions

None.
