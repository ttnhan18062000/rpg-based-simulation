---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: c6306454-56e4-4a14-b03f-7fc75ea22c2d
artifact_type: test_plan
tags: [c6306454, 56e4, 4a14, b03f, 7fc75ea22c2d]
---

# Test Plan - Tactical Combat Hardening

## Objectives
- Verify that `resolve_multi_attack` applies the same tactical bonuses as `resolve_attack`.
- Ensure that bracketing (flanking) bonuses require active attackers.
- Prevent regression in existing single-attack tactical logic.

## Strategy
1.  **Unit Testing**:
    - Update `test_bracketing_bonus_requires_active_attackers` to assert specific damage values that include the flanking bonus (1.15x multiplier).
    - Add `test_bracketing_bonus_ignores_inactive_entities` to verify that dead/inactive entities do not trigger flanking geometry.
2.  **Regression Testing**:
    - Run the full engine test suite (`tests/engine`) to ensure that refactoring `combat.py` did not break other systems.
3.  **Trace Verification**:
    - Check the `trace` dictionary in `CombatUpdate` for correct bonus attribution (e.g., `2_FLANKING`, `3_FLANKING`).

## Success Criteria
- 100% pass rate in `tests/tactical/test_bracketing_bonus.py`.
- 100% pass rate in `tests/engine` (excluding explicitly skipped long-run tests).
