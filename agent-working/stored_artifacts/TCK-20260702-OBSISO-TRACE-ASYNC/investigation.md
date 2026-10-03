---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260702-OBSISO-TRACE-ASYNC
artifact_type: investigation
tags: [observability, performance]
---

# Investigation — TCK-20260702-OBSISO-TRACE-ASYNC

## Current Behavior

### `DecisionTraceWriter.write_trace()` — `src/observability/cognition/decision_trace_writer.py:65-133`
Confirmed still present exactly as the ticket describes, with **one addition the ticket did not scope**:
- Line 128: `self._file.write(json.dumps(entry) + "\n")` — synchronous file write.
- Line 129: `self._file.flush()` — synchronous flush.
- Line 131: `self._index.append_entry(tick, offset)` — **also synchronous disk I/O**, not just an in-memory index update. `DecisionTraceIndex.append_entry()` (`src/observability/cognition/tick_index.py:39-56`) calls `self._flush()` (`tick_index.py:128-132`), which does `json.dump(serialized, f)` to `decision_trace_index.json` on every first-of-tick call. This is a second hot-path file-IO violation co-located with the one the ticket names. `append_entry()` short-circuits after the first entity per tick (`if tick in self._index: return`), so it's not per-entity, but it is still per-tick synchronous disk I/O inside `AdventureDecisionPhase.apply()`, and it is NOT mentioned in the ticket's Scope bullets. The fix must move this write to the async worker too, or the ticket will ship only half-compliant.
- `_ensure_open()` (line 60-63) does `os.makedirs` + `open(..., "a")` lazily on first write — also currently on the hot path (first call only, but still a real filesystem syscall from inside a phase).
- The `_latest_goal_scores` cache update (lines 92-102) is a pure in-memory dict write — already contract-§2-compliant, must stay hot-path-side per the ticket's plan.

### Call site — `src/domains/adventure/phase.py`
Ticket claims `phase.py:20` for the `get_active_writer()` wiring. Current state:
- Line 22: `from src.observability.cognition.decision_trace_writer import get_active_writer as _get_active_writer` (the import — 2 lines later than the ticket's cited line 20; **minor line-number drift**, not a logic drift).
- Line 86: `_resolved_writer = trace_writer if trace_writer is not None else _get_active_writer()` — resolved once per `apply()` call, outside the per-hero loop (a deliberate optimization per the comment at lines 83-85, to avoid O(n) lazy-import cost).
- Line 120: `_writer.write_trace(hero.id, tick, scored_candidates)` — the actual call site inside the `for hero in heroes:` loop (lines 88-134), i.e. genuinely hot-path, once per eligible hero per tick.
The ticket's behavioral description ("invoked from inside the adventure decision phase via `get_active_writer()`") is accurate; only the specific line number is stale.

### `get_latest_goal_scores()` / `entity_inspector.py` consumer
Confirmed exact: `src/observability/cognition/decision_trace_writer.py:135-141` returns `self._latest_goal_scores.get(entity_id, [])` (pure dict read, no I/O). Consumer at `src/observability/live/entity_inspector.py:138-144`, and specifically line 142: `goal_scores = _writer.get_latest_goal_scores(entity_id)` — **matches the ticket's cited line exactly**. This path must be preserved unchanged; it does not touch the file at all today and won't need to under the async fix, since the cache is populated synchronously inside `write_trace()` before any I/O happens.

### `Kernel` writer init/close — `src/engine/kernel.py`
- **Init**: lines 288-293 — **matches the ticket's cited lines exactly**. `DecisionTraceWriter(run_dir=run_dir_str)` is constructed and registered via `set_active_writer()` inside the `if obs_mode != ObservabilityMode.OFF:` block (line 275).
- **Close**: ticket claims lines ~981-986. **Actual is lines 1068-1074** — a drift of ~87 lines from the ticket's scoping-time snapshot. Current code:
  ```python
  if hasattr(self, "_decision_trace_writer") and self._decision_trace_writer:
      try:
          self._decision_trace_writer.close()
      except Exception:
          logger.exception("DecisionTraceWriter.close() failed during shutdown (non-fatal)")
      from src.observability.cognition.decision_trace_writer import set_active_writer
      set_active_writer(None)
  ```
  This runs inside `Kernel.shutdown()` (starts at line 1037), after `EventRecorder.shutdown()` (line 1061-1063) and `MetricWindowRecorder.shutdown()` (line 1065-1066), before the behavior-normalization-worker join (line 1076+). Ordering is compatible with the ticket's requirement ("flush and close the trace sink after final tick, before run finalization").
- **Worker accounting gap**: `Kernel.__init__` sets `self._workers_started = 1 if (obs_mode != ObservabilityMode.OFF) else 0` (line 305), with the comment "1 = EventRecorder._worker (QueueDrainWorker)". This counter does **not** account for any additional `QueueDrainWorker` the DecisionTraceWriter fix will start. If the fix follows the `EventRecorder` per-instance-worker pattern (recommended — see below), this line must be updated to `2 if obs_mode != OFF else 0`, or `ShutdownReport.workers_started` will under-report and any lifecycle-supervisor test asserting exact worker counts will need updating. Not mentioned anywhere in the ticket.

## Established Reuse Pattern (stronger precedent than the ticket names)

`src/observability/queue.py` provides two usable patterns:
1. **Global singleton** (`get_observability_queue()` + `get_or_start_global_worker()`, lines 164-190) — one shared queue/worker for the whole process, guarded against double-start.
2. **Per-instance queue+worker** (used by `EventRecorder`, `src/observability/event_recorder.py:96-107`) — each `EventRecorder` owns its own `BoundedObservabilityQueue` and `QueueDrainWorker(queue=..., file_write_fn=self._write_envelope_to_file, ...)`, started in `__init__` when enabled, stopped in `shutdown()`.

`DecisionTraceWriter` is run-scoped (one instance per Kernel run, exactly like `EventRecorder`), not process-scoped. **The per-instance pattern (#2) is the correct precedent, not the global singleton** — the ticket's Scope bullet ("reuse/extend `QueueDrainWorker`... following contract §6 singleton/shutdown/test-teardown rules") is directionally right but doesn't distinguish this; §6 itself documents both patterns and explicitly says `EventRecorder` uses its own private queue, not the global one. `EventRecorder.shutdown()` (`event_recorder.py:301-321`) is the concrete lifecycle template to copy: (1) `self._worker.stop()`, (2) synchronously drain any remaining queued items and write them, (3) close the file handle. This directly satisfies the ticket's "records written during a run appear in decision_trace.jsonl after shutdown" AC.

`QueueDrainWorker`'s thread is always named `"observability-drain-worker"` (`queue.py:114`, hardcoded, not parameterized) regardless of which queue it drains. `tests/tools/memory_probe.py::count_drain_workers()` counts threads by this exact name, and `tests/conftest.py::_observability_worker_thread_sentinel` fails the suite if the count grows net across the session. A second per-run worker for the trace writer will be counted by the same sentinel — correct behavior, but it means `DecisionTraceWriter.close()` must reliably call `.stop()` in every test/run path or the sentinel will trip. This is the enforcement mechanism for AC "Worker lifecycle: conftest worker-thread sentinel does not trip."

## Mechanics / Engine Constraints

- `docs/architecture/observability_hot_path_safety_contract.md` §1 defines the hot path as any code inside/called by simulation phases — `AdventureDecisionPhase.apply()` qualifies directly.
- §2 whitelists "Non-Blocking Queue Appends" (bounded, non-blocking) and "Bounded In-Memory Timeline Appends" — the target end-state for `write_trace()`.
- §3 forbids "Direct JSON/YAML/Pickle file writes" inside the hot path — this is the exact violation, for **both** `self._file.write()`/`flush()` and `DecisionTraceIndex.append_entry()`'s `_flush()`.
- §4.2 requires graceful degradation (drop, don't block) when the bounded queue saturates — the new buffer/queue must not block `AdventureDecisionPhase.apply()` under pressure.
- §6 Worker Lifecycle Contract: singleton guarantee (only for the *global* queue — not applicable if a private per-instance queue is used, per the contract's own carve-out for `EventRecorder`), test-teardown rule (`.shutdown()`/`.close()` required), and the conftest sentinel as the enforcement mechanism.
- `docs/observability/decision_trace_contract.md` "Tick Index Sidecar → Lifecycle" section explicitly documents the current *synchronous* crash-recovery contract: "`append_entry(tick, offset)` is called from `write_trace()` **after each flush**... keeps the sidecar valid after every write (crash recovery)." This sentence becomes false the moment the flush moves off-path, and must be rewritten, not just the code.

## Docs Requiring Update

- `docs/observability/decision_trace_contract.md`: the "Implementation Notes" and "Tick Index Sidecar → Lifecycle" sections assert per-write synchronous flush and per-write incremental index update as the crash-recovery mechanism; both become inaccurate once file IO moves to an async worker and must be rewritten to describe the new buffer/drain lifecycle and any crash-loss window.
- `docs/parity_ledger/infrastructure.yaml`: INFRA-211 (`v2_evidence` currently cites `DecisionTraceWriter.write_trace` as the synchronous-write mechanism) and INFRA-212 (`text` explicitly says "Updated incrementally on each write_trace() call (crash recovery)") both need `v2_evidence`/`text` updates to reflect the async drain path; `status: verified` should be re-affirmed only after the new test_path(s) pass.
- `docs/guidelines/intentional_divergences.md`: if the async fix introduces any observable crash-loss window (in-flight buffered records not yet drained at time of an unclean process kill), it must be recorded here with a rationale class (`Bounded` fits best) and a verification test path, per the ticket's own Assumptions/Open Questions bullet and per the Authoritative Mechanics Rule's Divergence clause. Note: the correct filename is `docs/guidelines/intentional_divergences.md` — see Drift below, the ticket names a nonexistent `v2_intentional_divergences.md`.
- `docs/plans/observability_process_isolation.md`: this is the source proposal for the whole `obs-isolation` epic batch; its "Gaps" section (G4, lines 60-63) is the canonical description of the bug being fixed here. It should be updated to mark G4 resolved (or cross-referenced to this ticket) so the epic-tracking doc doesn't keep describing live code as contract-violating after this ticket closes.

## Parity Ledger Overlap

- **INFRA-211** (`docs/parity_ledger/infrastructure.yaml:2392-2401`) — "Decision trace writer (LIGHT+ mode)". `status: verified`, `priority: P1`. `test_path: tests/unit/observability/test_decision_trace.py::test_decision_trace_runner_up_scores_present` — **path exists and the test exists** (verified at `tests/unit/observability/test_decision_trace.py:463`). `v2_evidence` names `DecisionTraceWriter.write_trace` — needs updating to describe the buffer-append + async-drain split.
- **INFRA-212** (`infrastructure.yaml:2402-2411`) — "Decision trace tick-index sidecar (Epic 2.2B)". `status: verified`, `priority: P1`. `test_path: tests/unit/observability/test_decision_trace.py::test_tick_index_o1_lookup` — **path exists** (`tests/unit/observability/test_decision_trace.py:316`). `text` explicitly claims per-write incremental updates for crash recovery — this text becomes stale under the fix and must be rewritten alongside the doc.
- Both entries are P1, not P0 — no hard test_path-passing gate beyond the repo's general "any status change needs a passing test_path" rule, but both already have valid, existing test paths that should be re-verified (and likely renamed/extended) as part of this ticket, not left dangling.
- No P0 entries touch this code path in `infrastructure.yaml`.

## Prior Work

- `TCK-20260619-E22A-TRACE-WRITER` (`tickets/working_log.csv`) — original writer, shipped with synchronous per-entity flush; this ticket's own ancestor.
- `TCK-20260619-E22B-TICK-INDEX` — added `DecisionTraceIndex` with the incremental-append/rebuild-on-close pattern this ticket must preserve or explicitly weaken.
- `TCK-20260610-WORKER-SINGLETON-GUARD` (`stored_artifacts/TCK-20260610-WORKER-SINGLETON-GUARD/investigation.md`) — directly relevant precedent: confirms `EventRecorder` uses a **per-instance** queue/worker (not the global singleton), and that `get_or_start_global_worker()` only guards the module-level global queue. This is the strongest evidence for recommending the per-instance pattern over the global one for `DecisionTraceWriter`.
- `TCK-20260610-THREAD-LEAK-CONFTEST` — added the `_observability_worker_thread_sentinel` this ticket's AC #5 depends on.
- `TCK-20260529-OBS-PHASE21` — "Non-Blocking Event Emission Pipeline", original implementation of `BoundedObservabilityQueue`/`QueueDrainWorker`, and their integration into `EventRecorder` — the exact pattern this ticket is asked to extend.
- `docs/plans/observability_process_isolation.md` (source proposal, dated 2026-07-02, `status: proposal`) — this ticket is the direct child of Gap G4 in that document; three sibling tickets exist for G1/G2/G3/G5 (`TCK-20260702-OBSISO-BROKER-CONFIG`, `TCK-20260702-OBSISO-WORKER-PARITY`, `TCK-20260702-OBSISO-ISOLATION-PROOF`) plus the tracking epic `TCK-20260702-OBSISO-EPIC`, all still sitting in `tickets/todos/obs-isolation/` (not yet started). No working_log entries exist yet for any OBSISO ticket — this is the first one being worked in the batch.

## Risks and Open Questions

- **Ticket scope gap (not just drift)**: the ticket's Scope section only names the main `.jsonl` write + flush as the violation. `DecisionTraceIndex.append_entry()`'s synchronous `_flush()` to `decision_trace_index.json` is an equally real §3 violation on the same call path and is not mentioned. If the implementer fixes only the main file write and leaves `append_entry()` synchronous, the ticket's own AC #1 ("no file IO calls reachable from `write_trace()` on the phase call path") will still fail a thorough static check. This should be treated as in-scope, not a follow-up ticket — it's the same call chain, same root cause, same fix shape (move to the async worker).
- **`test_tick_index_incremental_vs_rebuild`** (`tests/unit/observability/test_decision_trace.py:439-456`) inspects `writer._index._index` immediately after `write_trace()` calls and *before* `close()`, asserting it already matches the post-close rebuilt index. Once the index write moves to an async worker, this in-memory state will not be populated synchronously at that point — this test's premise breaks and it must be rewritten (e.g., assert equality only after an explicit drain/close, or assert eventual consistency).
- **Crash-loss window**: the ticket's own Assumptions section already flags this and offers a fallback (batched fsync every N ticks) if the contract owner disagrees. No contract owner sign-off is recorded anywhere in the repo — this is a genuine open decision, not a rubber-stamp. Flagging per the "do not assume an answer" instruction: the investigation does not resolve whether an unbounded crash-loss window (buffer drained only on the worker's `interval_sec` cadence, default 0.01s per `QueueDrainWorker.__init__`) is acceptable, or whether periodic off-path fsync is required. This should be an explicit decision recorded in plan.md, not decided silently during implementation.
- **Buffer bounding**: the ticket says "bounded buffer or dedicated bounded queue" but doesn't specify a size. `BoundedObservabilityQueue.__init__` defaults `max_size=1000`; `ObservabilityConfig.get_max_queue_size()` (config.py:341) is the existing knob `EventRecorder` uses. Decide in plan.md whether the trace writer reuses this same config knob or needs its own.

## Anti-Drift Hazards

- **Naming collision**: `src/observability/trace.py::DecisionTrace` / `DecisionOptionTrace` / `RejectedOptionTrace` (covered by `tests/unit/observability/test_phase17_decision_trace_contract.py`) is a **completely unrelated** "Phase 17" causal-decision-trace concept (combat/cooperation causal chains), not `decision_trace.jsonl`. `tests/unit/observability/test_phase17_decision_trace_validator.py`, `test_phase17_decision_trace_contract.py`, and `tests/integration/scenarios/test_phase17_decision_trace_scenarios.py` are all in this unrelated system — do not touch them, and do not let "decision trace" naming similarity pull them into this ticket's regression surface.
- Do not widen scope into `src/api/routes/decisions.py` (explicitly out of scope) even though `DecisionTraceIndex.lookup()` is its read path — the REST layer is unaffected by moving the write side async, since `lookup()` only reads the finished file/sidecar.
- Do not touch the P1-H runner-up retention logic (`_latest_goal_scores` construction, lines 91-102) — only the serialization+IO after that point should move.
- Do not change `execute_brain()` or any tactical cognition domain code — the contract note "execute_brain() is NOT modified" (both in the writer's module docstring and `decision_trace_contract.md`) predates this ticket and remains a hard boundary.
- Watch the `_workers_started` counter (`kernel.py:305`) and any lifecycle-supervisor test that asserts an exact worker count — adding a second per-run worker without updating this accounting will silently produce an incorrect `ShutdownReport.workers_started`, which is a durable-state-adjacent observability signal, not cosmetic.
