# Test Plan - TCK-20260508-ECON-PIPELINE-FIX

## Target
Restore regression suite pass rate to 100%.

## Automated Tests
1. `pytest tests/unit/test_interaction_system.py`
2. `pytest tests/verify/test_recovery_gaps.py`
3. `pytest tests/engine/test_transaction_grouping.py`
4. `pytest tests -k "not (test_long_run_determinism.py or test_long_run_stability.py)"`

## Verification Criteria
- All 101 currently failing tests must pass.
- `EntityUpdate.intent_results` must contain one result per `resource_transfer` intent.
- `WorldDynamicsSystem` must correctly apply hazard damage (verified by `test_regional_hazard_impact`).
