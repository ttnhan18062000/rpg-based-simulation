---
status: active
layer: performance
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING
tags: [performance, testing, calibration]
---

# Investigation — TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING

## Context Scan
- `search_docs("performance threshold hardware calibration warning")` and
  `search_docs("perf test assertion CI hard failure warning")` surfaced
  `docs/testing/regression_policy.md` §3 (Soft Monitors — Alert Only, the existing
  "important but does not block merge" convention this ticket extends),
  `docs/engine/architecture.md` §5 (Hardware Classes), `docs/engine/performance_contract.md`
  §3 (Benchmarking Rules), `docs/performance/perf_baseline_policy.md`, and the precedent
  ticket `TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION`.
- `graphify query "performance_contract hardware class"` traversed `HardwareClass` /
  `HardwareClassifier` (`src/config/profiles.py`, `src/certification/hardware.py`,
  `src/certification/models.py`) — confirms hardware-class scoping is a first-class engine
  concept, not something this stopgap invents in parallel.
- Read `docs/engine/performance_contract.md` in full (Hardware Classes A/B/C, §3.2
  measurement protocol, §5 Regression Enforcement) and `docs/testing/test_taxonomy.md` §4
  (Performance Test Authoring — the existing `perf_budget` fixture / `perf_baselines.json`
  convention in `tests/perf/conftest.py`).
- Read the precedent ticket `tickets/done/TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-
  CALIBRATION.md` and its per-test evidence in full — confirms the 5 files
  (`test_hard_law_monitor_overhead.py`, `test_perf_api_snapshot.py`,
  `test_perf_passive_scaling.py`, `test_perf_strategic.py`, `test_arena_stress.py`) already
  carry real measured-headroom thresholds; this ticket does not re-touch those numbers.

## Existing conventions found (why the new mechanism fits, not duplicates)
- `tests/perf/conftest.py::PerfBudget.assert_within_budget()` — an existing hard-assert
  helper tied to `perf_baselines.json`. Currently **unused by any real test** in
  `tests/perf/` (`perf_baselines.json`'s `entries` dict is empty; the only fixture
  consumers are `tests/unit/perf/test_perf_guard.py`, unit-testing the fixture itself, out
  of this ticket's scope). Extended (not replaced) with a `hard` parameter for consistency
  rather than leaving two parallel perf-assertion idioms in the tree.
- `tests/tools/memory_probe.py` — the existing precedent for "shared, importable,
  cross-suite (perf/arena/root conftest) test helper lives in `tests/tools/`". The new
  `tests/tools/perf_assertions.py` follows this exact placement convention.
- `docs/testing/regression_policy.md` §3 "Soft Monitors — Alert Only" is the doc-level
  precedent for "important but non-blocking, tracked as P1/P2" — this ticket's mechanism is
  the code-level implementation of that same idea for perf-threshold-specific assertions,
  and §3's table is updated to reference it (see plan.md).

## Per-file disposition (every file in tests/perf/, tests/arena/, tests/certification/ read individually)

### tests/perf/ — CONVERTED (genuine perf-threshold hard asserts)
| File | Assertions converted | Left hard (if any) |
|---|---|---|
| test_perf_movement.py | `p95_tick_compute_ms < threshold` | — |
| test_perf_resource.py | `p95_tick_compute_ms < threshold` | — |
| test_perf_combat.py | `p95_tick_compute_ms < 750.0` | — |
| test_perf_idle.py | `avg_tps > 20.0`, `mem_rss_mb.max < 512.0`, `tick_ms.p99 < 100.0` | — |
| test_perf_stress.py | `avg_tps > 5.0`, `mem_rss_mb.max < 1024.0`, `tick_ms.p99 < 200.0` | — |
| test_perf_strategic.py *(precedent)* | `p95_tick_compute_ms < 1650.0` | — |
| test_phase6_progression_conversion_budget.py | `t_duration_ms < 5.0` | — |
| test_phase8_world_emergence_budget.py | `duration_ms < 5.0` | — |
| test_api_projection_perf.py | `speedup >= 3.0` | `metrics["hits"] > 0` (cache-was-used correctness, not a calibration number) |
| test_phase9_campaign_semantic_budget.py | `avg_overhead_per_tick < 5.0` | — |
| test_phase2_self_model_budget.py | `t_warm_ms < 50.0`, `t_clean_ms < 5.0`, dirty-check `ratio >= 5.0` | — |
| test_hard_law_monitor_overhead.py *(precedent)* | `overhead < 0.60` | — |
| test_observability_scale_validation.py | `duration < 1.0` (10-tick wall time) | `len(event_recorder.events) == 0` (telemetry-must-not-accumulate correctness) |
| test_perf_api_snapshot.py *(precedent)* | 4x `p95 < 1.5`/`< 2.5` (present_minimal/to_readonly) | — |
| test_perf_metropolis.py | 6 asserts across 3 tests (`avg_tps`, `tick_ms.p99`, `mem_rss_mb.max`, `growth_per_tick`) | — |
| test_perf_passive_scaling.py *(precedent)* | 3x `p95_ms` branches, `max_rss`, `mem_delta` | — |
| test_perf_regression_baseline.py | `current_avg <= threshold` | — |
| test_phase10_integrated_enhanced_stack_budget.py | 5x `elapsed_ms < 1000.0`/`1500.0` | `res.allowed or "exhausted" in ...` inside the shared helper (budget-exhaustion-handling correctness, not timing) |
| test_phase3_adventure_decision_budget.py | `t_delta_ms < 70.0` | — |
| test_phase4_combat_engagement_budget.py | `duration_ms < 15.0` | — |
| test_phase5_information_belief_budget.py | `duration_ms < 5.0` | — |
| test_phase7_social_cooperation_budget.py | `median_duration < 25.0` | `metric_counters["cooperation_evaluations"] == 50` (correctness) |
| test_production_observatory_overhead.py | `overhead_pct < threshold`, `p95 < 200.0` | — |
| test_profiler_integrity.py | `elapsed_ms < 500.0` (pacing-disabled proxy) | `"replay_enabled" in result`/`is False`, `tick_compute >= phase_sum`, `"persistence" in ...`, `compute_tps >= wall_clock_tps` (all correctness/invariant, not calibration numbers; the last is separately CI-timing-jitter `skipif`'d already, unrelated mechanism) |
| test_simq_isolation_overhead.py | 4x `overhead_pct < *_BAND_PCT` | all `*.cpu_time_total_delta_s > 0` (baseline-was-positive correctness, needed for the ratio math itself, not a calibration threshold) |

### tests/perf/ — NOT CONVERTED (no genuine perf-threshold assert present)
| File | Why |
|---|---|
| test_phase28_behavior_observability_overhead.py | Asserts hardcoded `PRESET_PRODUCTION` config constants are sane (`<= 3.0`, `<= 0.5`) — a static config-value sanity check, not a measured runtime value. Hardware-independent. |
| test_bench_harness.py | CPU-time-delta monotonicity/equality invariants — correctness, not threshold calibration. |
| test_optimization_proof_report.py | `speedup_x > 0`/`latency_reduction_x > 0` are structural sanity floors (can't be negative), not calibrated numbers; rest is schema/artifact-existence correctness. |
| bench_apply_path.py, bench_capacity.py, bench_worker_throughput.py | `if __name__ == "__main__"` standalone scripts, no `test_`-prefixed function — not pytest-collected, zero assertions. |
| test_apply_compaction_perf.py | Only `fingerprint()` equality + count equality — correctness. |
| test_concurrency_parity.py | Only local-vs-concurrent state-hash equality — correctness. |
| test_dirty_parity.py | Only optimized-vs-full-scan state-hash equality — correctness. |
| test_dirty_set_integrity.py | DirtySet membership/exception-raising correctness. |
| test_lod.py | `assertEqual` on scheduled work-item counts — correctness (LOD selection logic), not timing. |
| test_profile_sweep.py | Pure unit tests of `scripts/profile_sweep.py`'s analysis functions on synthetic fixture stats — no real timing measured at all. |

### tests/arena/ — CONVERTED
| File | Assertions converted |
|---|---|
| test_arena_stress.py *(precedent)* | `result.peak_rss_mb < 375.0` |

### tests/arena/ — NOT CONVERTED
`test_arena_quests.py`, `test_arena_regional_control.py`, `test_arena_startup.py`,
`test_arena_stop_conditions.py`, `test_arena_tactics.py` — all assert game-state
correctness (quest status, gold amounts, region influence, entity counts, stop-condition
enum values, group formation) via `CertificationHarness`. Zero timing/memory/throughput
assertions in any of these five files (confirmed by full read, not just filename).

### tests/certification/ — CONVERTED (narrow, explicit carve-out only)
| File | Assertions converted | Explicitly NOT touched |
|---|---|---|
| test_cert_long_run_stability.py | `test_long_run_pure_stability`'s 4 flags: `report.rss_bounded`, `report.latency_stable`, `report.caches_bounded`, `report.gc_stable` (each is a resource/timing-drift threshold computed by `LongRunStabilityHarness`) | `test_long_run_determinism_parity` (whole test, per explicit instruction); `test_long_run_pure_stability`'s `baseline_hash`/`final_hash` equality (none present in this test directly — hash comparison lives inside `verify_determinism_parity`, called only by the determinism test) and its `report.passed_certification` (harness compound flag, left conservative — see ticket's Assumptions); `test_long_run_runtime_stability`'s `report.passed_certification` (same reasoning) |

### tests/certification/ — NOT CONVERTED (rest of directory, confirmed by full read + targeted grep for `assert .*[<>]`)
`test_allowed_failure_truth.py`, `test_artifact_budget.py` (grep-confirmed: only
`len(...) <= 5` sampling caps), `test_cert_result_serialization.py` (grep-confirmed: zero
`<`/`>` comparisons), `test_envelope_violations.py`, `test_event_observability_parity.py`
(hash parity), `test_final_gate.py` (artifact/manifest validation), `test_harness_contract.py`,
`test_manifest_snapshot.py`, `test_phase10_enhanced_determinism_parity.py` (hash/dict
equality), `test_phase10_enhanced_rollout_gate.py` and
`test_phase28_behavior_observability_rollout_gate.py` (unit-test a *gate script's own
validation logic* against synthetic fixture JSON reports — these must assert the gate
correctly flags a fabricated regression; converting them to soft would defeat their
purpose), `test_recorder_refactor.py` (grep-confirmed: zero `<`/`>` comparisons),
`test_resilience_recovery.py`, `test_world_compile_determinism.py` (hash determinism).

## Verification of scope command shapes
- `.github/workflows/test.yml`'s `perf-cert-arena` job:
  `pytest tests/perf tests/certification tests/arena -m "not slow and not extra_slow" --tb=short -q`
- `.github/workflows/test.yml`'s `slow` job:
  `pytest tests/ -m "slow or extra_slow" --resource-budget large --tb=short -q --ignore=tests/unit/worldassembly/test_corpus_diversity.py`
Both commands are used for post-change verification in test_plan.md.
