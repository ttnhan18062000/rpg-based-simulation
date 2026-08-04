---
status: active
layer: performance
authority: P1
audience: developer
---

# SimQ Isolation Overhead — Engine-Process CPU Cost by Mode

TCK-20260702-OBSISO-ISOLATION-PROOF (G5, closing gap of `docs/plans/observability_process_isolation.md`).

Measures and budgets the engine-process cost of the three SimQ configurations
Requirement R1 ("engine performance not affected by external components")
covers, replacing the code-read-only claim previously standing at
`docs/simulation_quality/quality_scoring_contract.md` line 1410 with a real
measurement.

## Method

- **Harness**: `src.perf.bench_harness.BenchHarness.run_benchmark()`, extended
  in this ticket with a `psutil.Process.cpu_times()` start/end delta
  (`cpu_time_total_delta_s`). Warmup=100 ticks, sample=1000 ticks (1,100 total
  engine ticks per mode), per `perf_baseline_policy.md` §2.1's minimums.
  `flags={"no_replay": True, "no_frame_pacing": True}` (M1 defaults).
- **Scenario**: `sandbox_world`, seed 42, compiled via `WorldCompiler` (same
  world-loading path `tools/calibrate_simq.py::_load_world_state` uses).
- **Profile**: `PROD_SMALL` (`src/config/profiles.py`).
- **`OBS_DECISION_TRACE`**: held constant at `"1"` across all three modes so
  `DecisionTraceWriter`'s independent `QueueDrainWorker` thread (orthogonal to
  `QUALITY_FEED_MODE`) cannot become an uncontrolled confound between runs.
- **Test**: `tests/perf/test_simq_isolation_overhead.py::test_three_mode_engine_overhead_benchmark`
  (`@pytest.mark.slow`) is the source of these numbers — this doc summarizes,
  it does not duplicate, that test's own measurement code.

### The three modes

| Mode | Config | What's built in-engine |
|---|---|---|
| (a) disabled | `QUALITY_SCORING_DISABLED=1` | `EventRecorder` fully enabled (JSONL/stream/queue keep running); only the `quality_fn` callback is skipped. **This is NOT `ObservabilityMode.OFF`** — do not compare against `tests/perf/test_production_observatory_overhead.py`'s OFF-vs-LIGHT numbers, which measure a different toggle entirely. |
| (b) inprocess | `QUALITY_FEED_MODE=inprocess` (default) | Full `QualityHub` + all 10 pillar scorers, wired into `EventRecorder`'s single `QueueDrainWorker`. |
| (c) broker | `QUALITY_FEED_MODE=broker` | Zero in-engine `QualityHub` (`INFRA-318`) — engine only produces events onto a Redis stream; scoring happens entirely in a separate `QualityWorker` subprocess (`INFRA-319` scorer-parity fix already landed). |

Mode (a)'s distinction from `ObservabilityMode.OFF` is enforced by a running
assertion in the test itself
(`kernel.event_recorder.enabled is True`, and `simulation_events.jsonl` is
confirmed non-empty after ticking), not just this doc's prose.

## Hardware Class

`certification_contract.md` §3's binary AND-rule (`CLASS_B` requires **both**
≥4 logical cores **and** ≥8GB total RAM) is used as canonical, per this
ticket's Key Decision #4. This session's measurement machine: 4 logical cores,
5.8GB total RAM — 4 cores clears the `CLASS_B` core bar, but 5.8GB fails the
RAM bar, so under the binary rule this machine is **`CLASS_C`**.

**Flag, not resolved by this ticket**: `perf_baseline_policy.md` §2.2 defines
its `CLASS_B`/`CLASS_C` table by a *different*, core-count-only reading (its
`CLASS_C` = "2 Cores, 2GB RAM" — this machine's 4 cores would not fit that
table's `CLASS_C` row either). The two docs' hardware-class tables are
genuinely inconsistent; this is a pre-existing conflict, out of this ticket's
scope to resolve. Numbers below are reported as `CLASS_C` per
`certification_contract.md`'s explicitly-canonical binary rule.

## Environment caveat — swap pressure

At implementation time, this sandbox's swap was under heavy, sustained
pressure (near 100% utilized throughout measurement, average available RAM
~1GB). Per the ticket's own Anti-Drift Notes, the first measurement run is
treated as indicative only; a second run is required before locking numbers.

**Convergence check** (in-process `cpu_time_total_delta_s`, the leg every
config shares):
- Run 1 (indicative): disabled=6.410s, inprocess=6.080s, broker=6.920s
- Run 2: disabled=7.050s, inprocess=6.460s, broker=7.090s
- Divergence: `|6.460 - 6.080| / 6.080 = 6.25%` — within the 10% convergence
  threshold (chosen to sit comfortably above `perf_baseline_policy.md` §3's
  own p99 band-tolerance of +15%). Run 2 is therefore committed as final,
  per the plan's convergence rule.
- A third, full run (executed while verifying the regression-guard tests
  below actually pass against the locked thresholds) produced a consistent
  third data point (disabled=6.900s, inprocess=6.630s, broker=6.950s),
  reinforcing that the committed numbers are not an outlier.

## Committed Results — `(PROD_SMALL, sandbox_world_seed42, CLASS_C)`

| Mode | Wall-clock TPS | Engine CPU time (`cpu_time_total_delta_s`, 1,100 ticks) |
|---|---|---|
| (a) disabled | 167.13 | 7.050s |
| (b) inprocess | 180.57 | 6.460s |
| (c) broker | 166.70 | 7.090s |

**Broker leg**: measured (Redis was reachable via a manually-provisioned
container, `docker run -d --name simq-isolation-proof-redis -p 6379:6379
redis:7-alpine`, per this ticket's Key Decision #7). Not skipped in this
session.

### Overhead vs. disabled baseline

| Mode | CPU overhead vs. disabled |
|---|---|
| (b) inprocess | **-8.4%** (no measurable overhead at this scale — within measurement noise) |
| (c) broker | **+0.6%** |

Both figures are well inside measurement noise (the run-to-run divergence
observed for the identical in-process leg across the two convergence-check
runs above was itself 6.25%, and up to ~8% on the broker leg between runs 1
and 2). This is consistent with `quality_scoring_contract.md` line 1410's
existing "< 1% overhead" claim for in-process mode — see Step 15's
reconciliation there.

## Locked Regression-Guard Thresholds

Per `perf_baseline_policy.md` §3's band-tolerance convention (relative,
never absolute wall-clock/CPU-ms), and set with margin above this session's
measured run-to-run noise floor (~6-8%) rather than the raw measured overhead
itself, to avoid a flaky gate on noisy hardware:

- **In-process vs. disabled**: CPU overhead must stay **< 25%**
  (`test_inprocess_simq_overhead_within_regression_band`).
- **Broker vs. disabled**: CPU overhead must stay **< 30%**
  (`test_broker_mode_engine_cpu_within_disabled_band`, skips — does not
  fail — when Redis is unavailable).

A tighter band could likely be justified on a quieter (non-swap-saturated)
machine; these thresholds are deliberately conservative given the only
environment available to measure them this session. Re-tightening is a
legitimate follow-up once a clean-machine measurement exists, not required
by this ticket's acceptance criteria.

## Related

- `docs/plans/observability_process_isolation.md` (G5 — this doc closes it)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-318`, `INFRA-319` — the
  routing/scorer-parity fixes this benchmark measures but does not alter)
- `docs/simulation_quality/quality_scoring_contract.md` line 1410 (reconciled
  against these numbers)
- `tests/perf/test_simq_isolation_overhead.py`, `tests/perf/test_bench_harness.py`
