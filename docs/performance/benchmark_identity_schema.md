---
status: active
layer: performance
authority: P2
audience: agent
tags: [performance, benchmarking, schema, documentation]
---

# Benchmark Identity and Result Schema (PERF-M2-T02 design draft)

> **Provisional design draft under the RPG-core stability entry gate.** Nothing in this document is
> implemented or binding. It becomes a contract only when `PERF-M2-T03`, `T04` and `T05` adopt it,
> and only after the entry gate lifts and M1 has reported the corrections that change benchmark
> identity (§8). It is based on reading code and committed files on 2026-10-03; no benchmark,
> baseline or profile was run for it. The owner approved writing it before the gate as a deliberate
> exception (`TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA`).

Inputs: `docs/performance/performance_clause_inventory.md` (`PERF-M2-T01`), PERF-D1, D2 and D4 in
`docs/architecture/performance_optimization_decisions.md`, the M2 epic's "Required contract
dimensions" (`docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md`),
and `docs/plans/design_enhancement/performance_optimization/performance_stack_survey.md`.

## 1. Inventory of result formats that exist today

One producer feeds most of them: `src/perf/bench_harness.py::BenchHarness.run_benchmark` returns the
dict that is the "harness dict" below. Its keys: `scenario_id`, `profile` (profile name only),
`sample_ticks`, `wall_clock_s`, `wall_clock_tps`, `compute_tps`, `avg_tps`, `tick_ms{avg,p50,p95,p99,max,min}`,
`mem_rss_mb{avg,max,delta}` (sampled every 10th tick), `phase_breakdown`, `metrics` (per-tick means),
`cpu_time_{user,system,total}_delta_s`, `replay_enabled`, `frame_pacing_enabled`, `timestamp`,
`mode_sequence` (one `RuntimeMode` name per measured tick), plus flat aliases such as
`avg_tick_compute_ms`. Callers add `matrix_scenario/scale/mode` (`tools/perf/run_benchmarks.py`) or
`source_world`, `source_entity_count`, `source_region_count` (`tools/bench_corpus_world.py`).

| ID | Format (path) | Writer | Reader | Notes |
|---|---|---|---|---|
| F1 | `tests/perf/baselines/*.json` (15 files: 12 synthetic at 20 sample ticks, 3 `simq_corpus_*` at 1000) | synthetic: copied by hand (no script, `perf_baseline_policy.md` §2.1); corpus: `tools/bench_corpus_world.py --commit` | `tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline` (reads `profile`, `avg_tick_compute_ms` only); `tools/perf/check_perf_regression.py` | Harness dict. None of the 15 contains `mode_sequence`. Tripwire references only |
| F2 | RuntimeMode check inside the same test (`_assert_runtime_mode_stayed_normal`) | in memory | same test | `_RUNTIME_MODE_HARD_SCENARIOS` is an empty frozenset, so every excursion is soft; nothing is persisted |
| F3 | corpus baseline checks, `tests/tools/test_corpus_perf_baseline.py` | none | asserts `scenario_id`, and that `profile`, `avg_tick_compute_ms`, `tick_ms`, `mem_rss_mb` exist | |
| F4 | `tools/bench_corpus_world.py` stdout JSON | `bench_corpus_world()` | human, or F1 via `--commit` | seed and warmup are inputs but not written |
| F5 | `reports/perf/matrix_full.json`, `reports/perf/<scenario>_<scale>_<mode>.json` (git-ignored) | `tools/perf/run_benchmarks.py::run_matrix` | `tools/perf/perf_report.py`, `check_perf_regression.py` | failed scenarios are skipped silently |
| F6 | `tools/perf/check_perf_regression.py`, `tools/perf/perf_ci.py` | stdout and exit code only | n/a | pairs baseline and report by file name only; a missing report is a skipped warning; second threshold policy (×1.15 or +3 ms on average and per-phase p95, +20 MB RSS) beside F1's `max(5 ms, ×1.25)` |
| F7 | `reports/perf/baseline.json`, `reports/perf/latest.json` (git-ignored) | `tools/perf/run_perf_baseline.py` (scenario-keyed dict of harness dicts); `tests/perf/bench_worker_throughput.py` (a different, flat shape); `tools/perf/perf_baseline.py` (copies latest to baseline) | `tools/release/generate_optimization_proof.py`, `tests/perf/test_optimization_proof_report.py` | `latest.json`: two writers, two incompatible shapes; `baseline.json`: a copy made by `perf_baseline.py`. Fixed by `TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER`: `bench_worker_throughput.py` now writes `worker_throughput.json`, `perf_baseline.py` runs `run_perf_baseline.py` and `--update` refuses a non-scenario-keyed file. |
| F8 | `reports/perf/<test name>.json` | `tests/perf/conftest.py::perf_reporter` (any `@pytest.mark.perf` test that sets `perf_results`) | `tools/perf/perf_report.py` fallback glob | the glob can ingest mixed shapes |
| F9 | `reports/perf/optimization_proof.{json,md}` | `tools/release/generate_optimization_proof.py::run_proof` | `tests/perf/test_optimization_proof_report.py` (key presence, `speedup_x > 0`) | see finding 1 Fixed by `TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS` (claims and defaults only): each scenario is now `compared` or `not_comparable` with a reason, the `1.0` fallbacks and fixed conclusion text are gone, and the report is labeled provisional. |
| F10 | `reports/perf/profiles/comparison.json` | `tools/release/verify_production_profiles.py::run_suite` | none | `{profile: {scenario: {p95_ms, avg_tps, peak_rss} or "CRASHED"}}`, 10 warmup and 10 sample ticks |
| F11 | `perf_baselines.json` (root; `entries` is `{}`), `.perf_last_run.json` | by hand from `tools/perf_guard.py` proposals; `PerfMeasurePlugin` for the last-run file | `tests/perf/conftest.py::_perf_baselines`, `perf_budget` fixture | per-pytest-nodeid `{time_ms, memory_kb, tolerance_pct, hardware_class, rationale, updated_by, updated_at}`; hardware class is the `PERF_HARDWARE_CLASS` env label (default "B"), not detected |
| F12 | `src/perf/regression_gate.py` (`PerfBaseline`, `PerfResult`, `PerfGateResult`) | none (never serialized) | `tests/unit/perf/test_perf_regression_gate.py` only | no consumer (`perf_baseline_policy.md` §3); reads `raw_entity_updates` from a top-level key the harness never emits (it writes `metrics.raw_entity_updates`), so it always reads 0 |
| F13 | `assert_perf_threshold` / `perf_check` (`tests/tools/perf_assertions.py`) | `PerformanceThresholdWarning` text in pytest output | none | a breach is never persisted; 66 call sites counted, `hard=True` at none of the literal calls (clause inventory §7) |
| F14 | `docs/performance/{phase,hash_callsite,wall_clock}_inventory.json`, `tools/perf/perf_threshold_inventory.py` output | the `tools/perf/*_inventory.py` tools | their own `--check` modes, `tests/tools/test_*_inventory.py` | evidence documents, not measurements; they carry `tool` and `ticket` keys and no schema version |
| F15 | profiling toolkit artifacts under `reports/perf/` (git-ignored): `phases.json`, `phases.md`, `profile.folded`, `profile.speedscope.json`, `memray*`, `flag_attribution/*.{md,json}`, `profile_diff` output | `tools/perf/profile_tick.py`, `flag_attribution.py`, `_profiling_common.py` | `profile_diff.py` reads `profile.folded` headers; no reader for the rest | header: `commit` (+ dirty-src flag), `scenario`, `entities`, `seed`, `warmup_ticks`, `measured_ticks`, `python`, `host_cores`; stamped PROVISIONAL, explicitly not a baseline or capacity claim; `profile_diff.py` warns when commit, scenario, entities or seed differ |
| F16 | `reports/profile/*.prof`, `*.txt`, `report.md`, `sweep_summary.json`, `sweep_report.md` | `tools/perf/profile_engine.py`, `profile_sweep.py` | `tests/perf/test_profile_sweep.py` (pure functions only) | cProfile timings, inflated by the profiler; sweep records `contention_at_start` (load average, core count), the only environment-noise record in the repo |
| F17 | `reports/profiling/baseline.json` | `tools/perf/profile_memory.py::run_suite` | the same function | `{suite, peak_rss_mb, timestamp}` of a whole pytest subprocess, not a simulation |
| F18 | `tools/perf/memory_probe.py` JSON (`--output`) | `_write_json` | none | `{rss_delta_bytes, worker_count_delta, event_recorder_delta, top_allocations}`, a synthetic queue-drain workload; a leak check, not performance |
| F19 | `ws_payload_<N>.json`, `ws_payload_<N>_ABORTED.json` | `tools/perf/live_map_ws_payload_measure.py::main` | none | message byte sizes, not time; the only format with `attempted`, `aborted`, `abort_reason` |
| F20 | `tools/perf/profile_api_payload.py` | stdout only | none | payload sizes; imports `EngineManager`, possibly stale (not verified) |
| F21 | `tools/perf/turbo_run.py` | stdout scorecard, `logs/stress_test.jsonl` (application log) | none | 5000 ticks, seed 111, `PROD_LARGE`, wall `time.time()`, no warmup |
| F22 | `reports/certification/long_run_{pure,runtime}_stability.json` | `tests/certification/test_cert_long_run_stability.py` via `LongRunStabilityReport.to_dict()` (`src/perf/long_run_harness.py`) | none | keys `scenario_id, run_mode, total_ticks, entity_count, seed, metrics{...}, certifications{..., passed_certification}, final_state_hash`; `to_dict()` drops `warmup_ticks`, `sample_interval_ticks` and the raw samples (including per-sample `active_mode`) |
| F23 | `src/observability/performance/` `PhaseTimingRecord` | `PhaseProfiler.profile_phase` (in memory) | tests only | `run_id, tick, phase_name, duration_ns, entity_count, update_count, event_count, provider_call_count, cache_hit_count, cache_miss_count, budget_status, failed`; never persisted, not called by the kernel |
| F24 | kernel in-memory signals (`kernel.status.get_recent_history`: `tick_compute_ms`, `phase_costs_ms`, `metrics`) | `src/engine/kernel.py` | `src/engine/governor.py`, F0 and F15 | source of the per-tick data above |
| F25 | `docs/performance/simq_isolation_overhead.md` | by hand (no file write found in `tests/perf/test_simq_isolation_overhead.py`) | thresholds in that test are "locked from" the document | named comparative result; no machine-readable form |

Not verified: assertion text and extra outputs of most `tests/perf/test_perf_*.py`, the thresholds
behind `passed_certification`, `verify_determinism_parity`'s return shape, `governance_scenarios.py`,
and the `EngineManager` import in F20. Line numbers were taken from a read-only pass and are not
repeated here; the paths and function names are the citations.

### Findings for perf-planner (not corrected here)

1. **Claims without identity.** F9's markdown states "consistent speedups" and "strict isolation ...
   preventing measurement jitter" as fixed text regardless of the data. A missing baseline key
   defaults to `1.0`, which inflates the speedup silently, and it compares `PROD_*` runs against a
   baseline whose profile is never checked. F22's `passed_certification` is an outcome claim with
   no runtime identity.
   Fixed by `TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS` for the proof report (the `1.0` defaults, the unchecked profile, the fixed text); `passed_certification` is not changed by it.
2. **Hardware class is a label, not a measurement.** Every `PERF_*` profile is hard-coded
   `CLASS_A` (`src/perf/profiles.py`), and F11 reads it from an environment variable.
3. **Comparison run lengths differ from baseline lengths.** The synthetic baselines were taken at 20
   sample ticks, the corpus ones at 1000, and the live test re-measures all of them at warmup 10 and
   sample 50. `check_perf_regression.py` has no length check at all.
4. **Percentiles are computed three ways.** The harness uses `sorted[int(n*q)]`, so p95 is the max
   only when n ≤ 20 and p99 is the max only when n ≤ 100. All 12 synthetic baselines (n = 20) record
   p95 = p99 = max, and the live tripwire's 50-tick sample records p99 = max while its p95 is the
   48th of 50 values. The profiling toolkit uses nearest-rank `ceil(0.95n)`; the sweep uses
   `round(p*(n-1))`.
5. **Two threshold policies and one name collision.** F1's reader and `check_perf_regression.py`
   disagree (see F6). `reports/perf/latest.json` has two writers with incompatible shapes (`run_perf_baseline.py` and `bench_worker_throughput.py`), and `perf_baseline.py` copies whichever ran last to `baseline.json`.
   Fixed by `TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER` (the `latest.json` half only): `latest.json` has one writer, and `perf_baseline.py --update` validates the shape before promoting.
6. **No performance result format or perf gate has an `INCONCLUSIVE` outcome.** (The word exists
   elsewhere, unrelated: a Gate A read-path verdict in `src/observability/warehouse/adapters.py`
   and `tests/tools/test_gate_a_readpath_review.py`.) The only explicit outcome states are F19's
   `attempted/aborted/abort_reason`, F22's boolean certifications, and F10's `"CRASHED"`.
7. **A committed baseline cannot prove it ran in `NORMAL`.** None of the 15 files has
   `mode_sequence`, and the hard-scenario set that would enforce it is empty.

## 2. Coverage matrix

Columns group the formats by the identity they record: **H** harness dict (F1, F3, F4, F5, F7, F8),
**P** optimization proof (F9), **C** profile comparison (F10), **B** `perf_baselines.json` (F11),
**G** `PerfBaseline` (F12), **T** profiling toolkit (F15), **S** cProfile outputs (F16), **L** long-run
report (F22), **W** WS payload (F19), **R** `PhaseTimingRecord` (F23), **O** other (F13, F17, F18,
F20, F21, F6, F10 aside). Cells: `R` recorded, `P` partial, `A` absent, with the field name.

| Dimension | H | P | C | B | G | T | S | L | W | R | O |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Scenario id | R `scenario_id` | R scenario name | P label key | R pytest nodeid | R `scenario_id` | R `scenario` | R scenario | R `scenario_id` | P file name | A | P F17 suite name |
| Builder / checkpoint | A | A | A | A | A | A | A | A | A | A | A |
| Workload cardinality | P `matrix_scale`, `source_entity_count` (caller-added) | A | A | A | A | R `entities` | P sweep `entity_count`, engine `.txt` Entities | R `entity_count` | R `entities` | P `entity_count` per record | A |
| Engine version | A | A | A | A | A | R `commit` + dirty-src flag | A | A | A | A | A |
| Content / rules | P `source_world` (name only, corpus) | A | A | A | A | A | A | A | A | A | A |
| Config | P `profile` (name) | A | P profile key | A | A | P `profile` | P `Flags` (engine `.txt`) | A | A | A | A |
| RNG seed | A | A | A | A | A | R `seed` | A | R `seed` | R `seed` | A | A |
| Schema version | A | A | A | P file-level `version` | A | A | A | A | A | A | A |
| Baseline version | A | A | A | P `updated_at` | A | A | A | A | A | A | A |
| Hardware / runtime | A | A | A | P `hardware_class` (env label) | A | P `python`, `host_cores` | P `contention_at_start` | A | A | A | A |
| DET-PORT tier | A | A | A | A | A | A | A | A | A | A | A |
| Determinism contract (PERF-D1) | A | A | A | A | A | A | A | P `run_mode` (pure or runtime, not the D1 contract) | A | A | A |
| Executor / backend | P `matrix_mode`, profile suffix | A | P profile key | A | A | A | A | A | A | A | A |
| Worker count | A (implied by profile name) | A | A | A | A | A | A | A | A | A | P F18 `worker_count_delta` |
| Warmup | A | A | A | A | A | R `warmup_ticks` | A | A | R `warmup_ticks_target` | A | A |
| Measured ticks | R `sample_ticks` | A | A | A | A | R `measured_ticks` | P `ticks_completed` | R `total_ticks` | P `count` | P `tick` | A |
| Repetitions | A | A | A | A | A | P `repetitions` (flag attribution) | A | A | A | A | A |
| Raw samples | A (aggregates only) | A | A | A | A | R per-tick lists in `phases.json` | A | A (dropped by `to_dict()`) | A | R per record | A |
| Latency distribution | R `tick_ms` | P `p95_ms` | P `p95_ms` | A | R `p95/p99_tick_compute_ms` | P mean, p95 (nearest-rank) | P `tick_ms_avg/p50/p95/max` | P `initial_p95`, `final_p95` | P byte-size percentiles (not time) | R `duration_ns` | A |
| Throughput | R `compute_tps`, `wall_clock_tps` | R `tps` | P `avg_tps` | A | R `compute_tps` | A | A | A | A | A | P F21 printed TPS |
| CPU / wall time | R `wall_clock_s`; P `cpu_time_*` (newer runs) | A | A | P `time_ms` (whole test) | A | P per-tick `wall_ms` | A | A | P `wall_seconds` | A | P F21 elapsed |
| Memory high-water | R `mem_rss_mb.max` (1-in-10 sampling) | R `peak_rss_mb` | P `peak_rss` | P `memory_kb` | R `peak_rss_mb` | A (memray optional) | A | R `peak_rss_mb` | A | A | P F17 `peak_rss_mb` (whole suite) |
| Scaling slope | A | A | A | A | A | A | A | A | A | A | A |
| `RuntimeMode` sequence | P `mode_sequence` (absent from all 15 baselines) | A | A | A | A | R run-length `runtime_mode_sequence` | A | A (dropped) | A | A | A |
| Verification level | A | A | A | A | A | A | A | A | A | A | A |
| Processed / dropped / coalesced | P `metrics.*` means | P `metrics` | A | A | P `raw/compacted_entity_updates` (reads a key the harness never writes) | P `work_mean_per_tick` | P `metrics` snapshot | A | A | R update, event, provider, cache counts | A |
| Replay / hash validity | A | A | A | A | A | A | A | R `final_state_hash` | A | A | A |
| Observer level | P `replay_enabled`, `frame_pacing_enabled` | A | A | A | A | A (fixed, not written) | P `Flags` | A | A | A | A |
| Gate tier | A | A | A | A | A | P PROVISIONAL stamp text | A | A | A | A | A |
| Outcome state | A (a breach raises) | A | P `"CRASHED"` | A | P in-memory `PerfGateResult` | A | A | P `certifications.*` booleans | R `attempted`, `aborted`, `abort_reason` | P `budget_status`, `failed` | A |

Reading the matrix: no format records engine version, content/rules, schema version, DET-PORT tier,
verification level, gate tier, executor, worker count or repetitions together with the rest, and
none records a scaling slope. The profiling toolkit (T) is the closest to an identity header; the
long-run report (L) is the only one with a hash; the WS tool (W) is the only one with an abort state.

## 3. Proposed schema

One versioned record. `schema_version` is `MAJOR.MINOR`; a MAJOR change is any change to a field
listed as blocking in §4, or to a field's meaning. Two parts: **identity** (what was measured and
where) and **result** (what came out). A record is valid only with both.

### 3.1 Field table

Source column: "today" names code that can supply the field now; "not yet" names the milestone that
provides it.

**Identity**

| Field | Type | Req. | Source |
|---|---|---|---|
| `schema_version` | string `MAJOR.MINOR` | required | constant in the writer; not yet (`PERF-M2-T03`) |
| `scenario.id` | string | required | today: `BenchHarness` `scenario_id`. Note: an id must not map to `build_metropolis_state()` until `TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION` is fixed |
| `scenario.builder` | string (module path and function) | required | not yet (`PERF-M2-T03`); builders live in `src/perf/scenarios.py` |
| `scenario.builder_version` | string (content hash of the builder source) | optional | not yet |
| `scenario.checkpoint_id` | string or null | required | not yet; null for from-scratch builds |
| `workload.entity_count` | integer ≥ 0 | required | today: the state at start (`len(state.entities)`); the harness does not record it, callers add it |
| `workload.region_count` | integer or null | optional | today: corpus path only (`source_region_count`) |
| `workload.unit` | string (for example `entities`, `pairs`) | required | not yet; combat scales count pairs, not entities |
| `engine.commit` | string (git SHA) | required | today: `_profiling_common.git_commit` |
| `engine.dirty_src` | boolean | required | today: `_profiling_common.git_commit` (`git status --porcelain -- src`) |
| `content.world_id` | string or null | required | today: corpus path (`source_world`) |
| `content.content_hash` | string | required | not yet (M1/M3 identity work; no content hash exists today) |
| `content.rules_version` | string | optional | not yet |
| `config.profile_name` | string | required | today: `RuntimeProfile.name` |
| `config.profile_hash` | string | required | not yet; hash of the resolved `RuntimeProfile` fields |
| `config.flags` | object of boolean | required | today: `replay_enabled`, `frame_pacing_enabled`; `audit_mode` and other flags are not recorded yet |
| `rng.seed` | integer | required | today: scenario builder argument (default 42), not written by the harness |
| `runtime.python_version` | string | required | today: `platform.python_version()` |
| `runtime.implementation` | string | required | today: `platform.python_implementation()` |
| `runtime.build_flavor` | string (for example `gil`, `free-threaded`) | required | not yet; PERF-D2 names it |
| `runtime.os` | string | required | today: `platform.system()`, `platform.release()` |
| `runtime.arch` | string | required | today: `platform.machine()` |
| `runtime.cpu_model` | string | required | not yet (pyperf records `cpu_model_name`) |
| `runtime.logical_cores` | integer | required | today: `os.cpu_count()` |
| `runtime.ram_mb` | integer | required | not yet; needed because `certification_contract.md` §3 defines hardware class by cores and RAM |
| `runtime.native_kernels` | object name → version | required (empty allowed) | not yet; no native kernel exists today |
| `runtime.hardware_class` | string (`certification_contract.md` §3) | required | not yet (M2-T05); today profiles hard-code `CLASS_A` and `PERF_HARDWARE_CLASS` is an env label, neither detected |
| `runtime.det_port_tier` | enum `DET-PORT-0/1/2` | required | not yet; derived from the fields above and the "Scope of the guarantee" section of `deterministic_execution.md` |
| `contract.determinism` | enum `canonical`, `live_bounded` | required | not yet (PERF-M1; PERF-D1) |
| `contract.verification_level` | string (for example `FULL`, `REDUCED`) | required | not yet; runs that reach DEGRADED or SURVIVAL keep a `REDUCED` label (C-04) |
| `executor.backend` | enum `sequential`, `thread`, `process` | required | not yet; implied today by the `_LOCAL`/`_CONC` profile suffix |
| `executor.worker_count` | integer ≥ 1 | required | not yet; PERF-M1-T01 changes what zero means |
| `observer.level` | string | required | not yet (M3); today `replay_enabled`, `frame_pacing_enabled`, `audit_mode`, profiler attachment |
| `gate.tier` | enum `tripwire`, `capacity_run`, `comparative` | required | `performance_contract.md` §3 |
| `gate.projection` | string | required | not yet (`PERF-M2-T03`/`T04`) |
| `baseline_ref` | object `{id, schema_version, record_digest}` or null | optional | not yet (`PERF-M2-T05`) |

**Result**

| Field | Type | Req. | Source |
|---|---|---|---|
| `protocol.warmup_ticks` | integer | required | today: harness argument, not written |
| `protocol.measured_ticks` | integer | required | today: `sample_ticks` |
| `protocol.repetitions` | integer ≥ 1 | required | today: `flag_attribution` only |
| `protocol.percentile_method` | enum `nearest_rank`, `linear` | required | not yet; three methods exist today (finding 4) |
| `protocol.clock` | string (`perf_counter`, `process_time`, `instructions`) | required | not yet |
| `protocol.gc_disabled` | boolean | required | today: harness disables gc during sampling, unrecorded |
| `samples.tick_wall_ms` | array of number, or `{uri, sha256}` | required for `capacity_run`, optional for `tripwire` | today: toolkit `phases.json`; the harness drops it |
| `latency_ms` | object `{avg, p50, p95, p99, max, min}` | required | today: `tick_ms` |
| `throughput` | object `{compute_tps, wall_tps}` | required | today: harness |
| `time_s` | object `{wall, cpu_user, cpu_system}` | required | today: harness (CPU includes warmup, which wall does not; the schema fixes one window) |
| `memory_mb` | object `{rss_high_water, rss_delta, sample_every_ticks}` | required | today: `mem_rss_mb`, sampled every 10th tick; `delta` is max minus min of samples |
| `scaling_slope` | object or null | optional | not yet (M4) |
| `runtime_mode_sequence` | array of `{mode, ticks}` (run-length) | required | today: `mode_sequence` per tick; toolkit compresses |
| `work` | object `{processed, dropped, coalesced, phase_runs, phase_skips}` | required | today: `metrics` per-tick means and kernel `_metrics`; dropped and coalesced names are not yet defined |
| `validity` | object `{replay_ok, final_state_hash, hash_scheme}` | required for `capacity_run` | today: `final_state_hash` only in F22; `hash_scheme` waits for `PERF-M1-T03` |
| `phases` | object phase → latency object | optional | today: `phase_breakdown` |
| `outcome.state` | enum `PASS`, `REGRESSION`, `INCONCLUSIVE`, `NOT_APPLICABLE` | required | `performance_contract.md` §3.3; not implemented anywhere today |
| `outcome.reason` | enum code plus free text | required | not yet |
| `recorded_at` | string RFC 3339 | required | today: `timestamp` (epoch float) |

### 3.2 JSON Schema draft

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "benchmark-result-v0.1-provisional",
  "title": "Benchmark result record (provisional PERF-M2-T02 draft)",
  "type": "object",
  "required": ["schema_version", "identity", "result"],
  "additionalProperties": false,
  "properties": {
    "schema_version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+$"},
    "identity": {
      "type": "object",
      "required": ["scenario", "workload", "engine", "content", "config", "rng", "runtime", "contract", "executor", "observer", "gate"],
      "additionalProperties": false,
      "properties": {
        "scenario": {
          "type": "object",
          "required": ["id", "builder", "checkpoint_id"],
          "properties": {
            "id": {"type": "string", "minLength": 1},
            "builder": {"type": "string"},
            "builder_version": {"type": "string"},
            "checkpoint_id": {"type": ["string", "null"]}
          }
        },
        "workload": {
          "type": "object",
          "required": ["entity_count", "unit"],
          "properties": {
            "entity_count": {"type": "integer", "minimum": 0},
            "region_count": {"type": ["integer", "null"], "minimum": 0},
            "unit": {"type": "string"}
          }
        },
        "engine": {
          "type": "object",
          "required": ["commit", "dirty_src"],
          "properties": {"commit": {"type": "string"}, "dirty_src": {"type": "boolean"}}
        },
        "content": {
          "type": "object",
          "required": ["world_id", "content_hash"],
          "properties": {
            "world_id": {"type": ["string", "null"]},
            "content_hash": {"type": "string"},
            "rules_version": {"type": "string"}
          }
        },
        "config": {
          "type": "object",
          "required": ["profile_name", "profile_hash", "flags"],
          "properties": {
            "profile_name": {"type": "string"},
            "profile_hash": {"type": "string"},
            "flags": {"type": "object", "additionalProperties": {"type": "boolean"}}
          }
        },
        "rng": {
          "type": "object",
          "required": ["seed"],
          "properties": {"seed": {"type": "integer"}}
        },
        "runtime": {
          "type": "object",
          "required": ["python_version", "implementation", "build_flavor", "os", "arch", "cpu_model", "logical_cores", "ram_mb", "native_kernels", "hardware_class", "det_port_tier"],
          "properties": {
            "python_version": {"type": "string"},
            "implementation": {"type": "string"},
            "build_flavor": {"type": "string"},
            "os": {"type": "string"},
            "arch": {"type": "string"},
            "cpu_model": {"type": "string"},
            "logical_cores": {"type": "integer", "minimum": 1},
            "ram_mb": {"type": "integer", "minimum": 1},
            "native_kernels": {"type": "object", "additionalProperties": {"type": "string"}},
            "hardware_class": {"type": "string"},
            "det_port_tier": {"enum": ["DET-PORT-0", "DET-PORT-1", "DET-PORT-2"]}
          }
        },
        "contract": {
          "type": "object",
          "required": ["determinism", "verification_level"],
          "properties": {
            "determinism": {"enum": ["canonical", "live_bounded"]},
            "verification_level": {"type": "string"}
          }
        },
        "executor": {
          "type": "object",
          "required": ["backend", "worker_count"],
          "properties": {
            "backend": {"enum": ["sequential", "thread", "process"]},
            "worker_count": {"type": "integer", "minimum": 1}
          }
        },
        "observer": {
          "type": "object",
          "required": ["level"],
          "properties": {"level": {"type": "string"}}
        },
        "gate": {
          "type": "object",
          "required": ["tier", "projection"],
          "properties": {
            "tier": {"enum": ["tripwire", "capacity_run", "comparative"]},
            "projection": {"type": "string"}
          }
        },
        "baseline_ref": {
          "type": ["object", "null"],
          "required": ["id", "schema_version", "record_digest"],
          "properties": {
            "id": {"type": "string"},
            "schema_version": {"type": "string"},
            "record_digest": {"type": "string"}
          }
        }
      }
    },
    "result": {
      "type": "object",
      "required": ["protocol", "latency_ms", "throughput", "time_s", "memory_mb", "runtime_mode_sequence", "work", "outcome", "recorded_at"],
      "additionalProperties": false,
      "properties": {
        "protocol": {
          "type": "object",
          "required": ["warmup_ticks", "measured_ticks", "repetitions", "percentile_method", "clock", "gc_disabled"],
          "properties": {
            "warmup_ticks": {"type": "integer", "minimum": 0},
            "measured_ticks": {"type": "integer", "minimum": 1},
            "repetitions": {"type": "integer", "minimum": 1},
            "percentile_method": {"enum": ["nearest_rank", "linear"]},
            "clock": {"enum": ["perf_counter", "process_time", "instructions"]},
            "gc_disabled": {"type": "boolean"}
          }
        },
        "samples": {
          "oneOf": [
            {"type": "object", "required": ["tick_wall_ms"], "properties": {"tick_wall_ms": {"type": "array", "items": {"type": "number"}}}},
            {"type": "object", "required": ["uri", "sha256"], "properties": {"uri": {"type": "string"}, "sha256": {"type": "string"}}}
          ]
        },
        "latency_ms": {
          "type": "object",
          "required": ["avg", "p50", "p95", "p99", "max", "min"],
          "additionalProperties": {"type": "number"}
        },
        "throughput": {
          "type": "object",
          "required": ["compute_tps", "wall_tps"],
          "properties": {"compute_tps": {"type": "number"}, "wall_tps": {"type": "number"}}
        },
        "time_s": {
          "type": "object",
          "required": ["wall", "cpu_user", "cpu_system"],
          "additionalProperties": {"type": "number"}
        },
        "memory_mb": {
          "type": "object",
          "required": ["rss_high_water", "rss_delta", "sample_every_ticks"],
          "properties": {
            "rss_high_water": {"type": "number"},
            "rss_delta": {"type": "number"},
            "sample_every_ticks": {"type": "integer", "minimum": 1}
          }
        },
        "scaling_slope": {"type": ["object", "null"]},
        "runtime_mode_sequence": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["mode", "ticks"],
            "properties": {"mode": {"type": "string"}, "ticks": {"type": "integer", "minimum": 1}}
          }
        },
        "work": {
          "type": "object",
          "required": ["processed", "dropped", "coalesced"],
          "properties": {
            "processed": {"type": "integer", "minimum": 0},
            "dropped": {"type": "integer", "minimum": 0},
            "coalesced": {"type": "integer", "minimum": 0},
            "phase_runs": {"type": "integer", "minimum": 0},
            "phase_skips": {"type": "integer", "minimum": 0}
          }
        },
        "validity": {
          "type": "object",
          "required": ["replay_ok", "final_state_hash", "hash_scheme"],
          "properties": {
            "replay_ok": {"type": "boolean"},
            "final_state_hash": {"type": "string"},
            "hash_scheme": {"type": "string"}
          }
        },
        "phases": {"type": "object", "additionalProperties": {"type": "object"}},
        "outcome": {
          "type": "object",
          "required": ["state", "reason"],
          "properties": {
            "state": {"enum": ["PASS", "REGRESSION", "INCONCLUSIVE", "NOT_APPLICABLE"]},
            "reason": {"type": "string", "minLength": 1}
          }
        },
        "recorded_at": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

`samples` and `validity` are required by the tier rules in §3.1 (capacity run), not by this
structural schema; a tier-aware validator belongs to `PERF-M2-T03`/`T04`.

## 4. Comparability rule

Two records are comparable only if every **blocking** field below is equal. Otherwise the
comparison returns `INCONCLUSIVE` with the differing field in `outcome.reason`, never a pass and
never a skip that reads as success. A missing baseline, a baseline with a different MAJOR
`schema_version`, and a record with a required field absent are all `INCONCLUSIVE` as well.

| Field | Treatment | Why |
|---|---|---|
| `schema_version` MAJOR | blocking | meaning of fields changed |
| `schema_version` MINOR | recorded only | additive; a newer reader reads older records, absent optional fields are "unknown" |
| `scenario.id`, `scenario.builder`, `scenario.builder_version`, `scenario.checkpoint_id` | blocking | different workload |
| `workload.entity_count`, `workload.region_count`, `workload.unit` | blocking | cost scales with it |
| `engine.commit`, `engine.dirty_src` | recorded only | the difference is the thing being compared; a dirty tree is recorded and flagged, and a `capacity_run` rejects `dirty_src: true` |
| `content.world_id`, `content.content_hash`, `content.rules_version` | blocking | a content change is a workload change |
| `config.profile_name`, `config.profile_hash`, `config.flags` | blocking | flags such as audit mode change cost |
| `rng.seed` | blocking | different seed, different trajectory |
| `runtime.python_version` minor, `implementation`, `build_flavor`, `os`, `arch`, `cpu_model`, `native_kernels` | blocking | PERF-D2 treats each as a runtime identity |
| `runtime.python_version` patch | recorded only | not part of the DET-PORT-0 definition |
| `runtime.logical_cores`, `runtime.ram_mb`, `runtime.hardware_class` | blocking | hardware class is defined by them |
| `runtime.det_port_tier` | blocking | a hash proof is comparable only within its tier |
| `contract.determinism`, `contract.verification_level` | blocking | different contract, different work |
| `executor.backend`, `executor.worker_count` | blocking | different execution route |
| `observer.level` | blocking | observer cost is part of the measurement |
| `gate.tier`, `gate.projection` | blocking | a tripwire result never stands in for a capacity run |
| `protocol.*` (warmup, measured ticks, repetitions, percentile method, clock, gc) | blocking | a 20-tick and a 1000-tick sample are not comparable (finding 3) |
| `runtime_mode_sequence` | blocking when either side left `NORMAL`; otherwise recorded | an excursion changes the work done (`RuntimeMode` can leave `NORMAL`) |
| `validity.hash_scheme` | blocking when both carry a hash; digests of different schemes are not comparable (PERF-D5) | two digests produced by different hash schemes can differ with identical state, so a mismatch proves nothing |
| `recorded_at`, host name, load average | recorded only | noise context; load average may add a variance warning, not a verdict |

**Schema version change.** A MAJOR bump invalidates every stored baseline of the older MAJOR for
comparison. They stay readable and are reported `INCONCLUSIVE` until migrated or re-recorded by an
owner-approved baseline update (`PERF-M2-T05`), which records the cause ticket and the before and
after identities. A MINOR bump only adds optional fields. The reader never guesses a missing
required field.

## 5. Tool mapping

The survey (`performance_stack_survey.md`, "Benchmark harness" and "CI regression tracking" rows)
picks `pytest-benchmark` for the PR lane, `pyperf` for controlled confirmation runs, and
instruction-count measurement for the tripwire. No tool is installed or added by this draft.

**`pytest-benchmark` 5.3.0** (documentation `pytest-benchmark.readthedocs.io/en/stable`, fetched
2026-10-03; key names from the 5.3.0 source `stats.py` and `utils.py`).
- Emits per benchmark: `group`, `name`, `fullname`, `params`, `param`, `extra_info`, `options`, and
  `stats` with `min`, `max`, `mean`, `stddev`, `rounds`, `median`, `iqr`, `q1`, `q3`,
  `iqr_outliers`, `stddev_outliers`, `outliers`, `ld15iqr`, `hd15iqr`, `ops`, `total`. Top level has
  `version`, `datetime`, `benchmarks`, and a `commit_info` with `id`, `time`, `author_time`,
  `dirty`, `project`, `branch`. The `--benchmark-json` page documents that raw timings are
  included; the full `machine_info` key list was not on the fetched pages and is **not verified**.
- Maps to: `latency_ms` (its `median` is `p50`; it has no p95 or p99, so those come from raw data),
  `protocol.measured_ticks` (`rounds`), `engine.commit` and `engine.dirty_src` (`commit_info`).
- Repository adds through `extra_info` (documented: set `benchmark.extra_info[...]`): the whole
  `identity` block, `runtime_mode_sequence`, `work`, `validity`, `outcome`. Its comparison features
  do not know the comparability rule, so the repository's own comparison runs on the stored records.

**`pyperf`** (documentation `pyperf.readthedocs.io/en/stable`, fetched 2026-10-03; the pages name
0.8.2 as the version of the JSON example; the exact release to pin is an open question, §7).
- Records run metadata: `name`, `loops`, `inner_loops`, `unit`, `date`, `duration`,
  `python_version`, `python_implementation`, `python_executable`, `python_compiler`,
  `python_cflags`, `python_hash_seed`, `cpu_count`, `cpu_model_name`, `cpu_freq`, `cpu_affinity`,
  `hostname`, `platform`, `aslr`, `boot_time`, `uptime`, `load_avg_1min`, `mem_max_rss`,
  `command_max_rss`; separates `values` from `warmups`.
- Maps to: `runtime.python_version`, `implementation`, `cpu_model`, `logical_cores` (`cpu_count`),
  `os`/`arch` (`platform`), `protocol.warmup_ticks`, `repetitions` (processes), `memory_mb`
  (`mem_max_rss`), `samples`.
- Repository adds through the documented `metadata` argument of `Run`/`Runner`: the remainder of
  `identity`, `ram_mb` (not recorded by pyperf), `hardware_class`, `det_port_tier`,
  `runtime_mode_sequence`, `work`, `validity`, `outcome`.

**Instruction-count tripwire.** The survey names the technique (CodSpeed and similar) without
selecting a tool, so there is no output format to cite. The schema reserves `protocol.clock =
instructions` and expects the tool to supply the count and its own version, which this repository
records as `extra_info`. Choosing the tool is `PERF-M2-T03`.

## 6. Migration

| Format | Disposition |
|---|---|
| F1 `tests/perf/baselines/*.json` | Keep outside the schema as tripwire references (PERF-D4). They keep `tripwire` semantics, are labeled unlabeled-identity, and are re-recorded in the new schema by `PERF-M2-T05` when a baseline is promoted. A converter would invent absent identity, so none is proposed |
| F2 mode check | Replaced by `runtime_mode_sequence` and the comparability rule; the empty hard-scenario set goes away |
| F3 corpus checks | Updated by `T03` to assert the new required fields |
| F4, F5, F7 (`run_perf_baseline.py` shape), F8 | Map into the schema: the harness dict becomes `result`, the caller-added fields move into `identity` |
| F6 `check_perf_regression.py`, `perf_ci.py` | Retire in favor of the single comparison over the schema; the two threshold policies collapse into the contract's thresholds (set by `T03`, not here) |
| F7 `bench_worker_throughput.py` writer and `perf_baseline.py` | Retire from the `latest.json` path (no consumer for the flat shape); keep `bench_worker_throughput.py` as a separate measurement with its own file name |
| F9 optimization proof | Retire the fixed prose; regenerate from schema records that carry identity, with a missing baseline key an error, not `1.0`. Until then treat its speedups as unlabeled |
| F10 comparison | Retire (no consumer); `CRASHED` becomes `outcome.state = INCONCLUSIVE` with reason `crashed` |
| F11 `perf_baselines.json`, `.perf_last_run.json` | Keep outside the schema: per-test wall budgets with a tolerance, whole-test granularity; the file is empty. `T03` decides whether to retire it (clause inventory §5.2 records `PerfBudget` as tripwire-adjacent debt) |
| F12 `PerfBaseline` / `PerfResult` | Retire; `src/` removal is out of this draft and waits for the `src/` freeze to lift |
| F13 threshold warnings | Keep as the in-test outcome channel; `T03` decides how a breach becomes an `outcome` record |
| F14 inventories | Keep outside the schema (evidence documents, not measurements) |
| F15 profiling toolkit | Keep outside the schema as diagnostic evidence stamped PROVISIONAL; align its header names to `identity` where the names overlap so a profile can cite a record |
| F16, F17, F18, F20, F21 | Keep outside the schema: profiles with profiler overhead, whole-suite memory, a leak probe, payload sizes and a stress run, none of which is a benchmark result in this sense |
| F19 WS payload | Keep outside the schema (bytes, not time); its `attempted/aborted/abort_reason` is the model for `outcome.reason` codes |
| F22 long-run report | Map `scenario_id`, `entity_count`, `seed`, `final_state_hash`, memory into the schema as a `capacity_run`-tier record; stop dropping `samples`, `warmup_ticks` and `active_mode`; `passed_certification` is replaced by `outcome` |
| F23 `PhaseTimingRecord` | Candidate source for `phases` and `work` if the kernel ever calls it (M3); not a result record |
| F24 kernel signals | Source, not a format |
| F25 `simq_isolation_overhead.md` | Keep (named comparative result); a machine-readable `comparative` record is future work |

Existing `tests/perf/baselines/` files remain tripwire references, per PERF-D4.

## 7. Open questions

For perf-planner and the owner.

1. Which instruction-count tool does the tripwire use, and does the owner accept a hosted tracking
   service (open with the owner; PERF-D4's revisit condition names it)?
2. Which `pyperf` release is pinned, and is the `stable` documentation's JSON identical to that
   release? The fetched pages cite 0.8.2 only as the version of an example.
3. The full `machine_info` key set of `pytest-benchmark` 5.3.0 was not on the fetched pages; confirm
   from the installed package at adoption.
4. `content.content_hash` and `scenario.builder_version` have no source today. Is a content hash an
   M1 or M3 deliverable?
5. Should a `capacity_run` record embed raw samples, or keep a `{uri, sha256}` pointer? Size and
   retention depend on the runner decision (`PERF-M2-T04`).
6. Which percentile method is the contract's? Nearest-rank is the toolkit's and `pyperf`-friendly;
   the harness's `int(n*q)` makes p95 equal the max at 20 ticks or fewer and p99 equal the max at 100 ticks or fewer.
7. Is `runtime.hardware_class` detected from cores and RAM per `certification_contract.md` §3, or
   declared by the runner configuration?
8. Should the blocking set vary by projection? `runtime.cpu_model` and `runtime.logical_cores` are
   blocking, so a wall-clock tripwire on shared CI runners whose CPU model varies would often return
   `INCONCLUSIVE`. An instruction-count tripwire (the survey's choice) may not need `cpu_model` to
   block. This draft does not change the rule.
9. Should a `RuntimeMode` excursion be `INCONCLUSIVE` or `REGRESSION`? §4 makes it `INCONCLUSIVE`
   when either side left `NORMAL`, but a head-side excursion against a `NORMAL` base may be the
   regression itself, and the live test already fails hard on it for scenarios in
   `_RUNTIME_MODE_HARD_SCENARIOS` (empty today). This draft does not change the rule.
10. Findings 1 to 7 in §1: which become tickets? Finding 1 (claim text without identity) touches a
   file under `tools/release/`.

### M1 candidates that could change identity fields

The M2 entry condition "M1 identifies every correction that changes benchmark or baseline identity"
is not met. These are the fields each M1 candidate could affect
(`performance_m1_correctness_prerequisites_epic.md`):

| M1 candidate | Identity or result fields it may change |
|---|---|
| `PERF-M1-T01` zero-capacity semantics | `executor.worker_count` (what zero and disabled mean), `runtime_mode_sequence` (the DEGRADED trigger), `contract.verification_level`; every concurrent-profile baseline |
| `PERF-M1-T02` debt-harness correctness | `work.*` accounting and any debt-related counters; `scenario.checkpoint_id` if fixtures change |
| `PERF-M1-T03` hash-policy reconciliation | `validity.hash_scheme`, `validity.final_state_hash`, persistence-phase cost in `phases`, and any baseline taken with the old schedule |
| `PERF-M1-T04` tied-result determinism | `executor.backend`, `executor.worker_count`, and the supported-protocol statement behind `runtime.det_port_tier` |
| `PERF-M1-T05` invalidation ledger | the list of stored artifacts that stay valid, need a rerun, or are incomparable; this document's migration table is rechecked against it |
| PERF-D1 amendment A1 (wall-clock reads) | `observer.level` and `protocol.clock` if wall-clock reads in decision inputs become configuration |

## 8. Revalidation

This draft is re-read after M1 reports its identity-changing corrections and after the entry gate
lifts. Until then: no field here is a requirement, no threshold or runner is chosen, and the
existing gates keep their current behavior.
