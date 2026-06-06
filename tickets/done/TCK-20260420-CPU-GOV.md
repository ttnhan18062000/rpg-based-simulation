# TCK-20260420-CPU-GOV

## Title
End-to-End CPU Resource Contract

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Wire the Governor's concurrency limit through the Kernel/Executor into the WorkerManager to ensure proactive shedding.

## Scope
- Extend `IWorkExecutor` with `set_concurrency_limit`.
- Propagate limits from `Kernel._current_policy` during the TICK phase.
- Verify batch throttling in `WorkerManager`.

## Acceptance Criteria
- [x] Governor policy limits are enforced by the executor.
- [x] 100% pass on certification scenarios.

## Completion Summary
Propagated authoritative CPU contracts from policy evaluation to hardware enforcement.
