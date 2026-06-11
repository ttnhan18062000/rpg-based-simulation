---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260426-FIX-PARITY-REGRESSIONS
artifact_type: test_plan
tags: [fix, parity, regressions]
---

# Test Plan: Parity Regressions

## Automated Verification
1.  **Parity Tests**:
    - `pytest tests/parity/test_parity_rpg_recovery.py`
    - `pytest tests/parity/test_parity_rpg_combat.py`
2.  **Full Suite**:
    - `pytest tests/` (Target: 100% pass, ignoring 2 skips).

## Manual Verification
- None required (logic-only fix).
