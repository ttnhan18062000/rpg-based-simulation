---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260817-RUNTIMEMODE-BENCH-SCOPING
artifact_type: test_plan
tags: [performance, engine, testing]
---

# Test Plan — TCK-20260817-RUNTIMEMODE-BENCH-SCOPING

## Regression Surface

**Unit**
- `tests/perf/test_bench_harness.py::test_bench_harness_cpu_time_sampling` — asserts on the
  `run_benchmark()` result-dict shape; must keep passing once `mode_sequence` is added (additive
  key, no existing key removed/renamed).
- `tests/unit/domains/optimization/test_phase_budget_governor.py` (all tests, esp.
  `test_resource_governor_propagates_phase_budgets`) — direct-construction pattern for forcing
  `ResourceGovernor`/`RuntimeStatus`/`PressureSignals` into non-NORMAL modes; must stay
  unaffected since this ticket does not touch `ResourceGovernor` or `PhaseBudgetGovernor` logic.
- `tests/unit/resource/test_resource_governor_contract.py::test_escalation_path`,
  `::test_multi_signal_escalation` — same reason.
- `tests/unit/kernel/test_verification_level.py` (all 3 tests) — exercises
  `RuntimeStatus.max_mode_reached`/`Kernel.shutdown().verification_level`, the nearest existing
  RuntimeMode-tracking behavior (INFRA-363); confirms this ticket's new sampling doesn't
  interfere with the existing mode-tracking path.
- `tests/unit/core/test_degradation_order.py`, `tests/unit/core/test_signal_truth.py` — governance
  isolation / degradation-order invariants adjacent to `RuntimeMode`; must stay unaffected.

**Integration**
- `tests/integration/kernel/test_milestone_b_closure.py` — Runtime Signals Contract closure tests
  covering `ResourceGovernor`; regression surface for the governor/signals plumbing this ticket
  reads from but does not modify.
- `tests/integration/pipeline/test_governance_isolation.py` — asserts `RuntimeMode`/
  `PressureSignals` never contaminate `AuthoritativeState`; directly relevant since the new
  per-tick sampling in `BenchHarness` must remain a pure read with the same isolation property.

**Perf / arena-combat**
- `tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline` (all 6 parametrize
  cases: `idle_100_local`, `movement_100_local`, `combat_10_local`, `simq_corpus_frontier_
  extended`, `simq_corpus_frontier_marches`, `simq_corpus_crowded_frontier`) — the test being
  modified; every existing case must still run and its existing `avg_tick_compute_ms` check must
  remain independently evaluated (acceptance criterion: new check is independent of the old one).
- `tests/perf/test_perf_idle.py`, `test_perf_movement.py`, `test_perf_combat.py`,
  `test_perf_resource.py`, `test_perf_strategic.py`, `test_perf_passive_scaling.py`,
  `test_perf_metropolis.py`, `test_perf_stress.py`, `test_profiler_integrity.py`,
  `test_hard_law_monitor_overhead.py`, `test_simq_isolation_overhead.py` — all call
  `BenchHarness.run_benchmark()` directly or via the `perf_harness`/`perf_budget` fixtures; must
  keep passing unmodified since `mode_sequence` is a purely additive result-dict key.
- No arena-combat-specific tests are in this ticket's regression surface (this is engine/perf
  layer, not `src/domains/combat_engagement/`).

## New Tests Required

1. **`test_run_benchmark_records_mode_sequence`**
   - Category: unit
   - Verifies: `BenchHarness.run_benchmark()`'s result dict contains a `mode_sequence` key, it is
     a list of length equal to (or otherwise well-defined relative to) `sample_ticks`, every
     element is a valid `RuntimeMode` name string, and for an ordinary low-load scenario (e.g.
     `build_idle_state`/`build_movement_state` with a small entity count and a generous profile
     like `PERF_1GB_LOCAL`) every entry is `"NORMAL"`.
   - Where: `tests/perf/test_bench_harness.py` (extends the existing file's coverage of
     `run_benchmark()`'s result-dict shape).

2. **`test_perf_regression_baseline_flags_runtime_mode_excursion`** (the ticket's required "new
   unit test" — "forces the Governor out of NORMAL mid-sample and asserts the gate surfaces the
   excursion")
   - Category: unit (fast, deterministic — prefer direct construction over a real starved
     benchmark run per the idiomatic pattern found in `test_phase_budget_governor.py`/
     `test_resource_governor_contract.py`)
   - Verifies: given a `mode_sequence` (or an equivalent harness result) containing at least one
     non-`"NORMAL"` entry, the gate's excursion-check logic surfaces it — via
     `pytest.warns(PerformanceThresholdWarning)` if Plan decides `hard=False`, or via
     `pytest.raises(AssertionError)` if Plan decides `hard=True` for this specific check — and
     that this happens **independent of** `avg_tick_compute_ms` staying within its normal
     threshold (construct a case where compute time is fine but mode excursion is not, to prove
     the two checks are decoupled per Acceptance Criterion 3).
   - Suggested construction: reuse the direct-construction idiom (`ResourceGovernor()` +
     `RuntimeStatus()` + a `PressureSignals` value chosen to exceed one of
     `ResourceGovernor._get_indicated_mode()`'s thresholds, e.g. `tick_compute_ms >=
     profile.max_tick_budget_ms`) to produce a synthetic `mode_sequence` list directly, OR patch
     `kernel.status.current_mode` mid-loop during a short (`sample_ticks<=5`) real
     `BenchHarness.run_benchmark()` call. Whichever Implement picks, the test must not rely on
     real load happening to trip the governor (non-deterministic / slow) — the excursion must be
     deliberately forced.
   - Where: `tests/perf/test_perf_regression_baseline.py` (co-located with the gate it tests) or
     `tests/perf/test_bench_harness.py` if it only exercises the sampling wiring rather than the
     gate assertion itself — Plan should pick one location and keep the gate-assertion logic and
     its test adjacent.

3. **`test_performance_contract_lists_runtimemode_scoped_claim`**
   - Category: architecture guard (doc-content check, mirrors existing doc-content static checks
     in this repo, e.g. `tests/tools/test_*_static.py` patterns)
   - Verifies: `docs/engine/performance_contract.md` §3.1 literally contains a `RuntimeMode`
     bullet alongside the existing 4 (Runtime Profile, Hardware Class, Scenario, Execution Mode) —
     a cheap regression guard against the doc drifting back out of sync with the enforced gate.
   - Where: new test file or an existing docs-static-check file if one already covers
     `performance_contract.md` (none was found in this investigation covering this specific file;
     Implement/Plan should confirm before creating a new file for a single assertion).

## Scoped Pytest Commands

Fast regression pass (excludes slow-marked scenario runs):
```
pytest tests/perf/test_bench_harness.py tests/perf/test_perf_regression_baseline.py \
  tests/unit/domains/optimization/test_phase_budget_governor.py \
  tests/unit/resource/test_resource_governor_contract.py \
  tests/unit/kernel/test_verification_level.py \
  tests/unit/core/test_degradation_order.py tests/unit/core/test_signal_truth.py \
  -m "not slow" -v
```

Full scoped pass including the slow-marked `perf`/`slow` scenario benchmarks (run before
declaring the gate change verified, since `test_regression_vs_baseline` itself is
`@pytest.mark.slow`):
```
pytest tests/perf/ tests/unit/domains/optimization/test_phase_budget_governor.py \
  tests/unit/resource/test_resource_governor_contract.py \
  tests/integration/kernel/test_milestone_b_closure.py \
  tests/integration/pipeline/test_governance_isolation.py -v
```

Never: `pytest tests/` (full suite) — CLAUDE.md Testing Rule.

## Anti-Drift Test Guards

- `test_run_benchmark_records_mode_sequence`'s all-`"NORMAL"`-under-low-load assertion doubles as
  a guard against accidentally sampling mode from the wrong source (e.g. a stale/cached
  `RuntimeStatus` that never updates) — a broken sampler that always reports `"NORMAL"` regardless
  of real state would still pass a naive "key exists" test but would be caught by pairing this
  with test #2's forced-excursion case, which must *not* read `"NORMAL"` when a mode was
  deliberately forced.
- `tests/integration/pipeline/test_governance_isolation.py` remaining green after this change is
  the guard against the new sampling code accidentally leaking `RuntimeMode`/mode-sequence data
  into `AuthoritativeState` or influencing tick execution (Governance Isolation Law,
  `signal_truth_contract.md` §7) — any implementation that reads `kernel.status.current_mode` in a
  way that mutates or feeds back into authoritative state would trip this test.
- Re-running `tests/perf/test_bench_harness.py::test_bench_harness_cpu_time_sampling` unmodified
  guards against the new `mode_sequence` key breaking the existing result-dict contract other
  perf tests depend on (additive-only change check).
- `test_performance_contract_lists_runtimemode_scoped_claim` guards against the doc and the
  enforced gate drifting apart again in the future (the exact failure mode C4 in
  `kernel_concurrency_design_review_proposal.md` originally reported: the doc/gate pair drifting
  silently out of sync).
