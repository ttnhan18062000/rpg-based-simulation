# Test Plan: Parity Regressions

## Automated Verification
1.  **Parity Tests**:
    - `pytest tests/parity/test_parity_rpg_recovery.py`
    - `pytest tests/parity/test_parity_rpg_combat.py`
2.  **Full Suite**:
    - `pytest tests/` (Target: 100% pass, ignoring 2 skips).

## Manual Verification
- None required (logic-only fix).
