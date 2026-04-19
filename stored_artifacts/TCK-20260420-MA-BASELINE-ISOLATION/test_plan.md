# Test Plan - Milestone A Isolation (TCK-20260420-MA-BASELINE-ISOLATION)

## 1. Unit Tests
- `tests_v2/engine/test_local_executor.py`: (NEW) Verify that `LocalSequentialExecutor` correctly executes `ENTITY_MOVE` and `ENTITY_ACT` without packets.
- `tests_v2/engine/test_executor_adapter.py`: (NEW) Verify that `ConcurrentExecutionAdapter` correctly builds packets and uses `WorkerManager`.

## 2. Milestone Closure Verification
- `tests_v2/engine/test_milestone_a_closure.py`: Verify that the kernel can COMPLETE a tick using `LocalSequentialExecutor` even if the `WorkerManager` is disabled or not initialized.

## 3. Deterministic Equivalence
- `tests_v2/engine/test_determinism_suite.py`:
  - Run Scenario `A` with `LocalSequentialExecutor`.
  - Run Scenario `A` with `ConcurrentExecutionAdapter` (Single worker).
  - Assert `final_hash_a == final_hash_b`.
