---
status: active
layer: performance
authority: P1
audience: developer
---

# Engine Performance Baseline Policy

## 1. Purpose and Scope

This document establishes the official engineering policy for performance baseline calibration, regression gating, and CI benchmarking across the RPG simulation engine. All commits must pass these automated performance gates to prevent performance degradation and memory bloat.

---

## 2. Standard Benchmarking Protocol

To ensure reproducible measurements across varying environments, all performance benchmarks must adhere to the following execution protocol:

### 2.1 Execution Windows
- **Warmup Period**: All benchmark runs must execute a minimum of 100 warmup ticks before timing metrics are recorded. This allows JIT compilation, spatial index seeding, and Python internal object allocation caches to stabilize.
- **Sampling Window**: A benchmark baseline must capture a minimum of 1,000 continuous simulation ticks.

### 2.2 Scoped Hardware Classes
Performance baselines are calibrated specifically for targeted hardware profiles:
- **`CLASS_A` (High-Performance Server)**: 8+ Dedicated Cores, 16GB+ RAM. Target: 10,000+ entities at < 50ms per tick.
- **`CLASS_B` (Standard Gaming Desktop)**: 4 Dedicated Cores, 8GB RAM. Target: 2,500 entities at < 40ms per tick.
- **`CLASS_C` (Constrained Edge / CI Runner)**: 2 Cores, 2GB RAM. Target: 500 entities at < 30ms per tick.

> **Known conflict, not resolved here**: `docs/engine/contracts/certification_contract.md` §3 defines
> these classes by a binary AND-rule (`CLASS_B` = ≥4 logical cores **and** ≥8GB RAM) instead of this
> table's core-count-only reading, so a 4-core/<8GB machine is `CLASS_B` by this table but `CLASS_C`
> under the canonical certification contract. See `docs/performance/simq_isolation_overhead.md`'s
> Hardware Class section for a worked example of the discrepancy. Flagged, not fixed, by
> TCK-20260702-OBSISO-ISOLATION-PROOF — pre-existing and out of that ticket's scope.

### 2.3 Named Benchmark Results
- **SimQ mode isolation overhead** (`QUALITY_SCORING_DISABLED=1` vs. in-process vs. broker):
  `docs/performance/simq_isolation_overhead.md`, produced by
  `tests/perf/test_simq_isolation_overhead.py`.

---

## 3. CI Performance Regression Guards

**Correction (2026-08-08, `TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION`):** direct grep for
real usage of `src/perf/regression_gate.py`'s `PerfRegressionGate`/`PerfBaseline`/`PerfResult`
classes found **zero real consumers** anywhere in `tests/`/`src/` — the only 2 hits are a skill-doc
text-content check and a code comment, never an actual instantiation. The mechanism §3.1-3.3 below
describes (p50/p95/p99 threshold percentages, `UnacceptableRegressionError`) does not match what
`tests/perf/test_perf_regression_baseline.py` actually runs today: a simpler check comparing
`avg_tick_compute_ms` against `max(5.0, baseline_avg * 1.25)`, reading the committed baseline JSON
directly as a dict, never going through those dataclasses. This section is retained as-written
(a larger correction is out of this ticket's own scope — see the ticket for what it did and didn't
touch) but should not be trusted as an accurate description of the currently-live CI check; treat
`tests/perf/test_perf_regression_baseline.py`'s own source as authoritative until a dedicated
doc-accuracy ticket reconciles this section with reality.

The automated Continuous Integration (CI) pipeline enforces strict regression checks via the `PerfRegressionGate` harness.

### 3.1 Compute Latency Thresholds
When executing standard scenarios (e.g., `MOVEMENT_STRESS_100_ACTORS` or `COMBAT_ARENA_STRESS`), the CI gate compares runtime tick latency against the established baseline.
- **p50 (Median) Latency**: Must not exceed baseline by more than **5.0%**.
- **p95 Latency**: Must not exceed baseline by more than **10.0%**.
- **p99 Latency**: Must not exceed baseline by more than **15.0%**.

### 3.2 Memory Stability and RSS Containment
- **RSS Delta Bound**: Total memory footprint (Resident Set Size) delta between tick 100 and tick 1,000 must not exceed **15.0%** of the starting baseline.
- **GC Allocation Rate**: The total number of garbage collection sweeps must remain stable, demonstrating that high-frequency singletons (e.g., `EMPTY_ENTITY_UPDATE`) successfully prevent generation 1 and 2 heap fragmentation.

### 3.3 CI Execution Rules
- Any commit that exceeds the compute latency or memory delta thresholds fails the CI build instantly with an `UnacceptableRegressionError`.
- If an intentional architectural change increases baseline costs, the commit author must provide a formal "Divergence Rationale" and execute a baseline re-calibration.

---

## 4. Baseline Calibration and Promotion Procedures

When simulation complexity increases (e.g., introducing a new subsystem or expanding map scale) or hardware target specifications change, the performance baselines must be re-calibrated.

### Step-by-Step Calibration Instructions

1. **Isolate the Test Environment**:
   Ensure no background CPU-intensive processes or heavy disk I/O operations are active on the test machine.
   ```bash
   # Pin execution to isolated CPU cores if available
   export PYTHONHASHSEED=42
   export SIMULATION_SCALE=1000
   ```

2. **Execute Baseline Generation Harness**:
   Run the performance regression gate script with the `--generate-baseline` flag. This executes 5,000 ticks across all standard scenarios and outputs clean empirical JSON baselines into `data/baselines/`.
   ```bash
   python3 -m tests.integration.optimization.test_perf_regression_gate --generate-baseline
   ```

3. **Verify Baseline Parity**:
   Run the verification integration suite to prove the newly generated baseline maintains bit-identical state hash parity against reference runs.
   ```bash
   pytest tests/unit/perf/test_perf_regression_gate.py
   ```

4. **Commit and Promote**:
   Commit the newly generated JSON baseline files and update the baseline revision timestamp in `docs/engine/performance_contract.md`.
   ```bash
   git add data/baselines/*.json
   git commit -m "CHORE: Re-calibrate performance baselines for Class B hardware targets"
   ```

---

## 5. SimQ Corpus World Baselines (`TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION`)

Prior to 2026-08-08, all committed baselines (`tests/perf/baselines/*.json`) covered only
synthetic scenarios (`combat_10`, `idle_100`, `mixed_200`, `movement_100`, `resource_100`,
`strategic_100`, via `src/perf/scenarios.py`'s raw `State` builders) — none of the real, authored
SimQ world corpus (`data/worlds/`) had ever been perf-measured.

`tools/bench_corpus_world.py --world {name} [--commit]` benchmarks a real corpus world: reuses
`tools/calibrate_simq.py::_load_world_state()` to build the same real, `WorldCompiler`-compiled
`AuthoritativeState` SimQ calibration uses (no synthetic content, no separate authoring), then runs
`BenchHarness(PERF_PROFILES["PERF_512MB_LOCAL"]).run_benchmark(...)` — a genuinely separate,
dedicated benchmark execution (NOT a free byproduct of a calibration run — `BenchHarness` runs its
own warmup+sample tick loop). Writes the same raw-dict JSON shape as the existing baselines
(`avg_tick_compute_ms`, `tick_ms{}`, `mem_rss_mb{}`, `phase_breakdown{}`), so
`tests/perf/test_perf_regression_baseline.py`'s own real, live comparison logic applies unchanged
— committed baselines are added as new `(scenario_id, builder_fn, kwargs)` rows in that file's own
`parametrize` list.

**Coverage so far**: `simq_corpus_frontier_extended` (59 entities), `simq_corpus_frontier_marches`
(62 entities), `simq_corpus_crowded_frontier` (38 entities) — the corpus's largest 3 worlds by
entity count at the time this ticket ran. Extending coverage to the remaining corpus worlds, or to
`TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION`'s own new large world once it exists, is a
natural follow-up using the same `tools/bench_corpus_world.py --commit` command — not automated in
this ticket.
