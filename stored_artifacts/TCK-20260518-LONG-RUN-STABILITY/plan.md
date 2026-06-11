---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260518-LONG-RUN-STABILITY
artifact_type: plan
tags: [long, run, stability]
---

# Plan: Long-Run Stability Certification (Milestone 18)

## 1. Architectural Design: `LongRunStabilityHarness`
We will create `src/perf/long_run_harness.py` containing `LongRunStabilityHarness`.

### Responsibilities:
1. **Scenario Bootstrapping**: Generate a 1,000-entity `metropolis` or `mixed` state using `scenarios.py`.
2. **Mode Configuration**:
   - `PURE`: Disables governor degradation, forcing full execution of all phases to test raw engine stability.
   - `RUNTIME`: Enables `PhaseBudgetGovernor` and adaptive budgets.
3. **Continuous Sampling**: Over 5,000 ticks, sample every N ticks (e.g. every 50 ticks):
   - Memory RSS (via `psutil.Process(os.getpid()).memory_info().rss`).
   - GC collection stats (`gc.get_stats()`).
   - Tick compute p50/p95/p99 latency (ms).
   - Cache sizes: `MovementPlanCache._cache`, `ReadModelCache._entity_dtos`, and spatial index entries.
   - Candidate counts and work debt.
4. **Stability Invariant Enforcement**:
   - **No Unbounded Memory**: Maximum RSS must not exceed 2.0x of baseline RSS after warmup.
   - **No Uncontrolled Latency Drift**: Final 500 ticks p95 compute ms must not exceed 1.5x of the first 500 ticks p95 compute ms.
   - **No Monotonic Cache Growth**: Cache sizes must plateau or remain strictly within configured capacity limits.
   - **Absolute Determinism**: Two consecutive runs with identical seeds must yield identical `CanonicalStateHasher.get_hash(state)` values.

## 2. Deliverables
1. `src/perf/long_run_harness.py`: The long-run certification runner.
2. `tests/certification/test_cert_long_run_stability.py`: Pytest suite executing the long-run certification across pure and runtime modes, asserting invariant passes.
3. `reports/certification/long_run_stability.json`: The generated long-run evidence report.

## 3. Verification Plan
- Execute `pytest -s tests/certification/test_cert_long_run_stability.py` to verify full 5,000-tick stability and determinism.
