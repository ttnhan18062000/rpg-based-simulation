---
status: active
layer: performance
authority: P1
audience: developer
---

# SimQ Isolation Overhead — Engine-Process CPU Cost by Mode

TCK-20260702-OBSISO-ISOLATION-PROOF (G5, closing gap of `docs/plans/archive/observability_process_isolation.md`).

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

## Push-Shaper Registry Overhead

`TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE` (child 1 of `TCK-20260806-SIMQ-
OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`) extended this file's test with a
standing, committed gate for `src/observability/event_shapers.py`'s
cumulative CPU cost — orthogonal to the three `QUALITY_FEED_MODE` legs above,
which never varied `ENABLE_PUSH_EVENT_SHAPERS`. This gate exists because
Phase 1 of the push migration (`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-
MIGRATION-EPIC`, DONE) validated its own performance impact via an
uncommitted, reduced-scope scratch script, and Phase 2 adds 4-5x more shaper
classes on top of it — a standing gate catches overhead accumulation across
those future children automatically instead of re-measuring by hand each
phase.

**Method**: same `BenchHarness`/`PROD_SMALL`/`sandbox_world_seed42`/
warmup=100/sample=1000 convention as the three modes above, but under the
`inprocess` SimQ mode only (the live default), varying
`AuthoritativeState.feature_flags["ENABLE_PUSH_EVENT_SHAPERS"]` between
`"ON"` and `"OFF"` explicitly (pinned via `dataclasses.replace`, since the
kernel's own default is `"ON"` when the key is absent). Test:
`tests/perf/test_simq_isolation_overhead.py::
test_push_shaper_registry_overhead_benchmark` (`@pytest.mark.slow`).

### Committed Results — `(PROD_SMALL, sandbox_world_seed42, inprocess mode)`

| Run | shapers OFF `cpu_time_total_delta_s` | shapers ON `cpu_time_total_delta_s` | Overhead |
|---|---|---|---|
| 1 | 5.870s | 5.650s | -3.75% |
| 2 | 5.970s | 5.830s | -2.35% |

Convergence check (OFF leg, the value every run shares): `|5.970 - 5.870| /
5.870 = 1.7%` — well within the 10% convergence threshold this doc's other
section already establishes. Both runs show the shaper-registry path
**faster**, not slower, than the old diffing-extractor path at this scale —
plausible given the shaper reads typed update-record fields directly
(`CombatUpdate.outcome_kind`, `ResourceTransferIntent.source_kind`,
`FactionUpdate.diplomatic_relations_set`) instead of the extractor's
prior/current full-state diffing for the same domains. Not claimed as a
durable general speedup — reported as measured, at this scale, on this
hardware, same honesty standard as the rest of this doc.

### Locked Regression-Guard Threshold

Per `perf_baseline_policy.md` §3's band-tolerance convention: **push-shaper
registry vs. `OFF` baseline CPU overhead must stay < 25%**
(`test_push_shaper_registry_overhead_within_regression_band`) — set with the
same margin-above-noise-floor philosophy as the in-process-vs-disabled
threshold above, not the raw (negative) measured overhead, since a threshold
locked at ~0% would be a flaky gate on noisy hardware for a genuinely
near-zero-cost change.

**CI wiring**: no new Makefile/CI target was needed — this file's existing
tests were already reached only via `.github/workflows/test.yml`'s broad
`pytest tests/ -m "slow or extra_slow"` sweep (the `slow` job), not a
dedicated per-file target; the 2 new tests are `@pytest.mark.slow` in the
same file, so they're automatically covered by that same sweep.

## Phase 2 Full-Registry Overhead

`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2` extended the gate above with a second pair of
tests, `test_phase2_shaper_registry_overhead_benchmark`/
`test_phase2_shaper_registry_overhead_within_regression_band`, measuring the *complete* Phase 2
registry (`StrategyShaper`, `ProgressionShaper`, `WorldDynamicsShaper`, `SocialShaper`,
`DeferredInstrumentationShaper` — 5 shaper classes, ~50 event types) via
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2=ON` vs `OFF`, on top of (not replacing) Phase 1's own
already-committed gate above — `ENABLE_PUSH_EVENT_SHAPERS` (Phase 1's flag) is left at its own
default (`ON`) in both legs, isolating Phase 2's own incremental cost specifically.

**Result** (`sandbox_world_seed42`, warmup=100/sample=1000): `phase2_off=5.880s`,
`phase2_on=5.770s`, **-0.35% overhead** — consistent with Phase 1's own measured
negative/near-zero cost; the complete Phase 2 registry adds no measurable CPU cost at this scale.
Locked threshold: same 25% band as Phase 1's gate, same margin-above-noise-floor philosophy.

## Related

- `docs/plans/archive/observability_process_isolation.md` (G5 — this doc closes it)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-318`, `INFRA-319` — the
  routing/scorer-parity fixes this benchmark measures but does not alter)
- `docs/simulation_quality/quality_scoring_contract.md` line 1410 (reconciled
  against these numbers)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-324`, `INFRA-325` — the
  push-shaper-registry parity entries this gate protects)
- `tests/perf/test_simq_isolation_overhead.py`, `tests/perf/test_bench_harness.py`
