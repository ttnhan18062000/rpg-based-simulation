# Plan: V2 Test Hardening

## Goal
Refactor legacy engine tests to the V2 architecture to ensure consistency with the `AuthoritativeApplyPipeline` and `V2EntityBuilder` API.

## Strategy
1. **API Migration**: Replace all direct `EntityState` constructor calls with `V2EntityBuilder`.
2. **Readiness Alignment**: Ensure all test entities have `readiness=100.0` before attempting actions, satisfying the "Action Readiness Law".
3. **Logic Parity**: Adjust test assertions to reflect V2-specific mechanics (e.g., movement mode multipliers).
4. **Determinism Verification**: Use `transaction_trace` to verify that the engine correctly logs rejections and successes.

## Targeted Files
- `tests/engine/test_executor_parity.py`
- `tests/engine/test_local_executor.py`
- `tests/engine/test_migration_proof.py`
- `tests/engine/test_worker_determinism.py`
- `tests/engine/test_worker_adaptation.py`
- `tests/engine/test_read_only_guard.py`
- `tests/engine/test_replay_determinism.py`
