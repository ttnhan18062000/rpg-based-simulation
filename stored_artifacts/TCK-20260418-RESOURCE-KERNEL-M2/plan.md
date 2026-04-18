# Implementation Plan: Resource-Safe Engine Milestone 2

## Purpose
Build the minimal runnable kernel with deterministic single-thread execution.

## Proposed Changes
1. **Documentation**: `minimal_kernel_m2.md`, `m2_test_matrix.md`.
2. **Core Types**: `StateUpdate`, `ActionProposal`. Add `world_time` to `AuthoritativeState`.
3. **Logic**: `ApplyPath` (generation-based), `Kernel.tick_once()`.
4. **Determinism**: `CheckpointService` (canonical hashing).

## Task List
- [ ] Draft docs
- [ ] Implement `updates.py` and state extensions
- [ ] Implement `apply.py`
- [ ] Implement `checkpoint.py`
- [ ] Upgrade `kernel.py`
- [ ] Write `tests_v2/`
- [ ] Verify determinism
