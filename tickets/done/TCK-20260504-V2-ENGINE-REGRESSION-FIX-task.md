# Task List - TCK-20260504-V2-ENGINE-REGRESSION-FIX

- [ ] Harden `V2EntityBuilder` with missing navigation/stamina methods.
- [ ] Refactor `EntityGenerator` in `src/systems/generator.py` to use `V2EntityBuilder`.
- [ ] Verify fix for `test_phase9_stability.py`.
- [ ] Systematic audit and fix for remaining 38 failures in `tests/engine/`.
  - [ ] `test_race_conditions_v2.py`
  - [ ] `test_reputation_learning.py`
  - [ ] `test_routine_biasing.py`
  - [ ] `test_runtime_state_contract.py`
  - [ ] `test_signal_hardening.py`
  - [ ] ... others ...
- [ ] Final verification of all tests in `tests/engine/`.

**Tier:** standard
**Type:** chore
**Priority:** P1
