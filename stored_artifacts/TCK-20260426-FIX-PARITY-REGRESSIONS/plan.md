---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260426-FIX-PARITY-REGRESSIONS
artifact_type: plan
tags: [fix, parity, regressions]
---

# Plan: Fix Parity Regressions

## Proposed Changes

### Engine
#### [MODIFY] `src/engine/evolution.py`
- Import `RewardUpdate`.
- Update `evaluate` to sum XP gain from `RewardUpdate` into the proposed delta.

#### [MODIFY] `src/engine/pipeline.py`
- Update `_refine_step` to merge readiness updates using `min(existing, new)` to ensure we stay within the brain's budget.

### Tests
#### [MODIFY] `tests/parity/test_parity_rpg_recovery.py`
- Adjust XP assertion to expect 10 XP remaining (990 + 10 - 1000 = 10).
