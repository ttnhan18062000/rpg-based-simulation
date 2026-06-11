---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260504-V2-ENGINE-REGRESSION-FIX
artifact_type: test_plan
tags: [v2, engine, regression, fix]
---

# Test Plan - TCK-20260504-V2-ENGINE-REGRESSION-FIX

## Regression Testing
- Primary indicator of success: `pytest tests/engine/` returning 100% pass rate.
- Secondary check: `pytest tests/rpg/` to ensure world dynamics and logic remain sound.

## Target Tests
All tests currently failing in `tests/engine/`, including:
- `test_phase9_stability.py`
- `test_race_conditions_v2.py`
- `test_reputation_learning.py`
- `test_routine_biasing.py`
- `test_runtime_state_contract.py`
- `test_signal_hardening.py`
- ... and others as reported by the initial `pytest` run.

## Verification Steps
1. Apply `V2EntityBuilder` enhancements.
2. Refactor `EntityGenerator`.
3. Run `pytest tests/engine/test_phase9_stability.py` (Verify first fix).
4. Run full suite `pytest tests/engine/`.
5. Fix any remaining `TypeError` or logic discrepancies in specific test files.
