# Test Plan: Phase 2 Performance Regression Fixes

## Automated Tests
- Run `pytest tests/unit` to verify all 82 regressions are fixed. Specifically monitor:
  - `tests/unit/combat/test_rpg_core_recovery.py`
  - `tests/unit/social/test_contracts.py`
  - `tests/unit/core/test_domain_6_hardening.py`
  - `tests/unit/core/test_rpg_depth.py`
  - `tests/unit/core/test_migration_proof.py`
- Run `pytest tests/perf` to ensure performance parity is maintained.

## Verification
- Confirm 0 failures across the unit test suite.
