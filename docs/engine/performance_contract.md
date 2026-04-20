# V2 Engine Performance Contract

## 1. Purpose
This contract defines how performance (TPS, Tick Cost) must be measured, reported, and certified in the V2 engine. It ensures that performance claims are honest, scoped, and reproducible.

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
- **Scenario**: (e.g. `MOVEMENT_STRESS_100_ACTORS`)
- **Execution Mode**: (LOCAL vs CONCURRENT)

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
