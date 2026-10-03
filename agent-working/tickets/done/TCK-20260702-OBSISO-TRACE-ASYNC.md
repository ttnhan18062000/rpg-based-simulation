---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260702-OBSISO-TRACE-ASYNC
phase: done
date: 2026-07-02
tags: [observability, decision-trace, hot-path, performance, contract-compliance]
---

# TCK-20260702-OBSISO-TRACE-ASYNC

## Title
Move DecisionTraceWriter file IO off the simulation hot path

## Status
DONE

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
Implemented per `staging_artifacts/TCK-20260702-OBSISO-TRACE-ASYNC/plan.md`'s 12 steps, in the
plan's dependency order. No deviations from the plan's code shapes; two additions beyond the 12
steps were required and are recorded below.

- **Step 1**: `DecisionTraceWriter` now owns a private `BoundedObservabilityQueue`/
  `QueueDrainWorker` pair (per-instance pattern, matching `EventRecorder`, not the global
  singleton), sized via `ObservabilityConfig.get_max_queue_size()`. Added the
  `_DecisionTraceQueueItem` dataclass wrapper (hardcoded `severity="INFO"`) so
  `BoundedObservabilityQueue.try_push()`'s overflow path doesn't `AttributeError` on a bare dict.
  `write_trace()` now only builds `entry`, updates `_latest_goal_scores` (unchanged, hot-path-side),
  and calls `self._queue.try_push(...)` — no `open()`/`write()`/`flush()`/`append_entry()` left in
  its body. The actual disk write + `DecisionTraceIndex.append_entry()` call moved into a new
  `_write_entry_to_file()` method, dispatched by the worker.
- **Step 2**: `tick_index.py` — docstring-only changes (module docstring + `append_entry()`
  docstring) describing the new caller (the drain worker) instead of `write_trace()`. Zero logic
  changes; `append_entry()`, `_flush()`, `rebuild()`, `lookup()`, `_load()` bodies untouched.
- **Step 3**: `close()` rewritten to the 4-step sequence: `_worker.stop()` → synchronous
  `self._queue.drain()` + `_write_entry_to_file()` per remaining item → close `self._file` → the
  existing `self._index.rebuild()`. Idempotency relies on existing primitives (`QueueDrainWorker.stop()`
  no-ops on a null thread, `drain()` returns `[]` once empty) — no new "already closed" flag added.
- **Step 4**: `kernel.py` — `_workers_started` changed from `1` to `2` (comment updated); added the
  missing `workers_stopped += 1` at the `DecisionTraceWriter.close()` shutdown site, unconditionally
  after the try/except (matching `EventRecorder`'s accounting three lines above it).
- **Step 5**: New `tests/architecture/test_decision_trace_hot_path_no_io.py` — AST-walks
  `write_trace()`'s own function body and asserts no `open`/`write`/`flush`/`dump` call and no
  `self._file`/`append_entry` attribute reference is reachable.
- **Step 6**: `test_decision_trace.py` — added 4 new tests (no-sync-IO proof, immediate
  `get_latest_goal_scores()` before flush, worker-thread-not-leaked-after-close, close() idempotent),
  rewrote `test_tick_index_incremental_vs_rebuild` to snapshot the incremental index state via a
  manual `_worker.stop()` + drain loop *before* calling `_index.rebuild()` separately (not two
  post-rebuild snapshots), and wrapped `test_set_and_get_active_writer` in `try/finally: writer.close()`
  so it no longer leaks a worker thread now that `__init__` always starts one.
- **Step 7**: `test_lifecycle_supervisor.py` — added
  `test_workers_started_counts_event_recorder_and_decision_trace_writer` asserting
  `_workers_started == 2`, `workers_started == workers_stopped == 2`, `outcome == "SUCCESS"`.
- **Step 8**: New `tests/integration/observability/test_decision_trace_determinism.py` — runs a
  real `Kernel` (hand-built minimal state + resource node + `ENABLE_ADVENTURE_ROUTING` flag, no
  full world compile needed) twice for 15 ticks into two separate run dirs, asserts
  `decision_trace.jsonl` content/order is byte-identical, and asserts `dropped_count == 0` on both
  writers' queues as the occupancy-headroom proof the determinism claim depends on (per the plan's
  Determinism caveat — not just output equality).
- **Step 9**: Added intentional-divergences entry §2.31 documenting both the crash-loss window
  (bounded by `interval_sec=0.01s`) and the queue-overflow-drop window (bounded by `max_size`),
  rationale class `Bounded`. Added
  `tests/unit/observability/test_decision_trace_divergence_doc.py` asserting the doc references
  this ticket ID and both window names.
- **Steps 10-12**: Updated `docs/observability/decision_trace_contract.md` (new "Async write path"
  paragraph in Implementation Notes, rewritten Tick Index Lifecycle section, new "Accepted
  Crash-Loss and Overflow-Drop Windows" subsection); updated `docs/parity_ledger/infrastructure.yaml`
  INFRA-211/INFRA-212 `v2_evidence`/`text` to describe the enqueue+async-drain split (status stays
  `verified`, no new IDs, `test_path`s re-verified passing before the edit); marked G4 resolved in
  `docs/plans/observability_process_isolation.md` with a cross-reference to this ticket, original
  gap text kept for history per the plan's scope guard (other gaps untouched).

**Deviation beyond the 12 steps (required, not scope creep):** running the full
`tests/integration/observability/` suite alongside `test_lifecycle_supervisor.py` surfaced a
genuine thread leak: `tests/integration/observability/test_initial_placement_check.py::test_check_initial_placement_mode_gating_matches_precedent`
exercises `Kernel.__init__` raising `HardLawViolationError` mid-construction (DEBUG/CERTIFICATION
fail-fast path) — `__init__` has no exception-safe teardown, so the test already reclaimed the
leaked `EventRecorder` via `gc.get_objects()` + `.shutdown()` (a pre-existing, documented gap).
Since `DecisionTraceWriter.__init__` now unconditionally starts a `QueueDrainWorker` too (Step 1),
that same construction path started leaking a second worker per fail-fast iteration (2 total,
matching the observed `_observability_worker_thread_sentinel` failure: "before=0, after=2").
Fixed by extending that test's `finally` gc-reclaim loop to also `.close()` any live
`DecisionTraceWriter` found via `gc.get_objects()`. This is a direct, unavoidable consequence of
Step 1's behavior change (a file outside the plan's originally-scoped list, but required to satisfy
AC #5 — the conftest worker-thread sentinel must not trip). Recorded as a Deviation in plan.md.

Verified via a clean `git worktree` checkout of pre-ticket `HEAD` that
`tests/integration/kernel/test_long_run_determinism.py::test_1000_tick_determinism` and the 2
`test_export_flow.py` failures (missing `pyarrow` optional dependency) are pre-existing and
unrelated to this change — same failures reproduce identically on unmodified `HEAD`.

## Test Summary
All ticket-scoped tests pass (58 total across the affected files, run together):
`tests/unit/observability/test_decision_trace.py` (28), `test_decision_trace_divergence_doc.py` (1),
`tests/architecture/test_decision_trace_hot_path_no_io.py` (2),
`tests/unit/engine/test_lifecycle_supervisor.py` (15),
`tests/integration/observability/test_decision_trace_determinism.py` (1),
`tests/integration/observability/test_initial_placement_check.py` (2),
`tests/unit/observability/test_entity_inspector.py` (9, AC #3 regression, unmodified and passing).
Also ran `tests/integration/observability/` (full dir) + `tests/integration/kernel/` +
`tests/unit/domains/adventure/` + `test_fused_loop.py` as broader regression: no new failures;
the only failures present (`test_export_flow.py` x2 — missing `pyarrow`;
`test_long_run_determinism.py::test_1000_tick_determinism` — pre-existing tick-budget/timeout
sensitivity in the `persistence` phase) are confirmed pre-existing on unmodified `HEAD` via a
throwaway `git worktree` comparison, not caused by this ticket.

## Files Changed
- `src/observability/cognition/decision_trace_writer.py`
- `src/observability/cognition/tick_index.py` (docstrings only)
- `src/engine/kernel.py`
- `tests/unit/observability/test_decision_trace.py`
- `tests/unit/engine/test_lifecycle_supervisor.py`
- `tests/integration/observability/test_initial_placement_check.py` (unplanned, required fix — see Implementation Notes)
- `tests/architecture/test_decision_trace_hot_path_no_io.py` (new)
- `tests/integration/observability/test_decision_trace_determinism.py` (new)
- `tests/unit/observability/test_decision_trace_divergence_doc.py` (new)
- `docs/observability/decision_trace_contract.md`
- `docs/parity_ledger/infrastructure.yaml`
- `docs/guidelines/intentional_divergences.md`
- `docs/plans/observability_process_isolation.md`

## Completion Summary
All 5 acceptance criteria met: (1) AC #1 — static AST guard proves no file I/O reachable from
`write_trace()`; (2) AC #2 — `test_decision_trace.py` updated/passing, tick-index lookup still
O(1) (unmodified `lookup()`/`append_entry()` bodies), `get_latest_goal_scores()` proven synchronous
pre-flush; (3) AC #3 — `test_entity_inspector.py` passes unmodified; (4) AC #4 — real two-run
`Kernel` determinism test passes with a `dropped_count == 0` occupancy proof, not just output
equality; (5) AC #5 — conftest worker-thread sentinel no longer trips (required one unplanned fix
in `test_initial_placement_check.py`, a direct and unavoidable consequence of Step 1's behavior
change), `close()`/`shutdown()` idempotent. `write_trace()` and the co-located
`DecisionTraceIndex.append_entry()` call are both fully off the `AdventureDecisionPhase.apply()`
hot path, converted to the established per-instance `BoundedObservabilityQueue`/`QueueDrainWorker`
pattern already used by `EventRecorder`. The resulting bounded crash-loss and queue-overflow-drop
windows are documented in `docs/guidelines/intentional_divergences.md` §2.31 and cross-referenced
from the contract doc. Kernel worker-count accounting (`_workers_started`/`workers_stopped`)
updated to reflect the second per-run worker, preventing a false `PARTIAL` shutdown outcome on
every LIGHT+ run.
