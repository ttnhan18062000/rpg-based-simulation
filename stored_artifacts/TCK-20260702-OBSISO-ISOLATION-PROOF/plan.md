---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260702-OBSISO-ISOLATION-PROOF
artifact_type: plan
tags: [performance, observability, simulation-quality, benchmark, queue-drops, regression-guard]
---

# Implementation Plan — TCK-20260702-OBSISO-ISOLATION-PROOF

## Summary

This plan closes gap G5 (the final gap in the observability-process-isolation epic) by (1) extending the
existing `BenchHarness` with a CPU-time sampler and using it to measure engine tick throughput/CPU under
three SimQ configs — `QUALITY_SCORING_DISABLED=1` (baseline, **not** `ObservabilityMode.OFF`), in-process,
and broker (real `QualityWorker` subprocess against a manually-provisioned Redis container) — committing the
results to a new `docs/performance/simq_isolation_overhead.md`, then locking a relative regression-guard
threshold from that measurement; and (2) adding a queue-drop / SURVIVAL-mode guard to `calibrate_simq.py`'s
`_run_engine()` (the real engine-running call site — not literal `make evaluate`, which is a dry-run diff
that cannot observe a live drop) that hard-fails calibration on overflow, persists drop/pressure state to a
new sidecar file so a later dry-run diff can retroactively detect an invalid run, and wires a warn-level
surface into `evaluate_simq.py`'s dry-run path per the ticket's own stated default. All ten open items
investigation.md flagged are decided below, not deferred. No in-engine routing logic (`INFRA-318`/`INFRA-319`)
is touched — this ticket only measures it.

## Key Decisions (resolving investigation.md's flagged open items)

1. **Mode (a) baseline** = `QUALITY_SCORING_DISABLED=1` with `EventRecorder` fully enabled (JSONL/stream/queue
   running; only the `quality_fn` callback skipped). This is explicitly **not** `ObservabilityMode.OFF`. Every
   benchmark artifact (test, results doc) must state this distinction in its own text so it cannot be silently
   conflated with `test_production_observatory_overhead.py`'s separate OFF-vs-LIGHT numbers.

2. **Queue-size test injection** = test-only post-construction mutation, `kernel.event_recorder.queue.max_size = N`,
   mirroring `test_obs_backpressure.py::_set_queue_fill`'s existing precedent. **Rationale**: this ticket is a
   measurement + tooling-guard ticket per its own Type/Scope — adding a new Kernel constructor flag/env override
   for `max_events` is a production-code surface expansion (needs its own docs, ops runbook entry, and test
   coverage) that is not required to prove AC #3. The test-only mutation achieves the same forced-overflow
   condition with zero production-code footprint and a direct existing precedent in the same subsystem.

3. **AC #3 target** = `calibrate_simq.py`'s `_run_engine()` (calibrate_simq.py:246-252 call site, immediately
   after the tick loop and **strictly before** the existing `try: kernel.shutdown() except Exception: pass`
   block at calibrate_simq.py:251-254) hard-fails on `dropped_count > 0` or
   `observability_status()["mode"] != "NORMAL"`. **This ordering is load-bearing, not a style choice — caught
   on architecture review**: `calibrate_simq.py` already has a bare `except Exception: pass` around
   `kernel.shutdown()`. If the new guard's raise is placed inside that block (a plausible misreading of
   "before/around shutdown"), the P0 hard-fail exception is silently swallowed and the guard does nothing.
   The raise MUST occur in its own statement, strictly before that try block begins — never inside it, never
   merged into its body. This function is invoked both by direct `calibrate_simq.py`
   runs and by `evaluate_simq.py`'s `evaluate-full` target (via `_run_calibration()` → `calibrate_simq.main()`),
   so fixing it here covers both real engine-running paths. Literal `make evaluate` (dry-run) is a diff-only
   target that never runs the engine and cannot observe a live drop — this is ticket-text drift, not something
   to force a fix into. To still give the dry-run path *some* retroactive visibility (closest honest reading of
   the AC's literal wording), the guard also persists drop/pressure state to a new **typed** sidecar record
   (see Key Decision #3a below), written next to `quality_report.json` on every calibration run (not just
   overflow ones). `evaluate_simq.py
   --dry-run` (`make evaluate`) is extended to read this sidecar if present and **warn** (not hard-fail — ad-hoc
   evaluation, per the ticket's own stated default) if it shows a non-NORMAL run. Hard-fail stays exclusively in
   `calibrate_simq.py`/`evaluate-full`, per the ticket's own default ("hard-fail for calibration, warn for
   ad-hoc evaluation").
   `QualityReport`'s own schema (`src/simulation_quality/quality_report.py`) is **not** modified — the sidecar
   keeps this additive and avoids touching a schema consumed elsewhere.

3a. **Sidecar file shape, corrected on architecture review**: the original draft of this plan proposed a bare
   dict literal for the sidecar (`{"dropped_count": int, ...}`), which was correctly flagged as a Durable State
   Rule violation ("If something survives beyond the current tick or current function call, it must have a
   typed model, a stable location, a defined lifecycle, inspection/debug visibility, and tests" — this sidecar
   is read back by a *separate later process invocation*, so it unambiguously survives beyond the current
   function call). Not touching `QualityReport`'s *existing* schema (legitimate, Key Decision #3) does not mean
   *no typed model at all* — a small sibling dataclass achieves the same additivity without the violation.
   **Corrected design**: define `RunHealthRecord` (new, small `@dataclass` in a new module
   `src/simulation_quality/run_health.py` or alongside `QualityReport` in `quality_report.py` — Step 10 decides
   the exact file at Implement time based on which keeps the diff smallest) with fields `dropped_count: int`,
   `pressure_mode_final: str`, `survival_triggered: bool`, `guard_passed: bool`, plus a `to_dict()` method
   mirroring `QualityReport.to_dict()`'s own shape (`quality_report.py:36`); `QualityReport` has no
   `from_dict()` to mirror, so `RunHealthRecord.from_dict()` is new territory specific to this record (needed
   since, unlike `QualityReport`, this sidecar is read back by a separate later process). Write it via the identical
   tmp-write-then-`os.rename()` crash-safe pattern `QualityPersistence.write_report()` already uses
   (`persistence.py:46-54`) — either by adding a `write_run_health(record: RunHealthRecord)` method to
   `QualityPersistence` itself (preferred — keeps the write path centralized where `quality_report.json` is
   already written, same `self._run_dir`) or a small standalone function if adding to that class would blur its
   existing single responsibility (Implement-time judgment call, not pre-decided here). Add round-trip
   serialize/deserialize tests per the Testing Rule's "Architecture tests: typed records serialize/deserialize
   correctly" — see Step 11.

4. **Hardware class** = `certification_contract.md`'s binary AND-rule (explicitly "Proof-Stable"). This
   session's/implement machine's class is computed at measurement time (4 cores / 5.8GB RAM at investigation
   time → `CLASS_C` under the binary rule) and recorded as such in the results doc, with a one-line note
   flagging that `perf_baseline_policy.md`'s CLASS_B/C table would call the same hardware `CLASS_B` by its
   core-count-only reading — noting the conflict, not resolving it (pre-existing, out of this ticket's scope).

5. **Benchmark harness** = extend `src/perf/bench_harness.py::BenchHarness` with a `psutil.Process.cpu_times()`
   sampler (start/end deltas) rather than writing a bespoke script. Rationale: it already implements the exact
   warmup(100)+sample(1000) methodology `perf_baseline_policy.md` §2.1 requires, plus TPS/percentile/RSS
   measurement — adding one additive sampler is strictly smaller-surface than a parallel bespoke benchmark
   runner, and keeps one canonical perf-measurement code path for future tickets.

6. **New benchmark test file** = `tests/perf/test_simq_isolation_overhead.py` (new file), not an addition to
   `tests/simulation_quality/test_performance.py`. Rationale: that file's 6 existing tests are pure
   scorer/accumulator microbenchmarks with zero `Kernel` instantiation — adding engine-driving tests there
   would blur its established purpose. `tests/perf/` already holds the structurally closest precedent
   (`test_production_observatory_overhead.py`, build-kernel-per-mode + percentile comparison), so the new file
   sits next to its nearest analog. This also matches test_plan.md's own Scoped Pytest Commands section, which
   already assumes this path.

7. **Redis provisioning** = manual `docker run -d --name simq-isolation-proof-redis -p 6379:6379 redis:7-alpine`
   before the broker leg, torn down (`docker rm -f simq-isolation-proof-redis`) after. The benchmark test and
   the `QualityWorker` subprocess launch gate on a `REDIS_AVAILABLE` check (probe a real connection, same
   pattern `test_broker_feed_integration.py` already uses) — if unavailable, the broker leg and
   `test_broker_mode_engine_cpu_within_disabled_band` **skip** with a clear reason, never fail, and the results
   doc records which legs were actually measured.

8. **`quality_scoring_contract.md` line 1410 reconciliation** = once step 4's numbers exist, update the line's
   evidence citation from "confirmed by direct code read" to point at
   `docs/performance/simq_isolation_overhead.md` with the actual measured figure — either keeping "< 1%" if
   measurement confirms it, or revising the number, but never leaving the code-read-only claim standing
   unreconciled next to a contradicting measurement.

9. **Parity ledger** = new entry `INFRA-320` in `docs/parity_ledger/infrastructure.yaml`, `priority: P0` (per
   the ticket's own AC wording), `status: verified` once its `test_path` passes
   (`tests/simulation_quality/test_calibrate_simq.py::test_calibrate_simq_fails_on_forced_queue_overflow`).

10. **`docs/plans/observability_process_isolation.md`** — G5's currently-open section (lines 117-119) moves to
    a RESOLVED block in the same format G1-G4 already use, as the final step once benchmark + guard both land.

No `docs/guidelines/intentional_divergences.md` entry is needed — this ticket is measurement + tooling-guard
work, not a mechanics behavior change from a documented expectation.

**Benchmark tick-count methodology**: the ticket's Scope text suggests reusing "a 200-tick sandbox_world run"
(the real, committed `sandbox_world_seed42_200t` calibration anchor). That 200-tick figure is a
*grade-calibration* anchor length (used by `calibrate_simq.py`'s own tuning), not this benchmark's sampling
requirement. `perf_baseline_policy.md` §2.1 requires **minimum 100 warmup + minimum 1000 sampled ticks** for
any baseline claim. Resolution: the benchmark drives the **same seed/world** (`sandbox_world`, seed 42) through
`BenchHarness.run_benchmark()` using its own warmup=100/sample=1000 (1100 total engine ticks per mode), not
capped at the 200-tick anchor length — the anchor value governs calibration/grading elsewhere and is a
different concept from this ticket's throughput/CPU sampling minimum. This resolves the ticket text's apparent
tension explicitly rather than silently picking one number.

## Steps

### Step 1 — Add a CPU-time sampler to BenchHarness
**Files:** `src/perf/bench_harness.py`
**Change:** Add a `psutil.Process(os.getpid()).cpu_times()` sample taken immediately before warmup starts and
immediately after the sampled-tick window ends inside `run_benchmark()`. Compute `cpu_time_user_delta_s` and
`cpu_time_system_delta_s` (or a combined `cpu_time_total_delta_s`) and add them to the result dict returned by
`run_benchmark()`, alongside the existing TPS/percentile/RSS fields. Keep the existing `flags={"no_replay":
True, "no_frame_pacing": True}` defaults and warmup(100)/sample(1000) behavior unchanged — purely additive.
**Do NOT touch:** existing TPS/percentile/RSS computation logic, the `flags` defaults, or any caller of
`run_benchmark()` outside this ticket's new test files.
**Verify:** `test_bench_harness_cpu_time_sampling` (new, `tests/perf/test_bench_harness.py`) — asserts the new
field(s) appear in the result dict and are monotonically non-decreasing across the sample window.

### Step 2 — Redis provisioning + REDIS_AVAILABLE gating helper for the broker leg
**Files:** `tests/perf/test_simq_isolation_overhead.py` (new file, created in this step as scaffolding; full
benchmark body added in Step 3)
**Change:** Add a module-level `REDIS_AVAILABLE` probe (attempt a real `redis.Redis(...).ping()`, same
detection pattern as `tests/simulation_quality/test_broker_feed_integration.py`), plus a documented manual
provisioning note in the test file's docstring: `docker run -d --name simq-isolation-proof-redis -p 6379:6379
redis:7-alpine`, torn down with `docker rm -f simq-isolation-proof-redis` after the benchmark session. Any
broker-leg test/fixture must be decorated to skip (not fail) when `REDIS_AVAILABLE` is false, with a clear skip
reason string.
**Do NOT touch:** `tests/simulation_quality/test_broker_feed_integration.py`'s own gating logic — reuse the
pattern, do not modify that file.
**Verify:** manual check — running the new file with no Redis running shows skips, not failures, for the
broker-only tests; running it with the container up executes the broker leg.

### Step 3 — Three-mode engine overhead benchmark test
**Files:** `tests/perf/test_simq_isolation_overhead.py`
**Change:** Add `test_three_mode_engine_overhead_benchmark` (`@pytest.mark.slow`). For each of the three
configs — (a) `QUALITY_SCORING_DISABLED=1` env, (b) `QUALITY_FEED_MODE=inprocess` (default), (c)
`QUALITY_FEED_MODE=broker` with a real `QualityWorker` subprocess (`python -m src.simulation_quality.worker`)
launched against the Redis container from Step 2 — build a `Kernel` on the `sandbox_world` seed-42 scenario and
call `BenchHarness.run_benchmark()` (warmup=100, sample=1000, `flags={"no_replay": True, "no_frame_pacing":
True}}`, per Key Decision above).
**Worker-readiness gating (added on architecture review — this is genuinely new subprocess-launching territory
in this repo; grepped every existing broker-mode test and confirmed zero prior `subprocess`/`Popen` usage
anywhere in `tests/simulation_quality/`, so no precedent exists to just follow)**: `QualityWorker.run()` starts
its `/health` HTTP server thread and returns `200 ok` *before* calling `self._feed.start(self._hub)`
(`worker.py:95-111`), so polling `/health` for a bare 200 alone does not prove the Redis consumer group is
actually subscribed and ready — a real readiness race, not just a hypothetical one. **A naive fix using
`/health`'s `current_tick` field does not work either** — `QualityHub._tick` is initialized to `0` at
construction (`quality_hub.py:101`), not absent, so it would report `current_tick: 0` immediately and
trivially, before the consumer thread has done anything; it is not a readiness signal. The correct, already-
proven signal (matching the exact pattern `TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX`'s own
`test_quality_worker_health_payload_includes_per_pillar_event_counts` test used) is `/health`'s
`pillar_event_counts` field, which only becomes non-zero once `hub.on_envelope()` has actually run — proving
the full round-trip (publish → Redis → consumer thread → `hub.on_envelope` → accumulator) is live. Before
starting the real `BenchHarness.run_benchmark()` warmup/sample window for the broker leg: publish one throwaway
probe event via the same producer path the benchmark itself uses, then poll `/health` until any
`pillar_event_counts` value is non-zero, with a bounded timeout (e.g. 10s) that fails the test loudly (not
silently proceeds) if the worker never becomes ready — never gate readiness on a fixed `time.sleep()`.
Hold `OBS_DECISION_TRACE` (or whatever env controls
`ObservabilityConfig.is_decision_trace_enabled()`) constant and explicit across all three runs, and record its
value in the test's captured result metadata — this guards against the `DecisionTraceWriter`'s independent
`QueueDrainWorker` becoming an uncontrolled confound (per investigation.md's Anti-Drift Hazards). Assert in the
test body (not just print) that mode (a)'s `kernel.event_recorder.enabled is True` and that JSONL/stream writes
still occur, to encode Key Decision #1 as a running check, not just a doc comment. Capture per-mode
wall-clock TPS and `cpu_time_total_delta_s` into a structured result (e.g. a dataclass or dict) that Step 5 (the
results doc) and Step 6 (the regression guards) both consume. The broker leg is skipped per Step 2's gating if
Redis is unavailable.
**Do NOT touch:** `src/engine/kernel.py`'s feed-selection/routing logic (`INFRA-318`/`INFRA-319`) — this step
only measures the three existing, already-verified routing paths.
**Verify:** `test_three_mode_engine_overhead_benchmark` passes in the slow lane; fast lanes (`-m "not slow"`)
unaffected since the test is slow-marked.

### Step 4 — Execute the benchmark and record raw numbers (indicative pass)
**Files:** none (execution step, produces data consumed by Steps 5-6)
**Change:** Run the Step 3 test (or an equivalent one-off invocation of the same code path) once to get initial
numbers. Per investigation.md's swap-pressure risk (920Ki free of 4.0Gi swap at investigation time), treat this
first run's numbers as **indicative only** — do not lock the Step 6 regression threshold from this run alone.
**Quantitative convergence rule (added on architecture review — the original draft left "quieter"/"diverge
significantly" undefined, an operational gap in an otherwise rigorous plan)**: before re-running, check
`free -h`'s swap-free value — re-run only once it exceeds its value at the first run (a directionally-quieter
state, not a specific absolute target, since this sandbox's baseline swap pressure is already known to be
high). Compare the two runs' `cpu_time_total_delta_s` for the in-process mode (the leg every config shares):
if the second run's value is within 10% of the first, treat the second run's numbers as final and commit them
(Step 5/6). If they diverge by more than 10%, run a third time and use the median of the three; document the
observed noise band explicitly in the results doc rather than silently discarding data. The 10% figure is
chosen to sit comfortably above `perf_baseline_policy.md` §3's existing p99 band-tolerance (+15%) — if the
raw measurement noise between two runs of the same code exceeds the tolerance the regression guard itself
uses, the guard would be measuring noise, not real regressions, so 10% is the threshold below which the
methodology is trustworthy enough to lock a number.
Record both runs' raw output in scratch form for comparison; only the final numbers (post-convergence) get
committed.
**Do NOT touch:** no code changes in this step.
**Verify:** two (or three, if the 10% rule triggers a third run) consistent (within the stated 10% band)
measurement runs exist before Step 5/6 proceed, per the 10% convergence rule above.

### Step 5 — Commit the results doc
**Files:** `docs/performance/simq_isolation_overhead.md` (new file)
**Change:** Write the committed overhead-budget table: per-mode (a/b/c) ticks/sec and engine CPU time, bound to
`(Profile, Scenario, Hardware Class)` per `certification_contract.md` §5's Reporting Law. Hardware class =
`CLASS_C` per Key Decision #4 (binary AND-rule from `certification_contract.md`), with a one-line note flagging
the conflict with `perf_baseline_policy.md`'s core-count-only table. State explicitly which `OBS_DECISION_TRACE`
value was held constant across all three runs (Step 3). State explicitly that mode (a) is
`QUALITY_SCORING_DISABLED=1`, not `ObservabilityMode.OFF`, and is not directly comparable to
`test_production_observatory_overhead.py`'s numbers. Note if the broker leg was skipped (no Redis) or measured.
Record the swap-pressure caveat from Step 4 and which of the two runs the committed numbers come from.
**Do NOT touch:** existing docs under `docs/performance/` other than adding this new file and the
`perf_baseline_policy.md` cross-reference in Step 14.
**Verify:** doc exists, reviewed for the required `(Profile, Scenario, Hardware Class)` triple on every number,
matches Step 4's final measurement run.

### Step 6 — Regression-guard tests (relative, band-tolerance)
**Files:** `tests/perf/test_simq_isolation_overhead.py`
**Change:** Add `test_inprocess_simq_overhead_within_regression_band` and
`test_broker_mode_engine_cpu_within_disabled_band` (`@pytest.mark.slow`). Both use a **relative** assertion
(percentage over the mode-(a) baseline's `cpu_time_total_delta_s`), threshold locked from Step 4/5's final
measurement, matching `perf_baseline_policy.md` §3's band-tolerance convention (p50 ≤ +5.0%, p95 ≤ +10.0%,
p99 ≤ +15.0% is the existing convention for tick-timing percentiles; this ticket's CPU-overhead band is a new,
separate threshold derived from its own measurement — state the exact percentage chosen and cite Step 5's doc
as the source). The broker-mode test skips per Step 2's `REDIS_AVAILABLE` gating.
**Do NOT touch:** any existing regression-guard threshold in `tests/perf/test_production_observatory_overhead.py`.
**Verify:** both tests pass in the slow lane against the locked threshold from Step 5's doc.

### Step 7 — Test-only queue-size injection helper
**Files:** `tests/simulation_quality/test_calibrate_simq.py` (new file, created here)
**Change:** Add a `_force_small_queue(kernel, max_size)` helper that mutates
`kernel.event_recorder.queue.max_size = max_size` post-construction, before the tick loop starts — mirroring
`tests/unit/observability/test_obs_backpressure.py::_set_queue_fill`'s existing precedent on the same class. No
production code is touched (Key Decision #2).
**Do NOT touch:** `src/engine/kernel.py`'s `EventRecorder(..., max_events=5000, ...)` construction call — no
constructor flag or env override is added.
**Verify:** helper is exercised by Step 8's test; confirm the mutated `max_size` actually takes effect (queue
overflow is reachable with a small enough value on a realistic scenario).

### Step 8 — Queue-drop hard-fail guard in `calibrate_simq.py`
**Files:** `tools/calibrate_simq.py`
**Change:** In `_run_engine()`, immediately after the tick loop (line ~246-248, before `kernel.shutdown()` at
line ~252), read `kernel.event_recorder.observability_status()` and `kernel.event_recorder.queue.dropped_count`
while the recorder is still alive. First, as a one-line verification during this step, confirm
`EventRecorder.shutdown()`'s body does not clear/reset `queue.dropped_count` before this read (investigation.md
flagged this as unread/unverified) — if it does, move the read to strictly before `kernel.shutdown()` is
called. If `dropped_count > 0`, raise a clear exception (e.g. `CalibrationIntegrityError`) that propagates to a
non-zero exit from `main()` — this is the hard-fail path for calibration runs (Key Decision #3). If
`dropped_count == 0` and mode stayed `NORMAL` throughout, proceed exactly as before — the existing zero-drop
success/exit-0 contract must be provably unchanged (test in Step 11).
**Do NOT touch:** the tick loop itself, `kernel.shutdown()`'s call site or ordering relative to other
post-loop work, or any other `_run_engine()` behavior unrelated to the drop/pressure read.
**Verify:** `test_calibrate_simq_fails_on_forced_queue_overflow` (Step 11) and the anti-drift
`test_calibrate_simq_succeeds_normally_with_zero_drops` (Step 11).

### Step 9 — SURVIVAL-mode detection in the same guard
**Files:** `tools/calibrate_simq.py`
**Change:** Extend the Step 8 guard so it checks both loss mechanisms independently, per investigation.md's
Mechanics/Engine Constraints note that SURVIVAL (mode-shed, zero queue push) and queue-drop (overflow-evict)
are distinct. **Resolved on architecture review (was hedged in the original draft — confirmed as fact, not
left uncertain for Implement)**: `EventRecorder._survival_event_counts` (`event_recorder.py:84`) is a
genuinely cumulative `Dict[str, int]`, incremented at `event_recorder.py:172`, exposed via
`observability_status()["survival_counts"]` (`event_recorder.py:271`), and cleared only by the test-only
`reset_mode()` (`event_recorder.py:274-279`, never called during a normal run or by `shutdown()`). A single
post-tick-loop read of `observability_status()["survival_counts"]` — checking whether any value in that dict
is non-zero — correctly captures "SURVIVAL was entered at any point during the run," with no need for a
per-tick sampling flag. Raise the same `CalibrationIntegrityError` (same placement constraint as Step 8: strictly
before the `try: kernel.shutdown() except Exception: pass` block) if any `survival_counts` value is non-zero,
even if `dropped_count` itself is 0 (SURVIVAL means SimQ received nothing, a different silent-degradation path
than overflow).
**Do NOT touch:** `src/observability/event_recorder.py`'s SURVIVAL-mode transition logic itself (`INFRA-199`,
already correct) — this step only reads the existing accessor, never changes backpressure behavior.
**Verify:** `test_survival_mode_flags_run_instead_of_silently_grading` (Step 12).

### Step 10 — Persist drop/pressure state (typed record) + wire `evaluate_simq.py`'s dry-run warn path
**Files:** `tools/calibrate_simq.py`, `tools/evaluate_simq.py`, and either `src/simulation_quality/quality_report.py`
or a new `src/simulation_quality/run_health.py` (per Key Decision #3a — exact file chosen at Implement time)
**Change:** Define `RunHealthRecord` (`@dataclass`, fields `dropped_count: int`, `pressure_mode_final: str`,
`survival_triggered: bool`, `guard_passed: bool`, plus `to_dict()`/`from_dict()` mirroring `QualityReport`'s
own shape at `quality_report.py:36`). In `calibrate_simq.py`, after computing the Step 8/9 guard's pass/fail
state, write this record via the same tmp-write-then-`os.rename()` crash-safe pattern
`QualityPersistence.write_report()` already uses (`persistence.py:46-54`) — either a new
`QualityPersistence.write_run_health(record)` method (preferred, keeps the write path centralized) or a small
standalone function, Implement-time judgment call — to `quality_report.run_health.json`, next to
`quality_report.json` in the same `self._run_dir`, on every run (success or failure). In `evaluate_simq.py`,
the `--dry-run` path (literal `make evaluate`) is extended to check for this sidecar (via `RunHealthRecord.from_dict()`)
next to whatever calibration data it diffs against, and **warn** (print a clear warning, non-fatal) if
`guard_passed` is false or the sidecar is stale/missing for a run it's diffing — this is the closest honest
fulfillment of AC #3's literal "`make evaluate` ... fails/flags" wording without pretending the dry-run target
can itself observe a live drop. The non-dry-run `evaluate-full` path inherits Step 8/9's hard-fail automatically
since it calls `calibrate_simq.main()` directly.
**Do NOT touch:** `src/simulation_quality/quality_report.py`'s existing `QualityReport` schema/fields — no new
field is added to that class (Key Decision #3); `RunHealthRecord` is a separate, additive sibling type.
**Verify:** `test_evaluate_simq_flags_queue_overflow_run` (Step 11) plus a new round-trip serialize/deserialize
test for `RunHealthRecord` (`RunHealthRecord.from_dict(record.to_dict()) == record` or field-by-field
equivalent), per the Testing Rule's architecture-test requirement for typed records.

### Step 11 — Calibration/evaluation guard tests
**Files:** `tests/simulation_quality/test_calibrate_simq.py` (extends Step 7's new file),
`tests/simulation_quality/test_evaluate_harness.py` (extends existing file)
**Change:** Add:
- `test_calibrate_simq_fails_on_forced_queue_overflow` — uses Step 7's helper to force a small queue, drives a
  scenario guaranteed to overflow it, asserts `calibrate_simq.py`'s `main()` raises / exits non-zero rather than
  writing a clean `quality_report.json`.
- `test_calibrate_simq_succeeds_normally_with_zero_drops` (anti-drift guard, test_plan.md) — runs a normal small
  scenario with the default queue size, asserts exit/return behavior is byte-for-byte unaffected by the Step
  8/9 guard when `dropped_count == 0` and mode stays `NORMAL`.
- `test_evaluate_simq_flags_queue_overflow_run` — asserts `evaluate-full` (non-dry-run) hard-fails on a forced
  overflow run (inherits Step 8/9), and that `--dry-run` prints the Step 10 warning when the sidecar shows a
  failed guard.
**Do NOT touch:** `tests/simulation_quality/test_evaluate_harness.py`'s existing tests for the normal-path
`_run_calibration()`/`main()` flow.
**Verify:** all three tests pass; existing `test_evaluate_harness.py` tests unaffected.

### Step 12 — SURVIVAL-mode flagging test
**Files:** `tests/simulation_quality/test_calibrate_simq.py`
**Change:** Add `test_survival_mode_flags_run_instead_of_silently_grading` — drives `EventRecorder.record()`
calls (or ticks) until `queue_fill_ratio >= 1.00` is forced (per
`docs/architecture/observability_hot_path_safety_contract.md` §5's documented SURVIVAL entry condition),
asserts `queue.dropped_count` growth stops while SURVIVAL's own counters grow instead, and asserts the Step 9
guard flags the run (raises) even though `dropped_count` may be 0 in this scenario — this is the test that
proves SURVIVAL and queue-drop are checked as two independent conditions, not conflated into one.
**Do NOT touch:** `test_obs_backpressure.py` — reuse its `_set_queue_fill`-style technique conceptually, do not
modify that file.
**Verify:** test passes; confirms both loss mechanisms are independently detected.

### Step 13 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Add `INFRA-320` entry: `text` describing the queue-drop + SURVIVAL-mode calibration guard,
`status: verified`, `priority: P0`, `v2_evidence` citing `tools/calibrate_simq.py`'s `_run_engine()` guard
(Steps 8-9) and the sidecar mechanism (Step 10), `test_path:
tests/simulation_quality/test_calibrate_simq.py::test_calibrate_simq_fails_on_forced_queue_overflow`.
**Do NOT touch:** `INFRA-318`/`INFRA-319`'s existing entries — no edits to their text, status, or
`support_boundary` fields; this ticket's entry is purely additive.
**Verify:** the cited `test_path` passes (confirmed by Step 11); `python3 tools/knowledge_search.py` or the
parity ledger schema validator (if one runs in CI) accepts the new entry.

### Step 14 — Update `perf_baseline_policy.md`
**Files:** `docs/performance/perf_baseline_policy.md`
**Change:** Add a reference to the new benchmark (`docs/performance/simq_isolation_overhead.md`, Step 5) in
whatever section already indexes named benchmarks/results docs. Add a one-line flag noting the CLASS_B/C table
in this doc conflicts with `certification_contract.md`'s binary AND-rule (Key Decision #4) — pointer only, not
a fix (pre-existing, out of scope).
**Do NOT touch:** the CLASS_A/B/C threshold definitions themselves — do not resolve the conflict in this
ticket, only flag it.
**Verify:** manual read — doc now points to the new results doc and carries the one-line conflict flag.

### Step 15 — Reconcile `quality_scoring_contract.md` line 1410
**Files:** `docs/simulation_quality/quality_scoring_contract.md`
**Change:** Update the checklist line (currently: "Simulation tick timing is not measurably affected by quality
scoring (< 1% overhead) — ... confirmed by direct code read 2026-07-11") to cite the new measured evidence from
Step 5's doc instead of "direct code read" — keep the "< 1%" figure only if Step 4/5's measurement confirms it
for in-process mode; otherwise revise the stated percentage to match the measured number. Also update line
1131's pointer to `tests/simulation_quality/test_performance.py` if the new tests actually live in
`tests/perf/test_simq_isolation_overhead.py` (Key Decision #6) — correct the file reference so it's accurate.
**Do NOT touch:** any other claim in this doc unrelated to the SimQ-overhead line.
**Verify:** manual read — line 1410 and line 1131 both cite real, current, correct evidence.

### Step 16 — Resolve G5 in `observability_process_isolation.md`
**Files:** `docs/plans/observability_process_isolation.md`
**Change:** Move G5's section (currently open, lines 117-119) into a RESOLVED block matching the exact format
G1-G4 already use (landed by prior sibling tickets this session) — cite this ticket's ID, the new results doc,
and `INFRA-320`.
**Do NOT touch:** G1-G4's existing RESOLVED blocks — this step only adds G5's, in the same format, without
editing the prior four.
**Verify:** manual read — all five gaps (G1-G5) now show RESOLVED in a consistent format; this is the epic's
closing action.

### Step 17 — Anti-drift regression verification pass
**Files:** none (verification-only step; no new code)
**Change:** Re-run the full regression surface listed in test_plan.md before considering the ticket done:
- `pytest tests/simulation_quality/ tests/unit/observability/ tests/integration/observability/ -m "not slow" -q`
- `pytest tests/perf/test_simq_isolation_overhead.py tests/perf/test_bench_harness.py -m slow -q`
- `pytest tests/simulation_quality/test_calibrate_simq.py tests/simulation_quality/test_evaluate_harness.py -q`
- If Redis was provisioned: `REDIS_AVAILABLE=1 pytest tests/simulation_quality/test_broker_feed_integration.py tests/simulation_quality/test_kernel_simq_integration.py -m slow -q`
Specifically confirm `test_kernel_simq_integration.py`'s four `INFRA-318`-cited tests and `test_worker.py`'s two
`INFRA-319`-cited tests are unchanged/still passing — this is the explicit proof that this ticket only measured
those paths and never altered their routing logic.
**Do NOT touch:** do not modify any test to make it pass — a failure here means a prior step introduced a
regression that must be fixed at its source step, not patched over here.
**Verify:** all listed commands exit 0; no fast-lane test became slow or vice versa; no `INFRA-318`/`INFRA-319`
test changed behavior.

## Scope Guards

Must NOT be touched by this ticket's implementation:
- `src/engine/kernel.py`'s SimQ feed-selection/routing logic (`INFRA-318`/`INFRA-319`) — measure only, never alter.
- `src/observability/event_recorder.py`'s SURVIVAL-mode transition logic (`INFRA-199`) — read existing accessors only.
- `src/simulation_quality/quality_report.py`'s schema — no new fields; use the Step 10 sidecar instead.
- Any Kernel constructor signature or `EventRecorder(..., max_events=5000, ...)` call site — no new production flag/env override for queue size (Key Decision #2).
- `perf_baseline_policy.md`'s / `certification_contract.md`'s CLASS_A/B/C threshold definitions — flag the conflict, do not resolve it.
- `tests/perf/test_production_observatory_overhead.py`'s existing thresholds/tests — this ticket's numbers are not directly comparable (mode (a) ≠ OFF mode) and must not be merged or compared against that file's assertions.
- G1-G4's existing RESOLVED blocks in `docs/plans/observability_process_isolation.md` — only add G5's block.
- `INFRA-318`/`INFRA-319` parity ledger entries — additive only, no edits to their existing text/status.
- Any optimization of SimQ, the queue, or broker-mode code paths — this ticket is measurement + guard only (ticket's own Out of Scope).
- CI hardware provisioning configuration — out of scope per ticket.
- Multi-run statistical benchmarking methodology beyond `perf_baseline_policy.md`'s existing single-baseline + band-tolerance method — out of scope per ticket.
- `docs/guidelines/intentional_divergences.md` — no entry added (Key Decision, this is not a mechanics behavior change).

## Dependency Map

- Step 1 (BenchHarness CPU sampler) → required before Step 3 (benchmark test uses the new sampler fields).
- Step 2 (Redis provisioning/gating scaffold) → required before Step 3's broker leg; independent of Step 1.
- Step 3 (three-mode benchmark test) depends on Steps 1 and 2.
- Step 4 (execute, get numbers) depends on Step 3.
- Step 5 (results doc) depends on Step 4's final measurement run.
- Step 6 (regression-guard tests) depends on Step 5 (threshold value) and Step 3 (harness/test scaffolding).
- Step 7 (queue-injection helper) is independent of Steps 1-6.
- Step 8 (drop hard-fail guard) depends on Step 7 (test will need it) but the production code itself can be written independently; sequenced after 7 for verification convenience.
- Step 9 (SURVIVAL detection) depends on Step 8 (same guard function, extended).
- Step 10 (sidecar + evaluate_simq warn path) depends on Steps 8-9.
- Step 11 (calibration/evaluation tests) depends on Steps 7-10.
- Step 12 (SURVIVAL test) depends on Step 9.
- Step 13 (parity ledger entry) depends on Step 11's test passing.
- Step 14 (perf_baseline_policy.md update) depends on Step 5.
- Step 15 (quality_scoring_contract.md reconciliation) depends on Step 5.
- Step 16 (G5 resolution) depends on Steps 5, 13 (needs both the benchmark doc and the parity entry to cite).
- Step 17 (full regression verification) depends on all prior steps.

Steps 1-6 (benchmark track) and Steps 7-13 (guard track) are otherwise independent of each other and may be
implemented in either order or interleaved; Steps 14-17 are closing steps that depend on both tracks.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Benchmark runs produce a committed results table (docs) with ticks/sec and engine CPU for all three modes on at least one hardware class. | Steps 1, 2, 3, 4, 5 | `test_three_mode_engine_overhead_benchmark` |
| Broker mode shows engine-process CPU within the agreed band of the disabled baseline (target from observability_process_isolation.md R1; exact band set from first measurement). | Steps 4, 5, 6 | `test_broker_mode_engine_cpu_within_disabled_band` |
| `make evaluate` on a run with forced queue overflow (test-injected small queue size) fails/flags instead of producing grades. | Steps 7, 8, 9, 10 | `test_calibrate_simq_fails_on_forced_queue_overflow`, `test_evaluate_simq_flags_queue_overflow_run`, `test_survival_mode_flags_run_instead_of_silently_grading` |
| New tests pass in the `slow` lane; fast lanes unaffected. | All steps (test placement/marking) | Step 17's full scoped pytest commands |
| Perf baseline policy doc references the new benchmark; parity ledger `infrastructure.yaml` entry added for the drop guard. | Steps 13, 14 | manual doc read + `INFRA-320`'s cited `test_path` passing |

(Scope bullet "Verify SURVIVAL-mode interaction... assert the run is flagged rather than silently graded" —
not a separately numbered AC but explicit Scope text — is covered by Steps 9, 12 and
`test_survival_mode_flags_run_instead_of_silently_grading`, mapped above under the queue-overflow AC row since
both are facets of the same drop/pressure guard.)

## Anti-Drift Notes

- Mode (a) is `QUALITY_SCORING_DISABLED=1`, never `ObservabilityMode.OFF` — Step 3 encodes this as a running
  assertion (`kernel.event_recorder.enabled is True`, JSONL/stream still writing), not just doc prose, so a
  future refactor that collapses the two concepts breaks a test rather than silently invalidating this ticket's
  baseline.
- The `DecisionTraceWriter`'s independent `QueueDrainWorker` is orthogonal to `QUALITY_FEED_MODE` — Step 3 holds
  its controlling env/profile constant across all three runs and records the value used, so it cannot become an
  unstated confound in the committed numbers.
- `EventRecorder.shutdown()`'s effect on `queue.dropped_count` readability was flagged unread in
  investigation.md — Step 8 explicitly verifies this before relying on a post-shutdown read; if shutdown clears
  the counter, the read must move to before `kernel.shutdown()` is called.
- SURVIVAL-mode and queue-drop are two independent loss mechanisms (mode-shed vs. overflow-evict) — Steps 9 and
  12 test them independently; do not collapse them into a single `dropped_count > 0` check.
- Swap was nearly saturated at investigation time (920Ki free of 4.0Gi) — Step 4 explicitly treats the first
  measurement as indicative and requires a second, quieter-system run before Step 5/6 lock any numbers into the
  committed doc or regression threshold.
- The sidecar file (`quality_report.run_health.json`, Step 10) uses its own typed `RunHealthRecord`
  (Key Decision #3a), additive next to `quality_report.json`, never a modification to `QualityReport`'s own
  schema — keep this boundary exact so existing `QualityReport` consumers (`quality_hub.py`, `persistence.py`,
  etc.) are unaffected. Do not write it as a bare dict literal — the typed-record requirement was a blocking
  architecture-review finding, not a style preference.
- **The `CalibrationIntegrityError` raise in Steps 8 and 9 must never land inside `calibrate_simq.py`'s
  existing `try: kernel.shutdown() except Exception: pass` block** (calibrate_simq.py:251-254) — this was a
  blocking architecture-review finding: that bare `except Exception: pass` would silently swallow the guard's
  entire P0 hard-fail purpose if the raise statement ends up inside it. Keep the raise in its own statement,
  strictly before that try block begins.
- `calibrate_simq.py`'s existing zero-drop success path must remain byte-for-byte unchanged — every existing
  anchor-based test (`test_grade_regression.py` et al.) depends on it; Step 11's
  `test_calibrate_simq_succeeds_normally_with_zero_drops` is the explicit proof, and Step 17's regression pass
  re-confirms it against the full existing suite before the ticket is considered done.

## Deviations

1. **Guard raise placement (Steps 8/9) — raised AFTER, not BEFORE, the shutdown try/except block.**
   This plan's Anti-Drift Notes (and Key Decision #3) specified the `CalibrationIntegrityError` raise
   must occur "strictly BEFORE" `calibrate_simq.py`'s existing `try: kernel.shutdown() except Exception:
   pass` block, so it could never be silently swallowed by that bare except. Implementing this literally
   — i.e. skipping `kernel.shutdown()` entirely whenever the guard fails — was found at Implement time to
   leak the kernel's independent `DecisionTraceWriter` `QueueDrainWorker` background thread (started at
   Kernel construction, never stopped if `shutdown()` is never called), which trips
   `tests/conftest.py`'s session-scoped `_observability_worker_thread_sentinel` fixture — a real,
   pre-existing regression-guard test, not something this ticket may work around. **Resolution:**
   `kernel.shutdown()` is now called unconditionally (still wrapped in the original swallow-all
   try/except, byte-identical behavior for the success path), and the `CalibrationIntegrityError` raise
   is a separate statement placed *after* that block instead of before. This still satisfies the reviewed
   invariant the original wording was protecting — the raise is never nested inside, or catchable by, the
   try/except — while avoiding the thread leak. Confirmed via a clean fast-lane regression pass both
   before and after this fix (`tests/simulation_quality/ tests/unit/observability/
   tests/integration/observability/ -m "not slow"`).

2. **Overflow-test mechanism required more than `queue.max_size` mutation.** Step 7 described
   `_force_small_queue(kernel, max_size)` as a `queue.max_size` mutation mirroring
   `test_obs_backpressure.py::_set_queue_fill`. During Implement it was found that
   `ObservabilityController.evaluate()` enters SURVIVAL at fill≥1.00 — the exact same condition
   `BoundedObservabilityQueue.try_push()` uses internally to decide the queue is full — so in a
   single-threaded caller, `EventRecorder.record()` always diverts to SURVIVAL's counter-only path
   *before* `try_push()` can ever observe a full queue. Genuine `queue.dropped_count > 0` is therefore
   unreachable through the real `record()`/tick call path unless the mode-controller's fill perception is
   decoupled from the queue's real length. The overflow test (only) additionally monkeypatches
   `queue.get_size = lambda: 0` after calling `_force_small_queue`, so `record()` always perceives NORMAL
   mode and every event reaches `try_push()`, letting the queue's own internal capacity-check genuinely
   overflow. The SURVIVAL test (Step 12) does *not* use this override — it relies on real fill reaching
   the SURVIVAL threshold through the actual code path, which is the more direct and correct way to
   trigger that specific mechanism.

3. **"generic" scenario too inert for either guard test.** `calibrate_simq.py`'s default "generic"
   hero+goblins fallback scenario produces roughly 1 recordable event across 20 ticks (no
   engagement/AI-decision events are generated when goblins are placed clear of the hero, by design).
   Both the overflow and SURVIVAL guard tests use `sandbox_world` (seed 42) instead — a real, active
   compiled scenario that generates dozens of events per short run, needed to make queue-fill state
   reachable at all. The zero-drop anti-drift test still uses "generic", since a near-inert scenario is
   exactly what proves the default (5000-max) queue never overflows in normal operation.

4. **Regression-guard CPU-overhead bands set above measured overhead, not tight to it.** Step 6 called
   for thresholds "derived from measurement, then locked." The actual measured overhead was near-zero
   (in-process -8.4%, broker +0.6% vs. the disabled baseline — see `docs/performance/
   simq_isolation_overhead.md`), but two convergence-check runs of the *same* in-process code showed
   6.25%-8% run-to-run divergence on this session's swap-saturated sandbox. Locking a band tight to the
   near-zero measured value would make the regression guard measure noise, not real regressions. Bands
   were set with margin above the observed noise floor instead (25% in-process, 30% broker) — disclosed
   explicitly in the results doc as deliberately conservative for this environment, with re-tightening on
   a quieter machine noted as a legitimate (not required) follow-up.
