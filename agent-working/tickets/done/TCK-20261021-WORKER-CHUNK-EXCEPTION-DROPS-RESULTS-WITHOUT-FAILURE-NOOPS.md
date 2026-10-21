---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261021-WORKER-CHUNK-EXCEPTION-DROPS-RESULTS-WITHOUT-FAILURE-NOOPS
phase: done
date: 2026-10-21
tags: []
---

# TCK-20261021-WORKER-CHUNK-EXCEPTION-DROPS-RESULTS-WITHOUT-FAILURE-NOOPS

## Title
When a worker chunk future raises, that chunk's results are dropped with no per-entity FAILURE no-ops, which the contract requires, and future.result() has no timeout path

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lead-planner-u24 found this on 2026-10-21 by reading the code on origin/main; it was not run. It does not block v1.
- worker_manager.py, around line 176: a chunk future that raises drops that chunk's results without the per-entity FAILURE no-ops the contract requires.
- future.result() has no timeout path. (Ruled, see Implementation Notes: it stays without one.)

## Scope
- On a chunk exception or timeout, emit one typed FAILURE no-op per entity in the chunk, so the tick stays deterministic and auditable.
- (Narrowed by rpg-planner's ruling, 2026-10-21: no timeout is added. `future.result()` stays untimed; the contract is documented to say so.)
- Tests: a raising chunk gives FAILURE no-ops for exactly its entities; the other chunks still commit; the result order is unchanged.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The contract's FAILURE no-op rule holds on a chunk exception, with tests. (The timeout half is dropped by ruling.)

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/worker_manager.py (~L176), the worker failure contract in docs/engine/

## Assumptions / Open Questions
- This was read from code, not reproduced. Re-verify it before any fix.

## Implementation Notes
- Verified by reading origin/main 735a1c635: `execute_batch` collected `future.result()` bare and, on an exception, logged and dropped the chunk's results; `_wrap_work` and `_process_chunk_wrapper` already turned an error inside ONE packet into a FAILURE no-op, so only a chunk that raises as a whole lost results.
- The "existing config" timeout does not exist: no worker/chunk/result/future timeout in src, config or docs/engine; RuntimeProfile has no timeout field; the only candidate, `max_tick_budget_ms`, is report-only (TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY) because a wall-clock decision makes the result host-speed dependent.
- Options put to rpg-planner: (a) a new profile field (a new knob), (b) a timeout that fires only outside audit_mode (two behaviours by mode), (c) no timeout in the commit path. Ruled (c) by rpg-planner on 2026-10-21: a hung chunk is liveness, the watchdog's job (docs/architecture/simulation_watchdog.md). Narrowing this ticket's Scope and Acceptance Criteria is that ruling, not a gate workaround. The contract's TIMEOUT status stays a named, unused value.
- Fix: module-level `failure_no_op(packet)` (the existing per-packet FAILURE shape, now one function used by `_wrap_work`, `_process_chunk_wrapper` and the new path); `execute_batch` keeps each future with its chunk and, when a chunk raises, extends the results with `failure_no_op(p)` for each packet in the chunk, in packet order. No new status or result type was needed.
- Contract §4 documents the chunk failure rule and the no-timeout decision; parity INFRA-437.
- Determinism: the rpg gate runs build their kernel with an injected `LocalSequentialExecutor` (tools/test_architecture/rpg_gate_run.py `build_kernel`), so they never reach `WorkerManager.execute_batch` (PROD_SMALL still has max_worker_count=2, but the pool is unused); no hash check is needed. A normal run raises no chunk, so nothing changes for a concurrent run either.

## Test Summary
tests/unit/engine/test_worker_chunk_exception_becomes_failure_no_ops.py (7): a raising chunk gives FAILURE no-ops for exactly its entities (3,4 of 8) while the other chunks commit; the no-op is an empty update with the packet's ids; result order is submission order with or without a failed chunk; an unchanged run stays all SUCCESS; failing-chunk patterns keep one result per entity. 6 of 7 fail on the old behaviour. With test_worker_capacity_semantics, test_worker_bounds, test_executor_parity, test_worker_adaptation, test_fallback_hardening: 35 passed, serial, 69 MB.

## Files Changed
src/engine/worker_manager.py, docs/engine/contracts/bounded_concurrency_contract.md (§4), docs/parity_ledger/infrastructure.yaml (INFRA-437), tests/unit/engine/test_worker_chunk_exception_becomes_failure_no_ops.py

## Completion Summary
A pooled chunk that raises now yields one FAILURE no-op per packet of that chunk; there is no timeout in the commit path (ruled), documented in contract §4. No simulation hash check needed (gate runs use the sequential executor).
