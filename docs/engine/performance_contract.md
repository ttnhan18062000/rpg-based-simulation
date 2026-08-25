---
status: active
layer: engine
authority: P1
audience: developer
---

# Engine Performance Contract

## 1. Purpose
This contract defines how performance (TPS, Tick Cost) must be measured, reported, and certified. It ensures that performance claims are honest, scoped, and reproducible.

## 2. Primary Metrics

### 2.1 Tick Cost (ms)
- **Definition**: The total wall-clock time spent inside `Kernel.tick_once()`.
- **Measurement**: Derived from `time.perf_counter_ns()` with microsecond resolution.
- **Reporting**: Reported per-tick in `PressureSignals`.

### 2.2 TPS (Ticks Per Second)
- **Definition**: The sustainable number of ticks the engine can process per second.
- **Measurement**: `1000 / avg_tick_compute_ms`.

### 2.3 Phase Breakdown
The engine must report the cost of each authoritative phase separately:
- `INIT`: Context setup and policy.
- `SCHEDULING`: Work selection.
- `COLLECTION`: Execution (local or concurrent).
- `RESOLUTION`: Applying results to state.
- `CLEANUP`: Metrics and finalization.
- `ADVANCEMENT`: Signal recording.

## 3. Benchmarking Rules

### 3.1 Scoped Claims
Performance claims are ONLY valid when combined with:
- **Runtime Profile**: (e.g. `standard_gaming`)
- **Hardware Class**: (e.g. `Class_B`)
- **Scenario**: (e.g. `movement` parameterized by `entity_count=100` — see `src/perf/scenarios.py`'s
  `SCENARIO_BUILDERS`; the previously-cited `MOVEMENT_STRESS_100_ACTORS` name is not a real wired
  scenario anywhere in `src/perf/scenarios.py` or `tests/`, corrected 2026-08-22 per
  `TCK-20260822-SCAN-POLICY-DOC-FIX`)
- **Execution Mode**: (LOCAL vs CONCURRENT)
- **RuntimeMode**: (NORMAL — see §7 Adaptive Phase Budget Governor for the ladder; a claim
  measured while the Governor left NORMAL is not a valid baseline claim without stating so)

### 3.2 measurement Protocol
- **Warmup**: Benchmarks must run a minimum of 100 warmup ticks before recording starts.
- **Sampling**: A minimum of 1000 ticks must be sampled for a baseline.
- **Environmental Stability**: Benchmarks must run on isolated cores if possible to minimize noise.

## 4. Optimization Laws

### 4.1 Parity Invariant
Optimization MUST NOT change the semantic outcome of an official RPG slice. Any optimization that causes a hash mismatch in the `AuthoritativeState` vs the baseline is a failure.

### 4.2 Bounded Overhead
Timing instrumentation itself must stay bounded (< 1% of total tick time).

## 5. Regression Enforcement
- Any commit that increases `avg_tick_compute_ms` by > 5% on a stable scenario must be flagged.
- Significant regressions require a "Divergence Reason" in the performance log.

## 6. Memory Management & Pooling
- **Differential Caching**: AuthoritativeState must utilize differential caching for read-only views. Reconstruction of views should be O(Dirty) rather than O(N).
- **Singleton Singletons**: High-frequency no-op updates (e.g. EMPTY_ENTITY_UPDATE) must be implemented as singletons to minimize object allocation spikes.
- **Deep-Freeze Caching**: Shared world components that are immutable for the duration of a simulation tick should be cached in their "frozen" state to avoid redundant recursive traversals.
- **Incremental GC**: The Kernel must utilize frame-pacing idle windows to perform shallow garbage collection (`gc.collect(0)`). This prevents the accumulation of short-lived objects into expensive generation 1/2 collections, smoothing the latency p95/p99 envelope.

## 7. Adaptive Phase Budget Governor

### 7.1 Granular Sub-Phase Budgets
Under system pressure or high work debt, the engine must not rely solely on macro concurrency limits. The `PhaseBudgetGovernor` monitors real-time sub-phase compute costs (e.g., Locomotion vs. Strategic Intelligence) and dynamically emits granular `PhaseBudgets`.

### 7.2 Sub-Phase Budget Parameters
- `candidate_budget`: Caps the maximum number of entities evaluated per tick during movement and action routing.
- `movement_budget`: Caps the number of spatial pathfinding operations per tick.
- `strategic_budget`: Caps the number of high-cost cognition cycles per tick.
- `scan_policy`: Governs candidate evaluation rigor (`FULL`, `THROTTLED`, `EXACT_DIRTY`). Under heavy pressure, systems bypass O(N) full scans and evaluate ONLY entities marked in the authoritative `DirtySet`.
- `background_sweep_interval`: Modulates the cadence of background entity sweeps (e.g., from every tick up to every 10 ticks under `SURVIVAL` mode).
- `compaction_level`: Modulates state update compaction (`NORMAL` vs `AGGRESSIVE`) to aggressively prune redundant or no-op updates before authoritative application.

