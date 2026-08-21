---
status: active
layer: engine
authority: P1
audience: developer
---

# Bounded Concurrency Contract

## Purpose
This contract establishes the finished law for engine concurrency. It ensures that parallel execution is as trustworthy as local execution by enforcing explicit packet/result protocols and a frozen deterministic commit order.

## Scope
This contract covers the transition of the concurrency layer from a prototype to a trustworthy model. It does NOT include distributed orchestration or gameplay changes.

## 1. Worker Packet Law
- **Identity**: Every packet must have an identifier `f"{tick}:{ordinal}"`.
- **Read-Only Input**: `WorkerPacket` contents (`subject` and `neighbor_view`) are read-only snapshots. Workers MUST NOT mutate them in place.
- **Canonical Context**: `neighbor_view` MUST be provided as a `List[Tuple[int, EntityState]]`, sorted ascending by `entity_id`.

## 2. Worker Result Law (Option A)
- **One-Result-Per-Entity**: Exactly one `WorkerResult` is allowed per entity per tick.
- **Identity Matching**: Every result must carry a `source_packet_id` matching its originating packet.
- **Structured Status**: Results must indicate `SUCCESS`, `FAILURE`, or `TIMEOUT`.

## 3. Deterministic Commit Law
- **Frozen Commit Key**: Results are authoritatively applied in a stable order defined by:
  1. `class_priority` (Explicit contract mapping)
  2. `local_priority` (Default 0, lower is earlier)
  3. `entity_id` (Ascending)
- **Priority Mapping**:
  - `CRITICAL`: 0 (Authoritative entity actions)
  - `PERIODIC`: 10 (Authoritative up-keep tasks)
  - `OPPORTUNISTIC`: 20 (Non-authoritative/Observational tasks)
  - `DEFERRED`: 30 (Postponed work items)
  (Lower value = Higher priority / Earlier commit)

## 4. Fallback and Failure Law
- **Failure-to-No-Op**: A worker failure (exception, timeout, or invalid status) results in a deterministic **authoritative no-op**.
- **Slot Consumption**: A failed result consumes the entity's single allow result slot for that tick. No retries are permitted within the same tick.
- **Fallback Equivalence**: Synchronous local execution (fallback) MUST enter the same collection and sorting path as concurrent execution to ensure semantic identity.

## 5. Concurrency Bounds
- **Max Workers**: Profile-controlled.
- **Queue Depth**: Profile-controlled.
- **Inflight Limit**: Profile-controlled.
- **Saturation**: If queue is full, the engine MUST fall back to local execution for remaining items in that batch, maintaining the same commit order.

### 5.1 Why `concurrency_limit` Decreases as `RuntimeMode` Escalates
`GovernorPolicy.from_mode()` (`src/engine/policy.py:70,91,112,133`) sets `concurrency_limit`
to 1.0 for NORMAL, 1.0 for CONSTRAINED, 0.5 for DEGRADED, and 0.25 for SURVIVAL — the active
worker pool *shrinks* as pressure rises. This is not self-evidently correct: naively, more
pressure might suggest more parallel workers to clear a backlog faster. It does the opposite
because concurrency is the last lever pulled, not the first, and by the time it is throttled
every earlier lever has already shrunk the batch being dispatched:

- **Phase budgets** (`PhaseBudgetGovernor.evaluate()`, `src/engine/phase_governor.py`) cut
  `candidate_budget`/`strategic_budget`/`movement_budget` and tighten `scan_policy`
  (FULL → THROTTLED → EXACT_DIRTY) as `RuntimeMode` escalates — e.g. `candidate_budget` goes
  1000 → 500 → 200 → 50 across NORMAL → CONSTRAINED → DEGRADED → SURVIVAL.
- **Cadence gating** (`SystemCadence`, `src/engine/cadence.py`) staggers how often
  per-entity/global subsystems re-evaluate at all (`should_run()`); cadence intervals widen
  as `RuntimeMode` escalates (e.g. `strategic_intelligence` runs every 10 ticks in NORMAL,
  every 100 in SURVIVAL).
- **Scheduling** (`DeterministicScheduler.select_work()`, `src/engine/scheduler.py`) filters
  candidates through readiness gating, LOD (`LODService.should_execute`, `src/engine/lod.py`
  — entities far from focus points skip), and the cadence gate above, before any work item is
  handed to the executor.

By the time `WorkerManager.execute_batch()` (`src/engine/worker_manager.py`) applies
`concurrency_limit` to compute `effective_cap`, the batch it is dispatching is already smaller
under pressure than it was in NORMAL. A smaller worker pool applied to an already-smaller batch
reduces thread/IPC contention rather than adding scheduling noise to an already-stressed system.
This rationale does not apply to `docs/engine/contracts/resource_governor_contract.md`, which
explicitly disclaims concurrency/worker-pool scaling as a Non-Goal — the Resource Governor only
decides `RuntimeMode`; this contract's worker pool is what consumes it.

## Non-Goals
- No distributed topology or external message brokers.
- No mid-tick result-to-result dependencies (beyond neighbor views).
