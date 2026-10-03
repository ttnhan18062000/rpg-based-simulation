---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260702-OBSISO-TRACE-ASYNC
artifact_type: test_plan
tags: [observability, performance]
---

# Test Plan — TCK-20260702-OBSISO-TRACE-ASYNC

## Regression Surface

**Unit**
- `tests/unit/observability/test_decision_trace.py` (593 lines, 22 tests) — the primary regression surface. Nearly every test constructs a `DecisionTraceWriter`, calls `write_trace()`, then `close()`, then reads `decision_trace.jsonl` synchronously. All of these depend on `close()` performing a full synchronous drain before returning:
  - `test_decision_trace_written_in_light_mode`, `test_decision_trace_schema_has_all_score_terms`, `test_decision_trace_not_written_in_off_mode`, `test_decision_trace_caps_at_5_routes`, `test_decision_trace_append_mode`, `test_decision_trace_selected_flag`, `test_decision_trace_empty_routes_is_noop`
  - `test_set_and_get_active_writer`, `test_adventure_decision_phase_wires_writer`, `test_decision_trace_writer_does_not_import_engine_cognition`
  - Tick-index tests: `test_tick_index_o1_lookup`, `test_tick_index_file_exists_after_close`, `test_tick_index_format_correctness`, `test_tick_index_lookup_missing_tick`, `test_tick_index_rebuild_idempotent`, `test_tick_index_load_from_disk`, `test_tick_index_incremental_vs_rebuild` (this one specifically inspects pre-close internal state — see New Tests / drift note below, it will very likely need rewriting, not just re-passing)
  - Runner-up/score tests: `test_decision_trace_runner_up_scores_present`, `test_decision_trace_source_goal_score_present`, `test_decision_trace_runner_up_fewer_than_3`, `test_decision_trace_runner_up_single_candidate`, `test_decision_trace_routes_sorted_descending`
  - Cache tests: `test_entity_inspection_snapshot_has_goal_scores_field`, `test_decision_trace_writer_caches_goal_scores`
- `tests/unit/observability/test_entity_inspector.py` — must pass **unchanged** per AC. Covers `EntityInspector.inspect_entity()` including the `goal_scores` field population at `entity_inspector.py:135-144`.
- `tests/unit/observability/test_obs_backpressure.py` — regression guard for `ObservabilityController`/backpressure modes; not directly touched but shares `src/observability/queue.py` primitives, worth a pass to confirm no shared-state bleed.
- `tests/unit/engine/test_lifecycle_supervisor.py` — covers `ShutdownReport`/`workers_started` accounting and `QueueDrainWorker` shutdown reporting (`TestCleanShutdown`, `TestShutdownReportShape`, `TestBehaviorWorkerShutdown`, `TestSurvivalCountsInReport`, `TestPendingReplayFlushesWarning`). Directly at risk if `_workers_started` (`kernel.py:305`) isn't updated to account for a second worker — see investigation.md Risks.

**Architecture**
- `tests/architecture/test_phase19_hot_path_safety_contract.py` — existing hot-path guard. Currently only checks `src/engine/`, `src/observability/config.py`, `event_extractor.py`, `event_recorder.py` for forbidden *analyzer class name* strings — it does **not** currently cover `src/domains/adventure/phase.py` or `decision_trace_writer.py`, and does not check for raw `open(`/`.write(`/`.flush()` calls at all. This existing test will keep passing regardless of this ticket's fix (it doesn't exercise the violated code path) — it should not be relied on as proof of compliance; a new, more targeted static/AST test is required (see New Tests).

**Integration**
- None of `tests/integration/scenarios/test_phase17_decision_trace_scenarios.py`, `tests/unit/observability/test_phase17_decision_trace_validator.py`, `tests/unit/observability/test_phase17_decision_trace_contract.py` are in scope — confirmed unrelated `src/observability/trace.py::DecisionTrace` system (naming collision only). Do not run these as part of this ticket's proof; listed here only to explicitly exclude them.

## New Tests Required

1. **Hot-path no-file-IO static/AST guard**
   - Category: architecture guard
   - Verifies: no `open(`, `.write(`, `.flush(`, or `json.dump(` call is reachable via AST/static analysis from `DecisionTraceWriter.write_trace()` or anything it calls synchronously on the `AdventureDecisionPhase.apply()` call path (including `DecisionTraceIndex.append_entry()`'s current `_flush()`). This directly implements the ticket's AC #1, which does not exist today (the closest thing, `test_phase19_hot_path_safety_contract.py`, only string-matches analyzer class names, not IO calls, and doesn't cover this module).
   - Location: `tests/architecture/test_decision_trace_hot_path_no_io.py` (new file) or extend `tests/architecture/test_phase19_hot_path_safety_contract.py` with a second, IO-specific check function.

2. **`write_trace()` is a pure in-memory append (no blocking)**
   - Category: unit
   - Verifies: calling `write_trace()` N times in a tight loop does not create/open `decision_trace.jsonl` synchronously (file only appears after the async worker drains, or after `close()`), and returns quickly (no `open`/`flush` syscall on the calling thread). Can assert via mocking `builtins.open` / `os.makedirs` during `write_trace()` and asserting zero calls.
   - Location: `tests/unit/observability/test_decision_trace.py`

3. **`get_latest_goal_scores()` returns current values before any flush**
   - Category: unit
   - Verifies: immediately after `write_trace()` (no `close()`, no worker drain triggered), `get_latest_goal_scores(entity_id)` returns the just-written top-3 scores — proves the in-memory cache update is synchronous/hot-path-side even though disk IO is not. Directly required by AC.
   - Location: `tests/unit/observability/test_decision_trace.py`

4. **Records appear in `decision_trace.jsonl` after shutdown/close (async drain correctness)**
   - Category: unit
   - Verifies: `write_trace()` N times, then `close()` (or the Kernel-level `shutdown()` path), and all N records are present in `decision_trace.jsonl`, valid JSON, and the tick-index sidecar (`decision_trace_index.json`) is complete and correct — updates/replaces the now-invalid pre-close-timing assumption in `test_tick_index_incremental_vs_rebuild`.
   - Location: `tests/unit/observability/test_decision_trace.py` (rewrite of `test_tick_index_incremental_vs_rebuild`, or a new test alongside it if the old one is kept for a narrower "eventual consistency after explicit drain" claim)

5. **Determinism: identical `decision_trace.jsonl` content across two same-seed runs**
   - Category: integration
   - Verifies: async draining does not introduce ordering nondeterminism — two same-seed runs of the same scenario produce byte-identical (or line-set-identical, preserving per-tick order) `decision_trace.jsonl`. This is explicitly required by AC and is a real risk introduced by moving from a synchronous per-call write (strict call order) to a queued async drain (potential reordering under concurrent producers — though `AdventureDecisionPhase.apply()` itself is single-threaded per tick, so ordering risk is specifically about whether the drain loop preserves FIFO order, which `BoundedObservabilityQueue`/`QueueDrainWorker` do today via list append/full-drain).
   - Location: `tests/integration/observability/test_decision_trace_determinism.py` (new) or an existing scenario-determinism suite if one already parametrizes on `decision_trace.jsonl`.

6. **Worker lifecycle: sentinel does not trip; `shutdown()`/`close()` idempotent**
   - Category: unit / architecture
   - Verifies: (a) creating and closing a `DecisionTraceWriter` (standalone, and via `Kernel`) leaves no `"observability-drain-worker"` thread alive after `close()`/`shutdown()` — assert via `tests/tools/memory_probe.py::count_drain_workers()` before/after, mirroring the existing conftest sentinel's own check; (b) calling `close()` twice does not raise or double-join.
   - Location: `tests/unit/observability/test_decision_trace.py`

7. **Kernel `_workers_started` accounting reflects the new worker**
   - Category: unit (lifecycle supervisor)
   - Verifies: `Kernel.__init__` with `obs_mode != OFF` reports `_workers_started` (and therefore `ShutdownReport.workers_started`) consistent with the actual number of `QueueDrainWorker`-backed components started (EventRecorder's + DecisionTraceWriter's, if the per-instance-worker approach is chosen). Guards the accounting gap flagged in investigation.md.
   - Location: `tests/unit/engine/test_lifecycle_supervisor.py`

8. **Crash-loss window is documented, not silently introduced**
   - Category: unit / doc-consistency (light-touch — this is really a plan.md decision gate, but a smoke test can assert the decision was recorded)
   - Verifies: if plan.md resolves the Assumptions/Open Questions item in favor of accepting a bounded crash-loss window, a test should assert `docs/guidelines/intentional_divergences.md` contains an entry referencing this ticket ID (simple substring/frontmatter check), so the doc-update requirement can't silently regress. Optional if the plan instead chooses zero-loss (e.g., synchronous drain on every N ticks off-path) — adapt or drop this test to match whichever decision plan.md records.
   - Location: `tests/unit/observability/test_decision_trace.py` or a lightweight docs-consistency test, per existing repo convention (see `tests/architecture/test_phase19_hot_path_safety_contract.py::test_hot_path_safety_contract_doc_exists` as a precedent for doc-presence assertions).

## Scoped Pytest Commands

```
# Primary regression surface
pytest tests/unit/observability/test_decision_trace.py -v

# Entity inspector — must pass unchanged
pytest tests/unit/observability/test_entity_inspector.py -v

# Queue/worker pattern + backpressure sanity (shared primitives, not directly modified)
pytest tests/unit/observability/test_obs_backpressure.py -v

# Lifecycle/shutdown accounting
pytest tests/unit/engine/test_lifecycle_supervisor.py -v

# New/updated architecture guard
pytest tests/architecture/test_phase19_hot_path_safety_contract.py tests/architecture/test_decision_trace_hot_path_no_io.py -v

# Full observability unit tier (broader net once the above are green)
pytest tests/unit/observability/ -v

# Determinism / integration (new test, once written)
pytest tests/integration/observability/ -v
```

Do not run `pytest tests/` — scope to `tests/unit/observability/`, `tests/architecture/` (hot-path guard only), `tests/unit/engine/test_lifecycle_supervisor.py`, and `tests/integration/observability/`.

## Anti-Drift Test Guards

- **Naming-collision guard**: do not add or modify anything in `test_phase17_decision_trace_validator.py`, `test_phase17_decision_trace_contract.py`, or `test_phase17_decision_trace_scenarios.py` — confirm they stay green as an unrelated-system sanity check (`src/observability/trace.py`, not `decision_trace_writer.py`), and treat any accidental edit there as scope creep.
- **REST API isolation guard**: `src/api/routes/decisions.py` and its tests (if any exist under `tests/api/` or `tests/unit/api/routes/`) must show zero diff — the read path only consumes the finished file/sidecar via `DecisionTraceIndex.lookup()`, which is untouched by this ticket.
- **`execute_brain()` / tactical cognition guard**: `test_decision_trace_writer_does_not_import_engine_cognition` (existing, `test_decision_trace.py:277-296`) already asserts `decision_trace_writer.py` never imports `src.engine.domain.cognition` — keep this passing verbatim; it is the existing enforcement for "execute_brain() is NOT modified."
- **P1-H runner-up retention guard**: `test_decision_trace_runner_up_scores_present`, `test_decision_trace_runner_up_fewer_than_3`, `test_decision_trace_runner_up_single_candidate` must all pass with byte-identical score/rank semantics — the in-memory scoring/cache-building logic (lines 88-106 of `decision_trace_writer.py`) is explicitly out of scope for this ticket and must not shift.
- **SimQ/EventRecorder non-interference guard**: since `EventRecorder` already owns a `QueueDrainWorker` on its own private queue, confirm the new trace-writer worker (if using the per-instance pattern) does not share state, thread name collisions aside (both will be named `"observability-drain-worker"` — acceptable per existing sentinel design, which counts by name across all instances, not per-component), or interfere with `SimQ`'s `quality_fn` wiring (`docs/plans/observability_process_isolation.md` §4.3 "shared per-tick budget" — a second worker adds to the cumulative per-tick observability cost this doc flags as unmeasured, G5's concern; out of scope to fix here but should not be made worse without note).
