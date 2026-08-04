---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260702-OBSISO-TRACE-ASYNC
artifact_type: plan
tags: [observability, decision-trace, hot-path, performance, contract-compliance]
---

# Implementation Plan — TCK-20260702-OBSISO-TRACE-ASYNC

## Summary

`DecisionTraceWriter.write_trace()` (`src/observability/cognition/decision_trace_writer.py:65-133`) and,
critically, the co-located `DecisionTraceIndex.append_entry()` call it makes (`tick_index.py:39-56`,
`_flush()` at `tick_index.py:128-132`) both perform synchronous file I/O from inside
`AdventureDecisionPhase.apply()`'s per-hero loop (`src/domains/adventure/phase.py:120`) — two real §3
hot-path violations on the same call chain, not one. This plan converts `DecisionTraceWriter` to the
established **per-instance queue+worker** pattern already used by `EventRecorder`
(`event_recorder.py:96-107`, `event_recorder.py:301-321`) — not the global singleton — since
`DecisionTraceWriter` is run-scoped exactly like `EventRecorder`. `write_trace()` becomes a pure in-memory
enqueue (plus the existing, already-compliant `_latest_goal_scores` cache update); a private
`BoundedObservabilityQueue`/`QueueDrainWorker` pair, owned by the `DecisionTraceWriter` instance, performs
the actual `decision_trace.jsonl` write **and** the `DecisionTraceIndex.append_entry()` call off-path, on
the worker thread. `close()` follows `EventRecorder.shutdown()`'s three-step lifecycle (stop worker → drain
remainder synchronously → close file), then keeps the existing `rebuild()` call for a clean end-of-run
sidecar. Kernel wiring changes are limited to worker-count accounting (`_workers_started` at `kernel.py:305`
and the missing `workers_stopped` increment at the close site, `kernel.py:1068-1074`) — the constructor
call at `kernel.py:288-293` needs no change, since `DecisionTraceWriter(run_dir=...)`'s signature is
unchanged. The crash-loss-window question is resolved in this plan (Step 9): accept a small bounded window
sized to the worker's `interval_sec=0.01s` default, consistent with the pre-existing, already-accepted
precedent set by `EventRecorder`/`simulation_events.jsonl`, and record it under
`docs/guidelines/intentional_divergences.md` with rationale class `Bounded`. No new fsync-every-N-ticks
mechanism is introduced — inventing one would create an inconsistency with `EventRecorder`'s own accepted
behavior on the identical queue/worker primitive, for no corresponding gain in this ticket's scope.

## Steps

### Step 1 — `DecisionTraceWriter`: add per-instance queue+worker; convert `write_trace()` to enqueue-only
**Files:** `src/observability/cognition/decision_trace_writer.py`
**Change:**
- In `__init__` (currently lines 52-58), add:
  ```python
  from src.observability.queue import BoundedObservabilityQueue, QueueDrainWorker
  self._queue = BoundedObservabilityQueue(max_size=ObservabilityConfig.get_max_queue_size())
  self._worker = QueueDrainWorker(queue=self._queue, file_write_fn=self._write_entry_to_file)
  self._worker.start()
  ```
  **Decision (buffer sizing):** reuse `ObservabilityConfig.get_max_queue_size()` (`config.py:341`) — the
  same knob `EventRecorder` already uses — rather than a dedicated size/env var. There is no scoping reason
  for decision-trace volume to need independent tuning from event volume, and a second knob would be an
  unexplained divergence from the established pattern.
- **Queue item shape — required design note, not optional:** `BoundedObservabilityQueue.try_push()`
  (`queue.py:28-67`) accesses `event.severity` on its overflow/eviction path
  (`is_high_priority = event.severity in ("CRITICAL", "ERROR")`, `queue.py:44`). A plain trace `entry`
  dict has no `.severity` attribute, so pushing raw dicts will raise `AttributeError` the first time the
  queue is ever full — an ungraceful failure mode, not a clean drop, violating §4.2. Add a small wrapper
  type in this file:
  ```python
  from dataclasses import dataclass, field

  @dataclass
  class _DecisionTraceQueueItem:
      # Decision-trace entries carry no real priority semantics; this constant value exists
      # only to satisfy BoundedObservabilityQueue's shared severity-eviction interface.
      severity: str = "INFO"
      entry: Dict[str, Any] = field(default_factory=dict)
  ```
  Push `_DecisionTraceQueueItem(entry=entry)` from `write_trace()`, not the bare `entry` dict.
- In `write_trace()` (lines 65-133): remove the `self._ensure_open()` call (line 85), the
  `offset = self._file.tell()` line (line 86), the `self._file.write(...)`/`self._file.flush()` lines
  (128-129), and the `self._index.append_entry(tick, offset)` line (131) — the offset can no longer be
  computed on the hot path since the file may not even be open yet; it is computed at actual write time
  inside the worker callback (Step 2). In their place, after building `entry` (unchanged construction,
  lines 90-127), add:
  ```python
  self._queue.try_push(_DecisionTraceQueueItem(entry=entry))
  ```
  Everything before that point in `write_trace()` — the `is_decision_trace_enabled()` guard, the empty-routes
  guard, `sorted_routes`, `top3`/`goal_scores_list` construction, and the `self._latest_goal_scores[entity_id]
  = goal_scores_list` cache write (lines 92-102) — is unchanged. This is the block the ticket's own
  Implementation Notes and the investigation's Anti-Drift Hazards both call out as already contract-§2
  compliant and out of scope to alter.
- Add the worker callback method (new; the actual file write moves here from `write_trace()`):
  ```python
  def _write_entry_to_file(self, item: "_DecisionTraceQueueItem") -> None:
      self._ensure_open()
      offset = self._file.tell()
      self._file.write(json.dumps(item.entry) + "\n")
      self._file.flush()
      self._index.append_entry(item.entry["tick"], offset)
  ```
  No internal `try/except` inside this method — `QueueDrainWorker._run()` (`queue.py:126-154`) already
  wraps every `file_write_fn` call in its own `try/except`, incrementing `failure_count`/setting
  `health_status = "DEGRADED"` on error, matching `EventRecorder._write_envelope_to_file`'s convention
  (no internal try/except there either).
- `_ensure_open()` itself (lines 60-63) is unchanged in body — it simply now executes on the worker thread
  on first drained item instead of on the hot path on first call.
**Do NOT touch:** the `_latest_goal_scores` construction/cache-write block (lines 88-106) — scoring/rank
semantics must stay byte-identical; `get_latest_goal_scores()` (lines 135-141) — unchanged, still a pure
dict read.
**Verify:** `test_decision_trace_writer_caches_goal_scores`, `test_decision_trace_runner_up_scores_present`
(existing, must keep passing unmodified — proves the cache-write path survived this step untouched); new
test 2 from Step 6 (`write_trace()` performs no synchronous file/`os` calls).

### Step 2 — Move `DecisionTraceIndex.append_entry()` off the hot path (the missed scope item)
**Files:** `src/observability/cognition/decision_trace_writer.py` (no further change beyond Step 1 — the
`append_entry()` call already moved into `_write_entry_to_file` in Step 1), `src/observability/cognition/tick_index.py`
**Change:** No logic change to `DecisionTraceIndex` — `append_entry()` (`tick_index.py:39-56`) and its
`_flush()` (`tick_index.py:128-132`) keep their exact current bodies. The fix for this violation is entirely
about **who calls `append_entry()`**: after Step 1, it is called from `_write_entry_to_file`, which runs on
the `QueueDrainWorker` thread, not from `write_trace()` on the phase call path. This satisfies AC #1 for the
index write without touching `append_entry()`'s internals.
What must change in `tick_index.py` is documentation that is now factually wrong:
- Module docstring (lines 10-14): "`append_entry()` is called incrementally from
  `DecisionTraceWriter.write_trace()` (crash-safe...)" → rewrite to say it is called from
  `DecisionTraceWriter`'s async drain worker callback after each queued entry is written to
  `decision_trace.jsonl`, not synchronously from `write_trace()`.
- `append_entry()`'s docstring (lines 40-49): "Called from `DecisionTraceWriter.write_trace()` before each
  flush so the sidecar is kept valid after every write (crash recovery)." → rewrite to describe the new
  caller (the worker's `_write_entry_to_file`) and clarify the sidecar is kept valid after every **drained**
  write, at the worker's cadence, not synchronously per hot-path call.
**Do NOT touch:** `append_entry()`'s body, `_flush()`, `rebuild()`, `lookup()`, `_load()` — no logic changes
anywhere in `tick_index.py`. `lookup()` in particular (used by the REST API, out of scope) must show zero
diff.
**Verify:** `test_tick_index_o1_lookup`, `test_tick_index_file_exists_after_close`,
`test_tick_index_format_correctness`, `test_tick_index_lookup_missing_tick`,
`test_tick_index_rebuild_idempotent`, `test_tick_index_load_from_disk` (all existing, must keep passing
unmodified — proves `tick_index.py`'s logic is untouched); new architecture guard test from Step 5 (proves
`append_entry()` is no longer reachable from `write_trace()`'s hot-path call graph).

### Step 3 — `DecisionTraceWriter.close()`: worker-stop + synchronous final drain + idempotency
**Files:** `src/observability/cognition/decision_trace_writer.py`
**Change:** Replace `close()` (currently lines 143-157, which only closes `self._file` and calls
`self._index.rebuild()`) with the three-step lifecycle from `EventRecorder.shutdown()`
(`event_recorder.py:301-321`), keeping the existing `rebuild()` call as a fourth, final step:
```python
def close(self) -> None:
    # 1. Stop the background drain worker.
    if getattr(self, "_worker", None):
        self._worker.stop()

    # 2. Final synchronous flush of any remaining queued items.
    try:
        remaining = self._queue.drain()
        for item in remaining:
            self._write_entry_to_file(item)
    except Exception:
        logger.exception("DecisionTraceWriter.close final queue drain failed (non-fatal)")

    # 3. Close the file handle.
    if self._file is not None:
        try:
            self._file.close()
        except Exception:
            logger.exception("DecisionTraceWriter.close failed (non-fatal)")
        finally:
            self._file = None

    # 4. Rebuild the index from the completed file for a clean, complete sidecar.
    try:
        self._index.rebuild()
    except Exception:
        logger.exception("DecisionTraceWriter.close index rebuild failed (non-fatal)")
```
Idempotency falls out of existing primitives without extra guard code: `QueueDrainWorker.stop()`
(`queue.py:120-124`) sets `self._thread = None` after joining, so a second `stop()` call is a no-op;
`self._queue.drain()` (`queue.py:69-76`) returns `[]` once already drained; `self._file` is already
`None`-guarded; `self._index.rebuild()` is already idempotent (rescans the file fresh each call). No new
"already closed" flag is needed.
**Do NOT touch:** the `rebuild()` call itself — keep it as the final step exactly as today, it remains the
end-of-run completeness guarantee the ticket's Scope explicitly requires ("tick-index sidecar... rebuilt on
close").
**Verify:** new test 4 from Step 6 (records appear in `decision_trace.jsonl` after `close()`); new test 6
from Step 6 (`close()` called twice does not raise, and no `"observability-drain-worker"` thread survives).

### Step 4 — Kernel worker-count accounting
**Files:** `src/engine/kernel.py`
**Change:**
- Line 305: `self._workers_started = 1 if (obs_mode != ObservabilityMode.OFF) else 0` → `self._workers_started
  = 2 if (obs_mode != ObservabilityMode.OFF) else 0`. Update the preceding comment (line 304, currently "1 =
  EventRecorder._worker (QueueDrainWorker)") to: "2 = EventRecorder._worker + DecisionTraceWriter._worker
  (both QueueDrainWorker instances), started when obs is enabled."
- Close site, lines 1068-1074: the existing block calls `self._decision_trace_writer.close()` inside a
  `try/except` but — unlike the `EventRecorder.shutdown()` call three lines above it (line 1061-1063, which
  does `self._event_recorder.shutdown(); workers_stopped += 1`) — never increments `workers_stopped`. Add
  `workers_stopped += 1` immediately after the existing `try/except` block (unconditionally, mirroring that
  the `except` branch already treats the failure as non-fatal and logs it — the worker's `.stop()` inside
  `close()` still runs regardless of whether `rebuild()` or the file-close raises, so counting it as
  "stopped" is accurate):
  ```python
  if hasattr(self, "_decision_trace_writer") and self._decision_trace_writer:
      try:
          self._decision_trace_writer.close()
      except Exception:
          logger.exception("DecisionTraceWriter.close() failed during shutdown (non-fatal)")
      from src.observability.cognition.decision_trace_writer import set_active_writer
      set_active_writer(None)
      workers_stopped += 1
  ```
  Without this, `report.workers_stopped` (line 1110) stays at 1 even though 2 workers were started and both
  actually stopped, tripping the `workers_stopped < workers_started` check (line 1111-1115) and forcing
  `report.outcome = "PARTIAL"` on every normal LIGHT+ run — a regression this ticket must not introduce.
**Do NOT touch:** the constructor call at lines 288-293 (`DecisionTraceWriter(run_dir=run_dir_str)`,
`set_active_writer(self._decision_trace_writer)`) — signature and call site are unchanged, since all new
queue/worker setup happens inside `DecisionTraceWriter.__init__` itself (Step 1). Do not touch
`self._event_recorder` accounting or its own `workers_stopped += 1` (line ~1063).
**Verify:** new test 7 from Step 7 (`test_lifecycle_supervisor.py`).

### Step 5 — Architecture guard: no file I/O reachable from `write_trace()`
**Files:** `tests/architecture/test_decision_trace_hot_path_no_io.py` (new)
**Change:** New AST/static-analysis test implementing test_plan.md New Test #1 and the ticket's AC #1
directly (no existing test covers this — `test_phase19_hot_path_safety_contract.py` only string-matches
analyzer class names, not I/O calls, and doesn't scan this module). Walk the call graph reachable from
`DecisionTraceWriter.write_trace()` (including anything it calls synchronously, i.e. everything except
calls dispatched through `self._queue.try_push(...)`) and assert no `open(`, `.write(`, `.flush(`, or
`json.dump(` call appears in that reachable set — specifically confirming `DecisionTraceIndex.append_entry()`
is unreachable from `write_trace()` post-Step-1/2. A source-text/AST scan of `write_trace()`'s own function
body (simplest, matches this repo's existing static-check style) is sufficient: assert the compiled function
body contains no `Call` node whose function resolves to `open`, `.write`, `.flush`, or `json.dump`, and that
`self._file` and `self._index.append_entry` are not referenced anywhere inside `write_trace()`'s AST subtree.
**Do NOT touch:** `test_phase19_hot_path_safety_contract.py` — leave it as-is; this is a new, separate file
per test_plan.md's stated preference, not an extension of that one.
**Verify:** the test itself, run standalone first
(`pytest tests/architecture/test_decision_trace_hot_path_no_io.py -v`), then alongside
`test_phase19_hot_path_safety_contract.py` per the scoped command list.

### Step 6 — Unit test updates in `test_decision_trace.py`
**Files:** `tests/unit/observability/test_decision_trace.py`
**Change:** Implements test_plan.md New Tests #2, #3, #4, #6:
- **New:** `write_trace()` performs no synchronous file/`os` calls — mock `builtins.open` and
  `os.makedirs` for the duration of N `write_trace()` calls (no `close()`), assert zero invocations, and
  assert `decision_trace.jsonl` does not exist on disk yet.
- **New:** `get_latest_goal_scores()` returns the just-written top-3 scores immediately after `write_trace()`,
  with no `close()` and no worker drain forced — proves the in-memory cache update (Step 1's untouched block)
  is still synchronous/hot-path-side even though disk I/O is not.
- **Rewrite `test_tick_index_incremental_vs_rebuild`** (currently lines 439-456): this test's premise —
  inspecting `writer._index._index` immediately after `write_trace()` calls and before `close()` — is
  invalid post-Step-1/2, since the index is no longer populated synchronously at that point. **Do not
  simply move both snapshots to after `close()`** — `close()`'s own final step (Step 3) unconditionally
  calls `self._index.rebuild()`, so an after-`close()`-only snapshot on both sides would always be
  identical regardless of whether the worker's incremental `append_entry()` calls ever ran correctly,
  silently losing the test's actual regression-detection purpose (caught on architecture re-review,
  2nd pass). Instead, capture the *incremental* snapshot after the drain completes but *before*
  `close()`'s own explicit `rebuild()` call — drive the drain manually rather than calling the full
  `close()`:
  ```python
  def test_tick_index_incremental_vs_rebuild():
      with tempfile.TemporaryDirectory() as run_dir:
          writer = DecisionTraceWriter(run_dir=run_dir)
          try:
              # ... write_trace() calls as before ...
              writer._worker.stop()
              for item in writer._queue.drain():
                  writer._write_entry_to_file(item)  # populates _index incrementally, no rebuild yet
              incremental_snapshot = dict(writer._index._index)

              writer._index.rebuild()
              rebuilt_snapshot = dict(writer._index._index)

              assert incremental_snapshot == rebuilt_snapshot
          finally:
              writer.close()
  ```
  This restores the original incremental-vs-rebuild equivalence check (proving the worker's
  `_write_entry_to_file` → `append_entry()` path produces the same tick→offset mapping as a full
  `rebuild()` scan) instead of two post-rebuild snapshots compared against each other. This is still the
  "records appear in `decision_trace.jsonl` after shutdown/close" test (test_plan.md New Test #4) in
  spirit — implement it as this rewrite, not a separate new test, per test_plan.md's stated option — but
  the snapshot timing above is load-bearing, not a cosmetic detail.
- **New:** worker lifecycle — (a) creating and closing a `DecisionTraceWriter` (standalone) leaves no
  `"observability-drain-worker"` thread alive after `close()`, checked via
  `tests/tools/memory_probe.py::count_drain_workers()` before/after; (b) calling `close()` twice does not
  raise or double-join.
- **Fix `test_set_and_get_active_writer`** (existing, lines 219-226): this test constructs a
  `DecisionTraceWriter` directly and never calls `.close()` — harmless today (the constructor starts no
  thread), but after Step 1 lands, `__init__` unconditionally starts a `QueueDrainWorker`, so this test
  would leak a live `"observability-drain-worker"` daemon thread for the rest of the pytest session,
  tripping `tests/conftest.py::_observability_worker_thread_sentinel` and directly contradicting AC #5
  ("conftest worker-thread sentinel does not trip"). Wrap the body in `try/finally` (or add an explicit
  `writer.close()` after the assertions) so the worker is always stopped before the function returns:
  ```python
  def test_set_and_get_active_writer():
      with tempfile.TemporaryDirectory() as run_dir:
          writer = DecisionTraceWriter(run_dir=run_dir)
          try:
              set_active_writer(writer)
              assert get_active_writer() is writer
              set_active_writer(None)
              assert get_active_writer() is None
          finally:
              writer.close()
  ```
  Caught during architecture review (pre-implementation) via a full grep of every `DecisionTraceWriter(`
  construction site in `tests/` cross-referenced against every `.close()` call — this was the one
  unpaired construction site.
**Do NOT touch:** any of the runner-up/score tests (`test_decision_trace_runner_up_scores_present`,
`test_decision_trace_source_goal_score_present`, `test_decision_trace_runner_up_fewer_than_3`,
`test_decision_trace_runner_up_single_candidate`, `test_decision_trace_routes_sorted_descending`) or
`test_decision_trace_writer_does_not_import_engine_cognition` — these must pass unmodified as regression
guards for the out-of-scope scoring/`execute_brain()` boundaries.
**Verify:** `pytest tests/unit/observability/test_decision_trace.py -v` (full file green, including all
untouched pre-existing tests).

### Step 7 — Lifecycle supervisor test: worker-count accounting
**Files:** `tests/unit/engine/test_lifecycle_supervisor.py`
**Change:** Implements test_plan.md New Test #7. Add/extend a test in the existing `TestCleanShutdown` /
`TestShutdownReportShape` classes asserting: `Kernel.__init__` with `obs_mode != OFF` sets
`_workers_started == 2`; after a clean `shutdown()`, `ShutdownReport.workers_started == 2` and
`ShutdownReport.workers_stopped == 2` and `report.outcome == "SUCCESS"` (not `"PARTIAL"`) — directly guards
the Step 4 accounting fix and the specific regression named there (workers_stopped under-reporting forcing a
false `PARTIAL` outcome on every LIGHT+ run).
**Do NOT touch:** `TestBehaviorWorkerShutdown`, `TestSurvivalCountsInReport`,
`TestPendingReplayFlushesWarning` — unrelated existing coverage, must stay green unmodified.
**Verify:** `pytest tests/unit/engine/test_lifecycle_supervisor.py -v`.

### Step 8 — Determinism integration test
**Files:** `tests/integration/observability/test_decision_trace_determinism.py` (new)
**Change:** Implements test_plan.md New Test #5 / ticket AC #4. Run the same seeded scenario twice
end-to-end (through `Kernel` init → tick loop → `shutdown()`), each into its own run directory, and assert
the two resulting `decision_trace.jsonl` files are identical in per-tick entry order (line-set-identical,
preserving order) — proving the async drain (`BoundedObservabilityQueue.drain()` full-list-drain +
`QueueDrainWorker`'s single-threaded sequential dispatch, both unmodified primitives) does not introduce
reordering relative to the single-threaded-per-tick producer (`AdventureDecisionPhase.apply()`).
**Determinism caveat — required, caught on architecture re-review (2nd pass):** strict FIFO ordering is
only guaranteed for items that are actually pushed onto the queue. `_DecisionTraceQueueItem.severity` is
hardcoded to `"INFO"` (Step 1), so `BoundedObservabilityQueue.try_push()`'s `is_high_priority` check is
always `False` for trace entries — on overflow (queue depth reaches `max_size`), the new item is silently
dropped (`queue.py`'s low-priority-drop branch), not evicted-and-reordered. Dropped-on-overflow is a
genuine, real non-determinism source independent of the crash-loss window (Step 9) — it depends on actual
producer/drain-worker thread-scheduling timing, not a process kill — and the test as originally scoped
(assert byte-identical output across two runs) would only incidentally pass at small scale rather than
proving the invariant. The test **must** assert queue occupancy never approaches `max_size` during the
run (e.g. instrument via a small `max_size` override plus a occupancy-high-water-mark counter exposed by
`BoundedObservabilityQueue`, or by choosing a scenario/tick-count combination with a comfortable headroom
margin and asserting `dropped_count == 0` on the queue after the run) — a passing determinism test must be
a proven invariant, not scale-dependent luck. Document this constraint in the test's own top-of-file
comment so a future scenario-size change doesn't silently reintroduce flakiness.
**Do NOT touch:** any existing scenario-determinism suite — this is a new, narrowly-scoped file per
test_plan.md's stated preference.
**Verify:** `pytest tests/integration/observability/test_decision_trace_determinism.py -v`.

### Step 9 — Resolve and document the crash-loss-window decision
**Files:** `docs/guidelines/intentional_divergences.md`, `tests/unit/observability/test_decision_trace.py`
(or a lightweight docs-consistency test file, implementer's choice per existing convention)
**Change: Decision (resolves the ticket's Assumptions/Open Questions item and investigation.md's Risk
"Crash-loss window").** Accept a small, bounded crash-loss window: any queued-but-not-yet-drained
`decision_trace.jsonl` records at the moment of an unclean process kill are lost, bounded by
`QueueDrainWorker`'s default `interval_sec=0.01s` drain cadence and the queue's `max_size` (Step 1). No
periodic off-path fsync/force-drain mechanism is introduced. **Rationale:** (a) `EventRecorder` already
carries the identical crash-loss profile on the identical `BoundedObservabilityQueue`/`QueueDrainWorker`
primitive for `simulation_events.jsonl`, and that has been accepted, shipped precedent with no fsync
mechanism of its own — introducing one only for the trace writer would be an unexplained, unjustified
inconsistency between two components using the same underlying pattern; (b) the ticket's own Assumptions
section already names this as the expected fallback-avoidance outcome ("crash-loss window... is acceptable
if documented"), and no contract owner has recorded disagreement anywhere in the repo. Add a new entry to
`docs/guidelines/intentional_divergences.md` with rationale class `Bounded`: describe the window precisely
(bounded by `interval_sec` and queue depth, not unbounded), name this ticket ID, and cite the verification
test path (Step 8's determinism test plus Step 6's close/drain test demonstrate the buffered-vs-persisted
boundary behaves as documented). **The same entry must also name a second, distinct divergence** (caught on
architecture re-review, 2nd pass): under sustained queue saturation (occupancy at `max_size`), new
decision-trace entries are silently dropped rather than blocking the hot path — a real, design-level
non-determinism/data-loss source independent of the crash-loss window above, bounded by `max_size` and
consistent with `EventRecorder`'s already-accepted precedent for `simulation_events.jsonl` on the identical
primitive. Both divergences share one rationale class (`Bounded`) and may be documented as two bullets
under the same entry rather than two separate entries. Add a light docs-consistency test (per
`test_phase19_hot_path_safety_contract.py::test_hot_path_safety_contract_doc_exists`'s precedent for
doc-presence assertions) asserting `docs/guidelines/intentional_divergences.md` contains a substring
referencing `TCK-20260702-OBSISO-TRACE-ASYNC`, so this documentation requirement cannot silently regress.
**Do NOT touch:** any other existing entry in `intentional_divergences.md` — append only.
**Verify:** the new docs-consistency test; manual read-through confirming the entry names a rationale class
and a verification path per the file's existing entry format.

### Step 10 — Update `docs/observability/decision_trace_contract.md`
**Files:** `docs/observability/decision_trace_contract.md`
**Change:** Rewrite the "Implementation Notes" and "Tick Index Sidecar → Lifecycle" sections (per
investigation.md's Docs Requiring Update) to describe the new architecture: `write_trace()` is a bounded
in-memory enqueue only; a private `QueueDrainWorker` performs the actual `decision_trace.jsonl` write and
`DecisionTraceIndex.append_entry()` call off-path; `close()` stops the worker, synchronously drains any
remainder, closes the file, and rebuilds the index. Remove the now-false claim that
`append_entry(tick, offset)` is "called from `write_trace()` after each flush." Add a subsection describing
the accepted crash-loss window from Step 9, cross-referencing the `intentional_divergences.md` entry.
**Do NOT touch:** any section describing the read path (`get_latest_goal_scores()`, REST API / `lookup()`
behavior) — those are unaffected and must not be reworded to imply a change that didn't happen.
**Verify:** manual read-through against the actual Step 1-3 code; no automated test targets prose content
directly, but Step 9's docs-consistency test pattern may be reused if a stronger check is wanted (optional,
not required by any AC).

### Step 11 — Update `docs/parity_ledger/infrastructure.yaml` (INFRA-211, INFRA-212)
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Per the Authoritative Mechanics Rule's Parity clause and investigation.md's Parity Ledger
Overlap findings — update `v2_evidence`/`text` on the existing entries, do not add new entries:
- **INFRA-211** (lines ~2392-2401, "Decision trace writer (LIGHT+ mode)"): update `v2_evidence` to describe
  the buffer-append (`write_trace()`) + async-drain-write (`_write_entry_to_file` via `QueueDrainWorker`)
  split, instead of citing `DecisionTraceWriter.write_trace` alone as the synchronous-write mechanism. Keep
  `test_path: tests/unit/observability/test_decision_trace.py::test_decision_trace_runner_up_scores_present`
  (still valid and passing per Step 1's "Do NOT touch" guard) or add the Step 5 architecture-guard test path
  alongside it. Keep `status: verified`.
- **INFRA-212** (lines ~2402-2411, "Decision trace tick-index sidecar (Epic 2.2B)"): rewrite `text` to
  remove the "updated incrementally on each write_trace() call" claim and describe incremental updates as
  occurring on the worker's drain cadence instead. Keep
  `test_path: tests/unit/observability/test_decision_trace.py::test_tick_index_o1_lookup` (still valid,
  unmodified per Step 2's guard) and consider adding the rewritten
  `test_tick_index_incremental_vs_rebuild` (Step 6) as a second cited path. Keep `status: verified`.
**Do NOT touch:** any other entry in `infrastructure.yaml`; do not change `priority` (both stay `P1`); do
not add new `id`s for this change — it is an update to two existing entries.
**Verify:** re-run the two cited `test_path`s after all code steps land (Steps 1-8) and confirm still
passing before committing the ledger edit, per the repo's "any status change needs a passing test_path"
rule.

### Step 12 — Mark G4 resolved in `docs/plans/observability_process_isolation.md`
**Files:** `docs/plans/observability_process_isolation.md`
**Change:** In the "Gaps" section (G4, lines ~60-63 per investigation.md), mark G4 resolved and
cross-reference `TCK-20260702-OBSISO-TRACE-ASYNC` as the closing ticket, so the epic-tracking doc does not
keep describing now-fixed code as contract-violating. Do not alter G1/G2/G3/G5 or any other section — those
remain open, tracked by the sibling tickets in `tickets/todos/obs-isolation/`
(`TCK-20260702-OBSISO-BROKER-CONFIG`, `TCK-20260702-OBSISO-WORKER-PARITY`,
`TCK-20260702-OBSISO-ISOLATION-PROOF`) and the epic `TCK-20260702-OBSISO-EPIC`.
**Do NOT touch:** any other Gap entry or section of this doc.
**Verify:** manual read-through; no automated test targets this doc's prose.

## Scope Guards

Reiterating the ticket's Out of Scope section and investigation.md's Anti-Drift Hazards, made concrete per
file:

- **`src/observability/trace.py`** (`DecisionTrace`/`DecisionOptionTrace`/`RejectedOptionTrace`, the
  unrelated "Phase 17" causal-decision-trace system) — do not touch. `test_phase17_decision_trace_contract.py`,
  `test_phase17_decision_trace_validator.py`, `tests/integration/scenarios/test_phase17_decision_trace_scenarios.py`
  are a naming collision only; they must stay green and unmodified as a sanity check that this ticket did
  not accidentally pull them into scope.
- **`src/api/routes/decisions.py`** — explicitly out of scope per the ticket. `DecisionTraceIndex.lookup()`
  (its read path) is untouched by Step 2 — only `append_entry()`'s caller relocates, `lookup()`'s logic does
  not change.
- **`execute_brain()` / `src/engine/domain/cognition`** — not modified. `test_decision_trace_writer_does_not_import_engine_cognition`
  (existing, `test_decision_trace.py:277-296`) must keep passing verbatim as the enforcement mechanism.
- **P1-H goal-layer runner-up retention logic** (`decision_trace_writer.py` lines 88-106, the
  scoring/rank/cache-building block inside `write_trace()`) — untouched; this is a separate concern per
  `docs/plans/audit_fix_plan.md`. Step 1 only changes what happens *after* `entry` is built.
- **`DecisionTraceIndex.append_entry()`, `_flush()`, `rebuild()`, `lookup()`, `_load()` bodies** — no logic
  changes in `tick_index.py` anywhere in this plan (Step 2 is docstring-only). Do not "improve" or refactor
  these methods while relocating their caller.
- **The global observability queue singleton** (`get_observability_queue()` / `get_or_start_global_worker()`,
  `queue.py:164-190`) — do not use. `DecisionTraceWriter` gets its own private `BoundedObservabilityQueue`/
  `QueueDrainWorker` instance, per the `EventRecorder` precedent, not the global singleton.
- **`src/domains/adventure/phase.py`** — no change. The fix is entirely inside `DecisionTraceWriter`; the
  call site (`phase.py:120`, `_writer.write_trace(hero.id, tick, scored_candidates)`) keeps calling the same
  method with the same signature.
- **Trace record schema / REST endpoints** — no field added, removed, or renamed in the `entry` dict shape;
  `src/api/routes/decisions.py` unaffected (see above).
- **`tests/unit/engine/test_lifecycle_supervisor.py`'s `TestBehaviorWorkerShutdown`, `TestSurvivalCountsInReport`,
  `TestPendingReplayFlushesWarning`** — unrelated existing coverage, must stay green unmodified.
- **`EventRecorder`'s own accounting** (`_event_recorder.shutdown()`, its `workers_stopped += 1` at
  kernel.py ~1063) — not touched by Step 4; only the `DecisionTraceWriter` close block and the
  `_workers_started` initial value change.

## Dependency Map

- Step 2 depends on Step 1 (the `append_entry()` relocation happens inside the `_write_entry_to_file`
  callback introduced in Step 1; cannot be implemented first).
- Step 3 depends on Steps 1-2 (close()'s worker-stop/drain lifecycle needs the queue/worker/callback to
  exist).
- Step 4 (Kernel wiring) is implementable independently of Steps 1-3's internal `DecisionTraceWriter` code
  (it only touches `kernel.py`), but should be sequenced after Step 3 so its "2 workers, both stopped"
  accounting matches a finished `close()` implementation rather than a half-built one.
- Step 5 depends on Steps 1-2 (asserts the post-fix call-graph shape).
- Step 6 depends on Steps 1-3 (exercises the finished enqueue/worker/close lifecycle).
- Step 7 depends on Step 4 (asserts the corrected `_workers_started`/`workers_stopped` values).
- Step 8 depends on Steps 1-3 (exercises the finished writer end-to-end through a real `Kernel` run).
- Step 9 is independent of Steps 1-8 code-wise (a decision + doc + light test) but should land before Step
  10, since Step 10's contract-doc rewrite references the crash-loss-window language Step 9 establishes.
- Step 10 depends on Steps 1-3 (describes actual new behavior) and Step 9 (crash-loss window language).
- Step 11 depends on Steps 1-8 being complete and green (cites their test paths as `v2_evidence`/`test_path`
  before re-affirming `status: verified`).
- Step 12 depends on all prior steps being complete (marks the gap resolved only once it actually is).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — No file IO reachable from `write_trace()` on the phase call path (static check) | Steps 1, 2 | `tests/architecture/test_decision_trace_hot_path_no_io.py` (Step 5) |
| AC #2 — `test_decision_trace.py` updated/passing: records appear in `decision_trace.jsonl` after shutdown; tick-index lookup still O(1); `get_latest_goal_scores()` returns current values mid-run before any flush | Steps 1, 2, 3 | Rewritten `test_tick_index_incremental_vs_rebuild`, new "get_latest_goal_scores before flush" test, `test_tick_index_o1_lookup` (unmodified, Step 6) |
| AC #3 — Entity inspector integration unaffected: `test_entity_inspector.py` passes unchanged | No step touches `entity_inspector.py` or `get_latest_goal_scores()`'s signature/behavior (Scope Guard) | `pytest tests/unit/observability/test_entity_inspector.py -v` (regression run, zero diff expected) |
| AC #4 — Determinism: two same-seed runs produce identical `decision_trace.jsonl` content, ordering included | Steps 1-3 (unmodified FIFO-preserving `BoundedObservabilityQueue.drain()`/`QueueDrainWorker` primitives) | `tests/integration/observability/test_decision_trace_determinism.py` (Step 8) |
| AC #5 — Worker lifecycle: conftest sentinel does not trip; `shutdown()`/`close()` idempotent | Steps 3, 4 | New worker-lifecycle test (Step 6), `test_lifecycle_supervisor.py` worker-count test (Step 7), existing `tests/conftest.py::_observability_worker_thread_sentinel` (regression, must not trip) |

## Anti-Drift Notes

- **The `_DecisionTraceQueueItem.severity` field is cosmetic, not semantic.** `BoundedObservabilityQueue`'s
  eviction logic treats it as a real priority signal for `ObservabilityEventEnvelope`s; for decision-trace
  entries it exists only so `try_push()` doesn't raise `AttributeError` on overflow. Do not build any actual
  priority/dropping behavior around this field for trace entries — if the queue overflows, whichever entry
  the shared eviction logic picks is fine; do not special-case it.
- **`workers_stopped += 1` at the Step 4 close site must be unconditional** (outside/after the `try/except`,
  not inside the `try`), matching the reasoning that `.close()`'s internal `.stop()` call on the worker
  thread still runs even if a later step inside `close()` (e.g. `rebuild()`) raises. Getting this
  conditional would silently reintroduce the exact `PARTIAL`-outcome regression this step exists to fix.
- **Do not conflate Step 2's "missed scope" fix with a `tick_index.py` logic change.** The entire fix is a
  caller relocation (accomplished mechanically by Step 1's restructuring) plus docstring corrections. Any
  temptation to "also clean up" `append_entry()`/`_flush()` while touching this file is out of scope and
  risks the O(1) `lookup()` guarantee AC #2 depends on.
- **Determinism (AC #4) is a proof of unmodified-primitive behavior, not new code.** `BoundedObservabilityQueue.drain()`
  (`queue.py:69-76`) is a strict FIFO list-drain, and `AdventureDecisionPhase.apply()` is single-threaded per
  tick — Step 8's test exists to confirm this holds under the new async path, not to add new ordering logic.
  If the test fails, the bug is most likely in how `entry`/`item` construction interacts with the queue, not
  a fundamental gap requiring new synchronization primitives.
- **Crash-loss window (Step 9) is a documentation and precedent-consistency decision, already resolved in
  this plan** — do not re-litigate it during implementation or add an off-path fsync mechanism `EventRecorder`
  itself doesn't have. If a reviewer disagrees post-implementation, that is a follow-up ticket, not a
  mid-implementation scope change.
- **INFRA-211/INFRA-212 (Step 11) update existing entries only** — verify both entries' cited `test_path`s
  actually pass before editing `status`/`v2_evidence`/`text`, per the repo's parity rule that any status
  change needs a passing test_path.

## Deviations

All 12 steps were implemented exactly as specified, in the dependency order given. One deviation
was required beyond the 12 steps:

- **Unplanned fix: `tests/integration/observability/test_initial_placement_check.py`.** Running
  the full `tests/integration/observability/` suite together with
  `tests/unit/engine/test_lifecycle_supervisor.py` surfaced a real `_observability_worker_thread_sentinel`
  failure ("2 thread(s) remained after test session"). Root cause:
  `test_check_initial_placement_mode_gating_matches_precedent` deliberately constructs `Kernel(...)`
  in `ObservabilityMode.DEBUG`/`CERTIFICATION`, where `Kernel.__init__` raises
  `HardLawViolationError` mid-construction (fail-fast on `LAW-SPAWN-OCCUPANCY`) — `__init__` has no
  exception-safe teardown for anything constructed before the raise point. This was already a known,
  documented gap for `EventRecorder` (the test's own comment names it), reclaimed via
  `gc.get_objects()` + `.shutdown()` in the test's `finally` block. Step 1 makes
  `DecisionTraceWriter.__init__` unconditionally start a `QueueDrainWorker` too (previously it
  started no thread at all — the file was opened lazily on first write), and
  `DecisionTraceWriter` is constructed before the raise point in `Kernel.__init__` (line ~292,
  before the raise at line ~322), so the same fail-fast path now leaks a second worker per
  DEBUG/CERTIFICATION iteration. Fixed by extending the test's gc-reclaim loop to also match
  `DecisionTraceWriter` instances and call `.close()` on them. This is not scope creep — it is a
  direct, unavoidable consequence of Step 1's behavior change, and required to satisfy AC #5 (the
  conftest worker-thread sentinel must not trip). See
  `tickets/inprogress/TCK-20260702-OBSISO-TRACE-ASYNC.md` Implementation Notes for the full
  before/after.

No other deviations. `tests/integration/kernel/test_long_run_determinism.py::test_1000_tick_determinism`
and 2 `test_export_flow.py` failures observed during regression runs were verified pre-existing and
unrelated (confirmed against a clean `git worktree` checkout of pre-ticket `HEAD`) — no fix applied,
none required by this ticket's scope.
