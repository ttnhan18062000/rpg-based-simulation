# TCK-20260607-COMBAT-REWARD-SERVICE

## Title
Add CombatRewardClassificationService; remove direct EntityRole reward checks

## Status
OPEN

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
P3 — can be implemented after P1 (TCK-20260607-PATH-DRIFT-SRC) and P2 tickets. Investigation must grep for all `EntityRole.MONSTER` reward checks across the codebase first.

## Test Summary
```
pytest tests/unit/engine/ -q
```

## Files Changed
- `src/engine/combat.py`
- `src/engine/combat_rewards.py` (new)
- `tests/unit/engine/test_combat_rewards.py` (new)

## Completion Summary
(to be filled)
