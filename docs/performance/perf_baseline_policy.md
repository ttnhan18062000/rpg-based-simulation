---
status: active
layer: performance
authority: P1
audience: developer
---

# Authoritative V2 Engine Performance Baseline Policy

## 1. Purpose and Scope

This document establishes the official engineering policy for performance baseline calibration, regression gating, and CI benchmarking across the V2 RPG simulation engine. All commits must pass these automated performance gates to prevent performance degradation and memory bloat.

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

---

## 3. CI Performance Regression Guards

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
   pytest tests/integration/optimization/test_perf_regression_gate.py
   ```

4. **Commit and Promote**:
   Commit the newly generated JSON baseline files and update the baseline revision timestamp in `docs/engine/performance_contract.md`.
   ```bash
   git add data/baselines/*.json
   git commit -m "CHORE: Re-calibrate V2 performance baselines for Class B hardware targets"
   ```
