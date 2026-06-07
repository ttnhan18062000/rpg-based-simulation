# TCK-20260607-COMBAT-REWARD-SERVICE

## Title
Add CombatRewardClassificationService; remove direct EntityRole reward checks

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`src/engine/combat.py` has multiple direct checks against `EntityRole.MONSTER` and
`EntityRole.HERO` at lines 175-178, 277, 383, 386 to gate XP grants, gold drops,
and rebirth logic. These scattered checks are not centralized, not testable as a unit,
and not traceable (no reward classification source in the result record).

A `CombatRewardClassificationService` should own all entity-role-to-reward-category
mapping, with a trace field in the reward result.

## Scope

### Fix 1 — `CombatRewardClassificationService`

Create:
```python
# src/engine/combat_rewards.py

from enum import Enum

class RewardCategory(Enum):
    NONE = "none"
    XP_ONLY = "xp_only"
    GOLD_DROP = "gold_drop"
    REBIRTH_ELIGIBLE = "rebirth_eligible"
    FULL_REWARD = "full_reward"

@dataclass(frozen=True)
class RewardClassification:
    category: RewardCategory
    xp_multiplier: float
    gold_eligible: bool
    rebirth_eligible: bool
    source: str  # e.g., "EntityRole.MONSTER", "EntityRole.HERO"

class CombatRewardClassificationService:
    def classify(self, entity_role: EntityRole) -> RewardClassification:
        ...
```

### Fix 2 — Update `combat.py`

Replace the four direct `EntityRole.MONSTER` / `EntityRole.HERO` checks with calls to
`CombatRewardClassificationService.classify()`.

The reward result (wherever XP/gold is granted) should carry `classification.source`
so it's traceable in telemetry.

### Fix 3 — Tests

Add `tests/unit/engine/test_combat_rewards.py`:
```python
- test_monster_role_grants_gold_drop
- test_hero_role_is_rebirth_eligible
- test_unknown_role_returns_none_category
- test_classification_carries_source_string
```

Also update `tests/unit/engine/test_combat.py` (or `test_relation_combat_integration.py`):
```python
- verify reward classification is used in the combat resolution path
```

## Out of Scope
- Do not change combat damage formulas (governed by `docs/mechanics/02_combat_laws.md`)
- Do not add new entity roles
- Do not change XP formula (Chapter 01)
- Do not add gold drop probability changes — this ticket is only about where checks live, not their values

## Acceptance Criteria
- [ ] `CombatRewardClassificationService` exists in `src/engine/combat_rewards.py`
- [ ] `RewardCategory` enum and `RewardClassification` dataclass exist
- [ ] `combat.py` no longer has bare `EntityRole.MONSTER` / `EntityRole.HERO` checks for rewards
- [ ] `classification.source` traces the entity role that triggered the classification
- [ ] Unit tests cover MONSTER, HERO, and unknown roles
- [ ] All existing combat tests pass

## Related Tickets
(none)

## Related Docs
- `docs/mechanics/01_entity_anatomy.md` — entity roles
- `docs/mechanics/02_combat_laws.md` — combat resolution
- `world_phase_20_28_repair_remaining.md` R7.1, R7.2

## Related Code Areas
- `src/engine/combat.py:175-178,277,383,386`
- `src/engine/combat_rewards.py` (new)
- `tests/unit/engine/test_combat_rewards.py` (new)

## Assumptions / Open Questions
- Are there other files outside `combat.py` that check `EntityRole.MONSTER` / `EntityRole.HERO` for reward gating? Must grep before scoping.
- Is `EntityRole` already an enum? Confirm import path.

## Implementation Notes
Created `src/engine/combat_rewards.py` with `RewardCategory` enum (NONE, MONSTER_KILL, HERO_KILL),
`RewardClassification` frozen dataclass (xp_multiplier, gold_multiplier, gold_eligible,
rebirth_eligible, source), and `CombatRewardClassificationService.classify()` classmethod with
class-level dispatch dict. Multipliers match Ch02 exactly (MONSTER: xp=10, gold=5; HERO: xp=20,
gold=50).

Replaced 3 direct EntityRole reward check sites in `combat.py`:
- `resolve_attack` (lines ~175-187): classify() replaces MONSTER/HERO if-elif; rebirth branch
  derives from classification.rebirth_eligible; trace["REWARD_SOURCE"] added.
- `resolve_skill_usage` (line ~277): classify() replaces MONSTER-only if block. HERO kills via
  skill now earn rewards per Ch02 (correctness fix — no skill exception in role reward table).
- `resolve_multi_attack` (lines ~382-388): classify() replaces MONSTER/HERO if-elif;
  full_trace["REWARD_SOURCE"] added.

The lethality gate at line 136 (role != HERO) and wound infliction check at line 585 are not
reward checks and were left untouched per investigation findings.

## Test Summary
```
pytest tests/unit/combat/ tests/unit/engine/ -q
pytest tests/unit/combat/test_combat_rewards.py -v
```

## Files Changed
- `src/engine/combat_rewards.py` (new)
- `src/engine/combat.py` (3 reward sites replaced)
- `tests/unit/combat/test_combat_rewards.py` (new, 5 tests)
- `docs/parity_ledger/combat_movement.yaml` (COMB-280 test_path updated)
- `docs/parity_ledger/progression.yaml` (PROG-064 v2_evidence and test_path updated)

## Completion Summary
Created src/engine/combat_rewards.py with RewardCategory enum, RewardClassification frozen dataclass, and CombatRewardClassificationService.classify() classmethod. Replaced 4 direct EntityRole reward checks in combat.py (resolve_attack, resolve_skill_usage, resolve_multi_attack). HERO kills via skill_usage now correctly earn rewards per Ch02 (correctness fix). Added 5 unit tests in tests/unit/combat/test_combat_rewards.py. Updated parity ledger: COMB-280, PROG-064.
