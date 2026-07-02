---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260702-OBSISO-TRACE-ASYNC
phase: open
date: 2026-07-02
tags: [observability, decision-trace, hot-path, performance, contract-compliance]
---

# TCK-20260702-OBSISO-TRACE-ASYNC

## Title
Move DecisionTraceWriter file IO off the simulation hot path

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`DecisionTraceWriter.write_trace()` performs a synchronous `file.write()` + `flush()` per entity per tick (`src/observability/cognition/decision_trace_writer.py:128-129`) and is invoked from inside the adventure decision phase (`src/domains/adventure/phase.py:20` via `get_active_writer()`). Direct file IO inside a simulation phase is forbidden by `docs/architecture/observability_hot_path_safety_contract.md` §3. The writer shipped with E22 (TCK-20260619-E22A) before this was scrutinized. Refactor so the hot path only appends trace records to a bounded in-memory structure; file IO happens on an async worker, following the established `BoundedObservabilityQueue`/`QueueDrainWorker` pattern.

## Scope
- Hot path: `write_trace()` becomes an in-memory append (bounded buffer or dedicated bounded queue) — no `open()`, no `write()`, no `flush()` inside any phase.
- Async sink: drain buffered records to `decision_trace.jsonl` on a background worker (reuse/extend `QueueDrainWorker` or a dedicated writer thread following the same lifecycle contract §6 — singleton/shutdown/test-teardown rules).
- Preserve the live read-back: `get_latest_goal_scores()` (consumed by `src/observability/live/entity_inspector.py:142`) must keep returning the most recent top-3 goal scores from an in-memory cache regardless of flush state.
- Preserve crash-recovery semantics from `docs/observability/decision_trace_contract.md`: tick-index sidecar written incrementally, rebuilt on close; on unclean shutdown, already-drained records must be recoverable. Document any weakening (e.g., last-N-ticks loss window on crash) in the contract and `docs/guidelines/v2_intentional_divergences.md` if behavior observably changes.
- Kernel shutdown ordering: `Kernel.shutdown()` must flush and close the trace sink after final tick, before run finalization.
- Update `docs/observability/decision_trace_contract.md` (write-path section) and add/update the parity ledger entry in `docs/parity_ledger/infrastructure.yaml`.

## Out of Scope
- Any change to trace record schema or REST endpoints (`src/api/routes/decisions.py`)
- P1-H goal-layer runner-up retention (separate concern, `docs/plans/audit_fix_plan.md`)
- Intention-log ring buffer or other read-side features

## Acceptance Criteria
- Static check: no file IO calls reachable from `write_trace()` on the phase call path (grep/AST assertion in test).
- `tests/unit/observability/test_decision_trace.py` updated and passing: records written during a run appear in `decision_trace.jsonl` after shutdown; tick-index lookup still O(1); `get_latest_goal_scores()` returns current values mid-run before any flush.
- Entity inspector integration unaffected: existing `test_entity_inspector.py` passes unchanged.
- Determinism: two same-seed runs produce identical `decision_trace.jsonl` content (ordering included).
- Worker lifecycle: conftest worker-thread sentinel does not trip; `shutdown()` idempotent.

## Related Tickets
TCK-20260619-E22A (original writer), TCK-20260619-E22B (tick index), TCK-20260702-OBSISO-EPIC

## Related Docs
docs/architecture/observability_hot_path_safety_contract.md (§2, §3, §6), docs/observability/decision_trace_contract.md, docs/plans/observability_process_isolation.md (G4)

## Related Stored Artifacts
stored_artifacts/TCK-20260619-E22A*, stored_artifacts/TCK-20260619-E22B*

## Related Code Areas
src/observability/cognition/decision_trace_writer.py, src/observability/cognition/tick_index.py, src/domains/adventure/phase.py, src/observability/queue.py, src/observability/live/entity_inspector.py, src/engine/kernel.py (writer init/close, lines ~288-293, ~981-986)

## Assumptions / Open Questions
- Assume per-tick flush is not a hard requirement of the trace contract (it was an implementation choice); crash-loss window of the in-flight buffer is acceptable if documented. If the contract owner disagrees, fall back to batched fsync every N ticks off-path.

## Implementation Notes
The in-memory latest-scores cache already exists in the writer (populated on `write_trace`); keep it hot-path-side. Only the serialization + disk write moves to the worker. Contract §2 explicitly whitelists bounded in-memory appends, so the buffer itself is compliant.

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
