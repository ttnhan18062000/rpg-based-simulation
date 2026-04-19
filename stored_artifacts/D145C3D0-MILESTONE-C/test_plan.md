# Test Plan: Milestone C - Operational Integrity

## Strategy
Verifying that the engine's lifecycle and persistence layers obey the **Operational Integrity Contract (MC)**. We will use `pytest` to run existing suites and add new tests for integrity-critical logic.

## Coverage Checklist

### 1. Replay Lifecycle
- [ ] **test_replay_is_non_authoritative**: Sink failure does not stop kernel.
- [ ] **test_replay_order_preservation**: Trace events on disk match emission order.
- [ ] **test_replay_overflow**: Buffer respects capacity and evicts oldest items.
- [ ] **test_manifest_integrity (NEW)**: Verify atomic write-rename of `manifest.json`.

### 2. Startup & Flags
- [ ] **test_too_low_budget_rejection**: Profile with <1ms budget is rejected.
- [ ] **test_contradictory_flags**: Mutually exclusive flags (SURVIVAL + REPLAY) rejected.
- [ ] **test_forbidden_flag**: `BYPASS_GOVERNOR` is rejected.

### 3. Shutdown & Snapshots
- [ ] **test_shutdown_skips_rotation_on_low_budget**: Finalize aborts if near 5s limit.
- [ ] **test_shutdown_performs_rotation_on_ample_budget**: Finalize succeeds if time permits.
- [ ] **test_graceful_shutdown**: Kernel shutdown stops all producers.

## Execution Sequence
1. Run all existing configuration and engine tests.
2. Implement `test_manifest_integrity.py`.
3. Verify all tests pass with `PYTHONPATH=. pytest`.
