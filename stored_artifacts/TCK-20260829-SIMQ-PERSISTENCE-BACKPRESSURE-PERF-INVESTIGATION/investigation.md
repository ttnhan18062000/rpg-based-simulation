---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION
artifact_type: investigation
tags: [performance, observability, simulation-quality]
---

# Investigation — TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION

## Current Behavior

### Context-search note (Step 0c)
`mcp__knowledge-search__search_docs` was tried with the query `"persistence phase telemetry I/O
overhead backpressure EventRecorder QueueDrainWorker"` and returned `{"error":"index not found"}`
— confirmed broken/missing index, as pre-flagged. Per the dispatch instructions this is a known,
pre-confirmed condition; `make knowledge-index`/`make knowledge-index-update` were intentionally
NOT run (out of scope for this ticket). `graphify query "persistence phase telemetry EventRecorder
QueueDrainWorker backpressure"` was run and returned the real node set (`QualityPersistence`
`src/simulation_quality/persistence.py:14`, `EventRecorder` `src/observability/event_recorder.py:56`,
`BoundedObservabilityQueue` `src/observability/queue.py:14`, `Kernel` `src/engine/kernel.py:35`,
`ObservabilityConfig`/`ObservabilityMode` `src/observability/config.py`, `calibrate_simq.py`) — used
as the primary file-target list for the follow-up direct reads below, per CLAUDE.md's Context Scan
step-4 fallback (`tickets/`, `docs/`, `stored_artifacts/`, code/tests).

### The "persistence" tick-phase, precisely
The ticket's own framing (and its title) treats "persistence/telemetry I/O" as one bucket. Reading
the actual code shows **two genuinely separate subsystems** sit under that name, with different
root causes. This distinction is the central finding of this investigation.

**1. The `persistence` tick-phase, as literally measured and reported in the WatchdogTrip evidence**
(`src/engine/kernel.py:1158` `_phase_persistence()`, timed at `kernel.py:434-436`) does only two
things:
```python
def _phase_persistence(self) -> None:
    tick_hash = "SKIPPED"
    if self._current_policy.replay_allowed and (self._audit_mode or self._current_policy.replay_richness == "FULL"):
        from src.engine.checkpoint import CanonicalStateHasher
        tick_hash = CanonicalStateHasher.get_hash(self._state)          # kernel.py:1162
    if self._current_policy.replay_allowed:
        self._replay.emit(TraceEvent(...), self._current_policy)        # kernel.py:1165-1170
    self._replay.on_tick_end(self._state.tick)                          # kernel.py:1172
```
It does **not** call `QualityPersistence.write()` or `EventRecorder._write_envelope_to_file()` at
all — those happen through a separate, mostly-async pipeline (see part 2 below). The
`persistence`-phase cost the ticket's WatchdogTrip evidence quotes (60-120ms/tick, spiking to
39-243ms in this investigation's own real runs) is entirely `CanonicalStateHasher.get_hash()` plus
`ReplayManager.on_tick_end()` / `_rotate_chunk()`.

**2. `QualityPersistence`/`EventRecorder` telemetry I/O** (`src/simulation_quality/persistence.py`,
`src/observability/event_recorder.py`) is a separate pipeline, mostly running on the background
`QueueDrainWorker` daemon thread (`src/observability/queue.py:87-154`), and is the direct cause of
the `CalibrationIntegrityError` (queue overflow / SURVIVAL mode-shed) — not of the `persistence`
tick-phase's own reported cost.

### Real profiling (cProfile, real unmocked Kernel-driven run)
Ran `tools/calibrate_simq.py::_run_engine("urban_political", seed=42, ticks=500)` twice: once under
`cProfile` for function-level attribution, once "clean" (no profiler) reading the Kernel's own
`_phase_costs` dict after every `tick_once()` for un-inflated absolute numbers. Both used the exact
harness the failing grade-stability tests drive (same `_run_engine`, same `no_frame_pacing=True`,
same feature-flag loading). Scripts and raw `pstats` are in the scratchpad
(`/tmp/claude-1000/.../scratchpad/profile_persistence.py`, `clean_baseline.py`) — not part of the
repo diff.

**Clean (no-profiler) run — 500 ticks, urban_political seed42, real Kernel:**
```
Clean (no cProfile) run: 500 ticks in 14.58s wall (29.15ms/tick avg)
persistence phase: mean=8.891ms median=7.307ms p90=10.572ms max=243.150ms min=0.005ms sum=4445.7ms
all-other-phases:  mean=21.418ms median=16.637ms p90=35.105ms max=170.713ms
total tick cost:   mean=30.309ms median=24.866ms max=261.612ms
persistence share of total tick cost (sum): 29.3%

Top 10 most expensive persistence-phase ticks:
  tick 200: persistence=243.150ms total=261.612ms
  tick 402: persistence=229.162ms total=248.073ms
  tick 301: persistence=195.284ms total=209.671ms
  tick 468: persistence=71.226ms total=100.113ms
  tick 375: persistence=67.447ms total=85.826ms
  tick 450: persistence=63.370ms total=83.574ms
  tick 282: persistence=62.367ms total=76.976ms
  tick 338: persistence=61.922ms total=80.246ms
  tick 190: persistence=59.313ms total=74.137ms
  tick 263: persistence=57.302ms total=73.417ms
```
The three dominant spikes (tick 200: 243ms, tick 402: 229ms, tick 301: 195ms) land almost exactly
100 ticks apart. This is not coincidental — `ReplayManager.__init__`'s default
`chunk_tick_limit=100` (`src/engine/replay_manager.py:36`) rotates the replay trace-event buffer to
a durable chunk every 100 ticks via `on_tick_end()` → `_rotate_chunk()` (`replay_manager.py:106-119,
176`), called synchronously from inside `_phase_persistence()`. The earlier cProfile run (below)
independently reproduced the same ~100-tick periodicity in its own WatchdogTrip warnings (ticks 102,
201-202, 302-303, 403, 421 — i.e. clustering right after each 100-tick chunk boundary).

**cProfile run — same scenario, 500 ticks (27.638s profiled, `pstats` sorted by cumulative and by
self/`tottime`):**
```
44494002 function calls (41665008 primitive calls) in 27.638 seconds
Ordered by internal time (tottime — most reliable signal for real CPU-bound work):
tottime  cumtime  function
2.182s   13.230s  src/engine/replay_sink.py:35 (_clean_for_json)     [788184 calls]
1.660s    4.986s  dataclasses.py:1325 (_asdict_inner)                 [1761900 calls]
0.965s    1.448s  src/engine/apply.py:8 (replace)
0.707s   22.753s  {method 'flush' of '_io.TextIOWrapper'}             [9773 calls]
0.593s    0.899s  src/simulation_quality/quality_hub.py:183 (_build_context)
0.535s    0.796s  src/observability/event_recorder.py:151 (record)    [5432 calls]
0.255s    1.875s  src/engine/checkpoint.py:62 (to_canonical_data)     [276 calls]

Filtered (persistence/checkpoint/observability/replay), ordered by cumulative:
      1    0.003    0.003   27.051   27.051  kernel.py:1174 (shutdown)
      1    0.000    0.000   27.051   27.051  replay_manager.py:121 (finalize)
   4237    0.041    0.000   23.077    0.005  src/simulation_quality/persistence.py:27 (write)
    500    0.009    0.000    5.185    0.010  kernel.py:1158 (_phase_persistence)
    589    0.004    0.000    5.611    0.010  replay_manager.py:279 (_to_dict)
    276    0.003    0.000    2.861    0.010  checkpoint.py:51 (to_canonical_json)
      5    0.007    0.001    1.588    0.318  replay_manager.py:176 (_rotate_chunk)
    276    0.005    0.000    1.572    0.006  checkpoint.py:43 (get_hash)
    500    0.001    0.000    1.241    0.002  replay_manager.py:106 (on_tick_end)
   5432    0.535    0.000    0.796    0.000  event_recorder.py:151 (record)
```
Note: `cumtime` figures for thread-crossing/blocking calls (`queue.py:120 stop`, `on_envelope`,
`.flush()`) are inflated beyond the 27.6s wall-clock total — a known `cProfile` artifact where a
blocking call that releases the GIL (`Thread.join`, a real `write()` syscall) lets other threads
run concurrently, and that concurrent work gets folded into the blocking call's own `cumtime`. Only
`tottime` (self time) and `ncalls` are trustworthy across that boundary; they are what the two
bullets below are based on.

### Root cause #1 (the dominant, spiky driver of `persistence`-phase cost): a redundant synchronous
JSON serialization inside `ReplayManager._rotate_chunk()`
`_rotate_chunk()` (`src/engine/replay_manager.py:176-246`) correctly offloads the actual chunk
write to a background `ThreadPoolExecutor(max_workers=1)` (`self._executor.submit(self._execute_persistence, ...)`,
lines 228-235) — that part is already non-blocking, as the M7 Law comment claims. But **before**
that submission, lines 185-207 do this, synchronously, on the main tick thread:
```python
def _to_dict(e):
    if isinstance(e, dict): return e
    if dataclasses.is_dataclass(e) and not isinstance(e, type): return dataclasses.asdict(e)
    if hasattr(e, '__dict__'): return e.__dict__
    return str(e)
estimated_bytes = len(json.dumps([_to_dict(e) for e in events], default=str).encode())
_bcheck = get_default_registry().check("replay_chunk", estimated_bytes)
if _bcheck.action in ("warn", "reject"):
    logger.warning(...)
```
This fully serializes the entire ~100-tick chunk buffer (potentially thousands of `TraceEvent`s)
purely to estimate a byte size for a budget-check *warning log* — duplicating, on the blocking main
thread, work that `_execute_persistence()` → `RunArtifactRepository`'s sink (`src/engine/replay_sink.py:35
_clean_for_json`, `:61 persist_chunk`) is about to redo properly, asynchronously, moments later.
`_clean_for_json` is the single largest `tottime` entry in the whole profiled run (2.182s self time,
788184 calls) and — per the filtered listing — `_rotate_chunk` itself accounts for 1.588s cumulative
across only 5 calls (avg ~318ms/call under profiler overhead; ~150-243ms/call in the clean run).
This is the direct mechanism behind the ~100-tick-periodic spikes.

### Root cause #2 (steady per-tick baseline, ~7-9ms/tick, and the actual `CalibrationIntegrityError`
driver): unconditional per-record `flush()` in both write paths
- `QualityPersistence.write()` (`src/simulation_quality/persistence.py:27-45`) calls
  `self._file_handle.write(...)` then `self._file_handle.flush()` **after every single
  `ScoreRecord`** — no batching, no interval. 4237 calls in the 500-tick profiled run.
- `EventRecorder._write_envelope_to_file()` (`src/observability/event_recorder.py:109-127`) does
  the identical pattern for every `ObservabilityEventEnvelope` drained by `QueueDrainWorker`. 5432
  calls in the same run.
- `QueueDrainWorker._run()` (`src/observability/queue.py:126-154`) drains the
  `BoundedObservabilityQueue` on a fixed 10ms cadence (`interval_sec=0.01`) and, per drained
  envelope, calls `file_write_fn` (the flush above) + `stream_publish_fn` +
  `quality_fn`/`on_envelope` synchronously, all inside that single background thread. If per-event
  processing cost (dominated by the unconditional syscall-per-record `flush()`) times the queued
  count exceeds the 10ms drain interval during a burst, the queue fills faster than it drains and
  grows toward `BoundedObservabilityQueue.max_size` (`EventRecorder`'s `max_events=5000` default;
  `DEFAULT_OBSERVABILITY_BUDGET.max_queue_items=10000`), eventually tripping
  `ObservabilityController`'s SURVIVAL threshold (`fill_ratio >= 1.00`,
  `src/observability/event_recorder.py:23-54`) and `BoundedObservabilityQueue.try_push()`'s
  drop/evict path (`src/observability/queue.py:28-67`) — exactly the two loss mechanisms
  `tools/calibrate_simq.py::_run_engine`'s hard-fail guard checks
  (`dropped_count == 0 and mode == "NORMAL" and not survival_triggered`, `calibrate_simq.py:305-309`,
  documented as `INFRA-320`). This — not the kernel `persistence`-phase cost itself — is the direct
  mechanism behind the `CalibrationIntegrityError` the ticket quotes.

In the 500-tick profiled run here, `guard_passed` was True (no drops/SURVIVAL) — consistent with
the ticket's report that 1000-tick runs (roughly double the chunk-rotation spikes, roughly double
the event volume and drain-worker load) are what actually trip the guard; 500 ticks did not
reproduce the failure but did reproduce and quantify both root-cause mechanisms.

### `CanonicalStateHasher.get_hash()` — real cost, but a *documented, verified* contract, not a bug
`get_hash()`/`to_canonical_json()`/`to_canonical_data()` (`src/engine/checkpoint.py:38-107`) do a
full canonical-JSON walk of the entire `AuthoritativeState` (every entity, region, building, corpse,
ground item, chest, group, home_storage, camp, blocked/town tiles) plus a SHA-256 hash, every tick
where `replay_allowed and (audit_mode or replay_richness == "FULL")`. `GovernorPolicy.from_mode`
(`src/engine/policy.py:88,109`) sets `replay_richness="FULL"` for both NORMAL and CONSTRAINED modes
— the common case — so in practice this ran on 276/500 ticks (55.2%) of this investigation's clean
run. **This is not an oversight**: `docs/parity_ledger/infrastructure.yaml`'s `INFRA-223` entry
(status `verified`, priority P2) and `docs/engine/known_limitations.md` §2.4 /
`docs/engine/kernel.md` (lines 111-134 / 114-130 respectively) explicitly document "NORMAL and
CONSTRAINED modes use replay_richness="FULL" and therefore compute the canonical hash every tick."
Separately, a `BudgetedCanonicalHasher` wrapper exists (`checkpoint.py:110-155`,
`DEFAULT_HASHING_BUDGET.max_full_hashes_per_100_ticks=10`) that rate-limits full hashes to 10 per
100 ticks — but `Kernel._phase_persistence()` calls `CanonicalStateHasher.get_hash()` directly, not
through this wrapper, so the wrapper's 10%-of-ticks budget is never actually applied on this path.
Changing that would be a real, deliberate divergence from a `verified` parity-ledger contract (see
Risks/Open Questions and the Docs section below) — Investigate is flagging it, not deciding it.

## Mechanics / Engine Constraints
- `docs/engine/kernel.md` (7-phase loop: Init → Scheduling → Collection → Resolution → Cleanup →
  Advancement → Persistence) — `PERSISTENCE _(non-authoritative)_` row: `entity, world, events →
  replay`. Persistence is explicitly non-authoritative; nothing here may become an authoritative
  mutation path.
- `docs/engine/kernel.md` lines 111-134 and `docs/engine/known_limitations.md` §2.4 — the canonical
  hash cadence-by-mode table (NORMAL/CONSTRAINED → SHA-256 every tick, DEGRADED → "SKIPPED",
  SURVIVAL → no TICK_END event at all). Any fix that changes hash cadence in NORMAL/CONSTRAINED mode
  must update both.
- `docs/engine/performance_contract.md` §2.3 requires the engine to report cost of each authoritative
  phase separately (INIT/SCHEDULING/COLLECTION/RESOLUTION/CLEANUP/ADVANCEMENT are listed;
  PERSISTENCE is the 7th, non-authoritative phase per `kernel.md` and is exactly what
  `_phase_costs["persistence"]` already reports — the instrumentation this investigation relied on
  is itself contract-compliant and needed no changes).
- M6 Law (`replay_manager.py` docstring): "Replay management is non-blocking and respects resource
  bounds." The redundant synchronous serialization in `_rotate_chunk()` (Root cause #1) is in
  tension with this law's intent even though the actual chunk *write* is correctly async — the
  *budget pre-check* is not.
- M7 Law ("Bounded non-authoritative flush budget"), cited in `ReplayManager.finalize()` — governs
  shutdown-time flush behavior, not directly implicated here but relevant context for any fix
  touching `_rotate_chunk`/`finalize`.

## Docs Requiring Update
None. No doc requires a change **for this investigation itself** — no code was modified, so no
described behavior actually diverged from what the docs already say. Whichever fix Plan selects
will very likely require updates; recording that expectation here rather than as a Format-1 bullet,
since nothing has changed yet:

The `docs/parity_ledger/infrastructure.yaml` `INFRA-223` entry, `docs/engine/known_limitations.md`
§2.4, and `docs/engine/kernel.md`'s hash-cadence table (all under `docs/`) are **not required to
change by this investigation** — they accurately describe current, unmodified behavior. They
**would** need updating (`v2_evidence` re-verification for INFRA-223, plus a new
`docs/guidelines/intentional_divergences.md` entry) only if Plan/Implement chooses the
"route through `BudgetedCanonicalHasher`" option for the canonical-hash cost — a decision this
investigation is explicitly not making (see Risks below).

`docs/engine/performance_contract.md` (Hardware Classes A/B/C, scaling limits) is not required to
change either: it defines *how* performance must be measured/reported, and the existing
`_phase_costs`/WatchdogTrip instrumentation already satisfies that contract; this investigation
found a bottleneck using the contract's own instrumentation, it did not find the contract itself
incomplete or wrong.

If Plan selects a fix for Root cause #1 (`_rotate_chunk`'s redundant synchronous serialization) or
Root cause #2 (unconditional per-record `flush()`), those are internal implementation-efficiency
changes with no documented behavioral contract describing the old (slow) shape specifically as
required — no parity ledger entry or Mechanics Bible chapter asserts "the budget pre-check must
fully serialize the chunk" or "every JSONL record must be flushed individually." Those fixes would
not need a `docs/` update beyond ordinary changelog-style notes Implement/Finalize would add anyway.

## Parity Ledger Overlap
- `INFRA-223` (`docs/parity_ledger/infrastructure.yaml`, status `verified`, priority P2) — directly
  overlaps: it is the entry documenting the canonical-hash-every-tick-in-NORMAL/CONSTRAINED-mode
  behavior this investigation profiled. `test_path: tests/integration/kernel/test_determinism_suite.py`
  exists and is a real file. Any change to hash cadence must update this entry's `v2_evidence` and
  keep it passing (P2, not P0, but still governed by the "docs and code must remain in 100% semantic
  parity" rule).
- `INFRA-199` (`docs/parity_ledger/infrastructure.yaml`) — documents the four dynamic observability
  modes (NORMAL/PRESSURE/DEGRADED/SURVIVAL) and their queue-fill thresholds
  (`test_path: tests/unit/observability/test_obs_backpressure.py`). Directly overlaps with the
  "is the SURVIVAL threshold tuned appropriately" question this ticket's Scope asks — see Risks.
- `INFRA-194` — `EventRecorder.pressure_report()` WARN/DEGRADED thresholds at 80%/100% of
  `max_queue_items`. Overlaps with the queue-capacity-tuning side of the same question.
- `INFRA-198` — `ReplayManager` in-flight async persist task tracking (`_inflight_count`,
  `test_path: tests/unit/engine/test_replay_backpressure.py`). Directly overlaps with Root cause #1's
  file (`_rotate_chunk`/`_execute_persistence`).
- `INFRA-320` — the exact `tools/calibrate_simq.py::_run_engine()` hard-fail guard
  (`dropped_count == 0 and mode == "NORMAL" and not survival_triggered`) this ticket's `Calibration
  IntegrityError` symptom comes from. No dedicated `test_path` line was found for INFRA-320 itself in
  the grepped excerpt — flagged as a gap for Plan to confirm (see Risks).
- None of these are `P0`; none currently require a passing `test_path` change as a hard gate, but
  `INFRA-223` and `INFRA-199`/`INFRA-198` should have their `v2_evidence` re-verified once a fix
  lands, per the Authoritative Mechanics Rule's "same session" parity requirement.

## Prior Work
- `tickets/done/TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH.md` — hotfix tier, no
  `stored_artifacts/` (staging artifacts are standard/epic-only per the Workflow Rule), so its full
  per-tick evidence lives only in the ticket body itself (read in full). It is the direct origin of
  this ticket: found the same `WatchdogTrip`/`phase_costs` evidence and the
  `CalibrationIntegrityError` repro at `--resource-budget large`, deferred 6 tests here rather than
  force-fitting a floor edit onto a timeout/backpressure failure. Also separately fixed an unrelated
  `lifecycle.py` TypeError bug (`TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`) that
  should not be confused with this investigation's scope.
- `tickets/done/TCK-20260824-TOWN-CENTER-POINTER-FIX.md` — the navigation fix whose slightly-longer
  runs (more distance traveled, more ticks with active entities → more replay/telemetry event
  volume) made this pre-existing perf characteristic newly visible as test timeouts. Read for
  context; out of scope, not touched.
- No `stored_artifacts/` entries matched this ticket's Related Code Areas via
  `docs/REGISTRY.yaml`/direct search under `src/simulation_quality/persistence.py`,
  `src/observability/`, `tools/calibrate_simq.py`, or `tests/conftest.py` beyond what's cited above
  — this appears to be the first dedicated performance investigation into this specific code path.

## Risks and Open Questions
- **Whether to change `CanonicalStateHasher.get_hash()`'s cadence in NORMAL/CONSTRAINED mode is a
  real product/architecture decision, not a default "fix it" — flagging, not assuming.** It is a
  `verified`, documented (`INFRA-223`, `known_limitations.md` §2.4, `kernel.md`) contract that
  exists specifically so replay/determinism verification has a fresh canonical hash every tick in
  the common (NORMAL/CONSTRAINED) case. Routing it through the existing (but currently-bypassed)
  `BudgetedCanonicalHasher` would measurably reduce persistence cost but would also measurably
  reduce per-tick replay/determinism verification coverage in the common case — a real trade-off
  requiring an explicit `docs/guidelines/intentional_divergences.md` entry if chosen, not a "route
  it through the existing rate limiter" free lunch. Plan must decide; Investigate does not.
- **The `_rotate_chunk()` redundant-serialization fix (Root cause #1) and the per-record `flush()`
  fix (Root cause #2) both look safe** (no documented contract describes the old, slow shape as
  required), but neither was implemented or test-verified here — Plan/Implement must confirm no
  hidden dependency on the current `_rotate_chunk` budget-check's exact synchronous timing (e.g. a
  test asserting the warning log fires before a specific point) before changing it.
- **INFRA-320 has no confirmed `test_path` in the grepped ledger excerpt** — worth a direct
  `grep -A20 "id: INFRA-320"` re-check at Plan time to confirm whether it's untested or the
  `test_path` field simply wasn't captured in this investigation's excerpt.
- **500 ticks did not reproduce `CalibrationIntegrityError`** in either profiling run here (guard
  passed both times) — the mechanism (drain-worker throughput ceiling under sustained per-record
  `flush()` cost) is demonstrated and quantified, but a full 1000-tick reproduction of the actual
  failure was not attempted in this investigation (time-boxed to representative 500-tick runs per
  the dispatch instructions' "several hundred to 1000" range, and 500 ticks already surfaced both
  root causes clearly). Plan/Implement should budget for at least one 1000-tick before/after
  comparison run to confirm the guard actually starts passing again after a fix.
- **cProfile's own overhead measurably distorts absolute timings** (elapsed(inner)=24.95s under
  profiler vs. 14.58s clean for the same 500-tick run — profiler overhead alone is on the order of
  the entire baseline). This investigation used the clean (unprofiled) run for absolute numbers and
  the profiled run only for relative/function-level attribution (`tottime`/`ncalls`), which is the
  correct way to combine the two, but Plan/Implement should do the same rather than quoting profiled
  absolute ms figures as real.

## Anti-Drift Hazards
- Do not conflate the `persistence` **tick-phase** (canonical hash + replay chunk rotation) with the
  `QualityPersistence`/`EventRecorder` **telemetry-write pipeline** — they are different code paths
  with different owners, different root causes, and different fixes. A fix that touches one will not
  by itself fix the other; the ticket's acceptance criteria (re-run the 6 named tests) requires both
  to actually be addressed, or a documented decision not to fix one of them.
- Do not change `CanonicalStateHasher`/`_phase_persistence`'s hash-cadence gating without updating
  `INFRA-223`, `known_limitations.md` §2.4, and `kernel.md` in the same session — the Authoritative
  Mechanics Rule requires docs/parity to move together with any such change, and this is a `verified`
  entry, not a stale one.
- Do not silently raise `BoundedObservabilityQueue.max_size`/`max_events` as a "fix" for the
  `CalibrationIntegrityError` — per Root cause #2's analysis, that masks the drain-worker throughput
  ceiling (more buffering before the same eventual overflow, plus more memory) rather than fixing it;
  the ticket's own Scope explicitly asks Investigate/Plan to distinguish "tune the threshold" from
  "fix write volume/frequency/batching/format," and this investigation's evidence points at the
  latter.
- `test_corpus_diversity.py` is a Soft Monitor (`docs/testing/regression_policy.md` §3,
  `tests/unit/worldassembly/`) — this investigation does not change that classification, and neither
  should Plan/Implement; don't accidentally promote it to a hard gate as a side effect of touching
  its 6 deferred tests.
- Do not fold the already-known, already-deferred mid-resolution wall-clock throttle finding into
  this ticket's fix (see next section) — they are architecturally related but mechanically distinct,
  and the user has already chosen to let the throttle finding sit.

## Kernel Wall-Clock Throttle Relationship
**Verdict: genuinely separate mechanisms, sharing the same broad architectural pattern
("wall-clock-measured budgets" rather than deterministic tick-count budgets) but operating at
different points in the tick with different concrete effects.** Evidence:

1. **The already-known, already-deferred finding** lives in `_phase_resolution()`
   (`src/engine/kernel.py`, mid-resolution throttle block, ~lines 594-610 in this checkout — matches
   the ticket's cited "585-596"; line numbers have drifted slightly from intervening edits). It
   compares `elapsed = (time.perf_counter_ns() - self._start_perf_ts) / 1e6` — where
   `self._start_perf_ts` is reset to `t0` at the very top of *this same tick's*
   `_tick_once_inner()` (`kernel.py:371-372`) — against `hard_cap = self._profile.max_tick_budget_ms`,
   **while resolution work items are still being applied** (checked every 10th result,
   `kernel.py:594-595`). If exceeded, it actively drops remaining result items
   (`self._status.record_dropped_work(...)`) and calls
   `self._governor.force_mode(RuntimeMode.DEGRADED, ...)` (`kernel.py:604`) — a real,
   state-mutating, mode-changing side effect that alters `GovernorPolicy` (concurrency, replay
   richness) for subsequent ticks. This is genuinely nondeterministic under variable real-world CPU
   load: the same tick can have a different amount of resolution work silently dropped depending on
   how fast the machine happened to be at that instant.
2. **This ticket's own finding** is the *separate* watchdog block at `kernel.py:420-465` (in this
   checkout), which runs **after** `_phase_persistence()` has already completed
   (`kernel.py:434-436`) and computes `self._final_compute_ms = sum(self._phase_costs.values())`
   — i.e. it *includes* whatever the persistence phase (canonical hash + chunk rotation) already
   cost, then compares that total against `min(hard_cap, limit_ms)`. This is literally the exact
   code path that produced the ticket's own quoted per-tick evidence: it constructs an
   `AlertEvent.create_watchdog_trip(..., details={"phase_costs": self._phase_costs.copy()})` and
   routes it through `AlertsManager` (`kernel.py:446-462`) — confirmed by reproducing the identical
   `phase_costs` dict shape in this investigation's own cProfile run log (tick 18:
   `persistence: 39.35292` inside a full `phase_costs` dict). Critically, **this block does not call
   `self._governor.force_mode(...)`** — it only logs a WARNING, routes a CRITICAL alert, and calls
   `self._record_runtime_signals()` (feeding `avg_ms` for the *next* tick's `limit_ms` threshold,
   not the resolution throttle's `hard_cap`). It does not itself drop resolution work or change
   `GovernorPolicy` state.
3. **Practical implication of the distinction**: the mid-resolution throttle (already deferred) is a
   genuine source of run-to-run *behavioral* nondeterminism (different entities' actions silently
   dropped depending on real-time load). This ticket's persistence-phase watchdog trip is, by
   itself, an *alerting/logging* side effect — it does not change what the simulation computes on
   its own. However, the **underlying cost this ticket found** (the `_rotate_chunk` redundant
   serialization spike, and the steady per-tick canonical-hash/flush overhead) does lengthen
   `_tick_once_inner()`'s total wall-clock duration, which — on a **subsequent** tick, once that
   slow tick's `tick_compute_ms` is folded into `self._status.signal_history` — raises `avg_ms` and
   therefore `limit_ms` for future ticks' watchdog comparisons (not the resolution throttle's
   `hard_cap`, which stays fixed at `self._profile.max_tick_budget_ms`). So the two mechanisms are
   architecturally adjacent (both live in `kernel.py`, both compare wall-clock elapsed time against
   a budget, both can fire in the same run) but are not the same code path, do not share a trigger
   condition, and do not have the same behavioral consequence. **Do not merge them into one fix.**
   Fixing this ticket's persistence-phase cost will likely *reduce how often* the mid-resolution
   throttle also fires (since less of each tick's real-time budget gets consumed by a slow prior
   tick's `avg_ms` inflation), but will not eliminate the throttle's own wall-clock-vs-tick-count
   design, which remains the separately-tracked, separately-deferred issue.

## Resource-Budget Question
Real options for `tests/conftest.py`'s default `--resource-budget medium` (60s SIGALRM cap), for
Plan to decide between — not a bare recommendation:

**Option A — leave `--resource-budget medium` as the global default, mark these specific tests to
always run under `large`.** `pytest.mark` (or a per-test `--resource-budget` override mechanism, if
one doesn't already exist in `conftest.py` it would need adding) applied to the 6 named 500-1000t
grade-stability tests. Pro: doesn't weaken the 60s budget's usefulness as a fast-iteration guard for
the rest of the suite (most tests genuinely should fail fast at 60s). Con: requires either a new
per-test marker mechanism in `conftest.py`, or accepting that these 6 tests can only be run
correctly with an explicit `--resource-budget large` CLI flag (easy to forget, silently produces a
spurious `TimeoutError` failure instead of the real signal otherwise).

**Option B — treat the 60s cap as simply mis-sized for this specific workload class (3-trial ×
500-1000-tick `_run_engine` calibration batches) independent of whatever perf fix lands, and raise
the default for the whole `tests/unit/worldassembly/` directory** (e.g. a `pytest.ini`/`conftest.py`
directory-scoped override, or a `conftest.py` in that subdirectory). Pro: simpler, no per-test
markers to maintain, matches this investigation's own measurement that even a *clean* 500-tick run
already costs ~15-30s wall-clock before any queue-overflow issue, and 1000-tick × 3-trial batches
(the actual test shape) are correspondingly ~3-6x that. Con: broadens the exemption beyond the 6
specific tests, potentially hiding a *different*, unrelated future test in the same directory that
genuinely regresses to a real 60s+ runtime.

**Option C — do nothing to the resource budget; treat it as correctly-sized and rely entirely on
fixing the underlying perf/backpressure root causes** so total run time drops back under 60s
without needing any test-invocation change. Pro: no test-infrastructure change at all, cleanest.
Con: contingent on the perf fix being enough — this investigation's Root cause #1 fix alone would
remove ~150-243ms × ~5 spikes ≈ 1-1.2s out of a 500-tick run's ~15-30s (a few percent), and Root
cause #2's fix would remove the steady per-record `flush()` overhead across ~4000-5000 records/500
ticks (harder to estimate precisely without implementing it) — plausible but not proven to be
enough on its own to close a 3-trial × 1000-tick batch back under 60s; the ticket's own evidence
(`--resource-budget large` needed even to *reach* the `CalibrationIntegrityError`, not just to avoid
the earlier `TimeoutError`) suggests these workloads are inherently well above 60s regardless of the
perf fix, making Option C alone risky as the sole answer.

**Assessment for Plan**: the ticket's own Scope already treats this as "a *separate*, narrower
question from the backpressure/perf root cause itself — both may need addressing, but they are not
the same fix," and this investigation's evidence supports that framing — Option A or B (some form of
test-invocation-level fix) is very likely needed *regardless* of which perf fix is chosen, because
the workload is 500-1000 real ticks × 3 trials of a real Kernel run, which is inherently a multi-tens-
of-seconds operation even in the best case measured here (14.58s wall for a single clean 500-tick
trial, no 3x multiplier, no queue-overflow-driving 1000-tick length yet applied). Recommend Plan
choose between A and B (not C alone) and pair it with whichever perf fix(es) it selects from Root
causes #1/#2.
