---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260702-OBSISO-ISOLATION-PROOF
artifact_type: test_plan
tags: [performance, observability, simulation-quality]
---

# Test Plan — TCK-20260702-OBSISO-ISOLATION-PROOF

## Regression Surface

Existing tests that must keep passing (grouped by domain touched by this ticket's code areas):

**Unit — observability queue/recorder (must be unaffected by any drop-guard code):**
- `tests/unit/observability/test_obs_backpressure.py` (mode transitions, `observability_status()` accuracy)
- `tests/unit/observability/test_event_recorder.py`
- `tests/unit/observability/stream/test_phase21_bounded_observability_queue.py`
- `tests/unit/observability/test_core_rules.py`

**Unit/Integration — SimQ calibration/evaluation harness (must be unaffected by the new drop guard's control flow):**
- `tests/simulation_quality/test_evaluate_harness.py`
- `tests/simulation_quality/test_grade_regression.py -m "not slow"` (fast tier)
- `tests/simulation_quality/test_kernel_simq_integration.py` (in-process/broker mode routing — `INFRA-318` regression coverage)
- `tests/simulation_quality/test_worker.py` (`INFRA-319` regression coverage — `QualityWorker` 10-pillar parity)
- `tests/simulation_quality/test_feed.py`, `tests/simulation_quality/test_broker_feed_integration.py` (skipped without `REDIS_AVAILABLE=1`; run if Redis is provisioned)

**Integration — kernel/observability wiring (must show the drop guard did not change normal-path behavior):**
- `tests/integration/observability/test_kernel_event_recording.py`
- `tests/integration/observability/test_phase21_non_blocking_event_emission.py`
- `tests/integration/observability/test_phase28_observability_degradation.py`

**Arena-combat:** none directly touched — this ticket does not modify combat resolution, only observability/SimQ plumbing and calibration tooling. No arena-tier regression surface identified.

**Existing perf precedents (structural, not this ticket's code, but must keep passing since the new benchmark should not duplicate/contradict them):**
- `tests/perf/test_production_observatory_overhead.py`
- `tests/simulation_quality/test_performance.py` (all 6 existing scorer-level tests)

## New Tests Required

Per acceptance criteria:

1. **`test_three_mode_engine_overhead_benchmark`**
   - Category: integration (slow lane)
   - Verifies: runs the same seed+scenario (`sandbox_world`, 200 ticks, per the ticket's anchor scenario — already a real committed anchor key, confirmed in `tests/simulation_quality/fixtures/grade_anchors.json`) under `QUALITY_SCORING_DISABLED=1`, `QUALITY_FEED_MODE=inprocess`, and `QUALITY_FEED_MODE=broker` (with a real `QualityWorker` subprocess), and produces wall-clock ticks/sec + engine-process CPU time (via `psutil.Process.cpu_times()`, sampled start/end — not currently captured by `src/perf/bench_harness.py::BenchHarness`, needs adding) for each. Marked `@pytest.mark.slow` (per `perf_baseline_policy.md` conventions — no absolute-time assertions on CI; only relative/band checks).
   - Location: `tests/simulation_quality/test_performance.py` (new engine-level section — see investigation.md's note that this file currently has zero `Kernel`-driving tests) or a new `tests/perf/test_simq_isolation_overhead.py` if keeping engine-level benchmarks out of the scorer-microbenchmark file is preferred (Plan decision).
   - **Depends on Redis provisioning** for the broker leg — see investigation.md's blocking risk. If Redis cannot be provisioned in a given environment, this test must skip broker-mode measurement gracefully (mirroring `REDIS_AVAILABLE` gating already used by `test_broker_feed_integration.py`) rather than fail outright, and the results doc must record which legs were actually measured on which hardware.

2. **`test_inprocess_simq_overhead_within_regression_band`**
   - Category: integration (slow lane), regression guard
   - Verifies: in-process SimQ engine-CPU overhead vs. `QUALITY_SCORING_DISABLED=1` baseline stays under a locked ratio threshold, derived from the first real measurement (per ticket AC — "derive the threshold from measurement, then lock it"). Must use a **relative** assertion (percentage over baseline), matching `perf_baseline_policy.md` §3.1's band-tolerance convention — never an absolute-ms assertion.
   - Location: same file as test 1, `@pytest.mark.slow`.

3. **`test_broker_mode_engine_cpu_within_disabled_band`**
   - Category: integration (slow lane), regression guard
   - Verifies: AC #2 — "Broker mode shows engine-process CPU within the agreed band of the disabled baseline." Requires the broker leg of test 1 to have run; skip (not fail) if Redis unavailable, with a clear skip reason.
   - Location: same file, `@pytest.mark.slow`.

4. **`test_calibrate_simq_fails_on_forced_queue_overflow`**
   - Category: unit/integration
   - Verifies: AC #3 — with a test-injected small `EventRecorder` queue (see investigation.md's open question on mechanism — recommend `kernel.event_recorder.queue.max_size` mutation, following `test_obs_backpressure.py::_set_queue_fill`'s precedent, unless Plan adds a Kernel-level override flag instead), a `calibrate_simq.py` run that provably drops ≥1 envelope (`dropped_count > 0`) hard-fails (non-zero exit / raises) rather than silently producing a `quality_report.json`.
   - Location: `tests/simulation_quality/test_calibrate_simq.py` (new file — no existing test file for `calibrate_simq.py`'s `main()`/`_run_engine()` functions was found).

5. **`test_evaluate_simq_flags_queue_overflow_run`**
   - Category: integration
   - Verifies: whichever `evaluate_simq.py` invocation Plan designates (per investigation.md's flagged AC-wording drift — almost certainly `evaluate-full`/non-dry-run, not literal `make evaluate`) surfaces the same overflow condition rather than reporting a clean pass. Must also cover the persisted-artifact gap noted in investigation.md: if drop/pressure state is not embedded in `quality_report.json`, a subsequent `--dry-run` diff cannot detect it — this test should assert whichever mitigation Plan picks (e.g., a sidecar `run_health.json` next to `quality_report.json`, or refusing to write `quality_report.json` at all on overflow).
   - Location: `tests/simulation_quality/test_evaluate_harness.py` (extends the existing file, consistent with `TCK-20260702-SIMQ-EVAL-HARNESS`'s own test file).

6. **`test_survival_mode_flags_run_instead_of_silently_grading`**
   - Category: unit/integration
   - Verifies: AC #4 — when backpressure forces `ObservabilityMode.SURVIVAL` (`queue_fill_ratio >= 1.00`), `EventRecorder.record()` takes the counter-only path (confirmed by code read: `event_recorder.py:171-174`, zero queue push) — SimQ receives nothing — and the calibration/evaluation guard flags the run rather than producing a report with a spuriously-clean (near-zero-event, misleadingly-high or -low) grade. Distinct assertion from test 4: SURVIVAL is a *different* loss mechanism than `dropped_count` (mode-shed vs. queue-overflow-evict) and the guard must check both, per investigation.md's Mechanics/Engine Constraints section.
   - Location: same new file as test 4, or `test_obs_backpressure.py` if the SURVIVAL-detection logic is factored as a standalone pure function.

7. **`test_bench_harness_cpu_time_sampling`** (supporting/infra test, only needed if `BenchHarness` is extended rather than a bespoke script written)
   - Category: unit
   - Verifies: if `src/perf/bench_harness.py::BenchHarness` is extended with a `psutil.Process.cpu_times()` sampler (recommended in investigation.md over writing new engine-driving code from scratch), the new field appears in `run_benchmark()`'s result dict and is monotonically non-decreasing across the sample window.
   - Location: `tests/perf/test_bench_harness.py` (new, or extend an existing `tests/perf/` file if one already covers `BenchHarness` — not confirmed to exist during this investigation; verify at Implement time before assuming "new").

## Scoped Pytest Commands

Fast-tier regression check (must pass before any slow-lane work):
```
pytest tests/simulation_quality/ tests/unit/observability/ tests/integration/observability/ -m "not slow" -q
```

Slow-lane new-benchmark verification (after implementation, on a quiet machine — see investigation.md's swap-pressure risk note):
```
pytest tests/simulation_quality/test_performance.py tests/perf/test_simq_isolation_overhead.py -m slow -q
```
(adjust the second path if the benchmark test lands in `tests/simulation_quality/test_performance.py` instead of a new `tests/perf/` file — do not run `pytest tests/` unscoped.)

Queue-drop / SURVIVAL guard verification:
```
pytest tests/simulation_quality/test_calibrate_simq.py tests/simulation_quality/test_evaluate_harness.py -q
```

Broker-mode round trip (only if Redis is provisioned in the run environment):
```
REDIS_AVAILABLE=1 pytest tests/simulation_quality/test_broker_feed_integration.py tests/simulation_quality/test_kernel_simq_integration.py -m slow -q
```

## Anti-Drift Test Guards

- A test asserting `ObservabilityMode.OFF` and `QUALITY_SCORING_DISABLED=1` are **not interchangeable** — e.g. constructing a kernel with `QUALITY_SCORING_DISABLED=1` and asserting `kernel.event_recorder.enabled is True` and that JSONL/stream writes still occur. This guards against a future refactor collapsing the two "off" concepts and silently invalidating this ticket's mode-(a) baseline.
- A test asserting the `DecisionTraceWriter`'s independent `QueueDrainWorker` thread count (`get_active_global_worker_count()`-style check, or a per-instance equivalent) is identical across all three benchmark configs when the same runtime profile is used — guards against the benchmark accidentally picking up TRACE-ASYNC's second worker as a confound.
- A test asserting `calibrate_simq.py`'s existing zero-drop success path is unchanged — run a normal small scenario, assert exit code / return value is unaffected by the new guard when `dropped_count == 0` and mode stays `NORMAL` throughout. This guards against the new hard-fail guard being over-eager and breaking every existing calibration/anchor-based CI check (`test_grade_regression.py` et al. all depend on `calibrate_simq.py` succeeding normally).
- A test asserting `INFRA-318`/`INFRA-319`'s existing behavior (broker mode builds zero in-engine `QualityHub`; `QualityWorker` builds all 10 pillars) is unchanged by this ticket — this ticket must only *measure* those paths, never alter their routing logic. Re-run `test_kernel_simq_integration.py`'s four `INFRA-318`-cited tests and `test_worker.py`'s two `INFRA-319`-cited tests as an explicit anti-regression check before considering this ticket done.
- A test asserting the new regression-guard threshold in `test_performance.py`/`test_simq_isolation_overhead.py` uses a **relative** (percentage-over-baseline) assertion, not an absolute wall-clock or CPU-ms literal — guards against violating `perf_baseline_policy.md` §3's band-tolerance convention the very first time this benchmark is written.
