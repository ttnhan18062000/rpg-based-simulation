---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260420-MA-BASELINE-ISOLATION
artifact_type: plan
tags: [ma, baseline, isolation]
---

# Plan - Milestone A Isolation (TCK-20260420-MA-BASELINE-ISOLATION)

## Goal
Decouple the single-process semantic baseline from worker protocols to satisfy Milestone A requirements.

## Proposed Changes
1. **Define Interface**: Create `src/engine/executor.py` with `IWorkExecutor`.
2. **Local Path**: Implement `LocalSequentialExecutor` using direct domain-logic calls.
3. **Concurrent Path**: Refactor existing `Kernel` loop into `ConcurrentExecutionAdapter`.
4. **Injection**: Update `Kernel.__init__` to accept and use the executor.

## Verification
- Run `test_milestone_a_closure.py` which must now pass WITHOUT initializing a `WorkerManager`.
- Run `test_determinism_suite.py` to ensure bit-identical results between local and concurrent paths.
