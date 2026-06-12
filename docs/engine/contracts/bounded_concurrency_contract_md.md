---
status: active
layer: engine
authority: P1
audience: developer
---

# Bounded Concurrency Contract - [Milestone D]

## Purpose
This contract establishes the "Finished Law" for v2 engine concurrency. It ensures that parallel execution is as trustworthy as local execution by enforcing explicit packet/result protocols and a frozen deterministic commit order.

## Scope
Milestone D covers the transition of the concurrency layer from a prototype to a trustworthy model. It does NOT include distributed orchestration or gameplay changes.

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

## Non-Goals
- No distributed topology or external message brokers.
- No mid-tick result-to-result dependencies (beyond neighbor views).
