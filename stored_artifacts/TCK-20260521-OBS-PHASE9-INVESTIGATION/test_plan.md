# Phase 9 Verification and Testing Plan

## 1. Testing Strategy

The verification suite for **Phase 9 (Simulation Mining and AI-Assisted Investigation)** ensures that:
1.  **Deterministic Mining**: All outlier detection, pattern clustering, and priority scoring algorithms yield consistent, repeatable, and correct metrics when executed against identical run directories.
2.  **Absolute Non-Interference**: Telemetry mining operations do not inject latency, side-effects, or state changes into the active WorldLoop execution path.
3.  **Data Ingestion Resilience**: Incomplete or corrupted runs are handled gracefully, documented in completeness logs, and do not crash the dataset builder.

---

## 2. Test Specifications

### A. Unit Tests (Mock & In-Memory Isolation)

#### `test_mining_experiment_config.py`
*   Verifies that `MiningExperimentConfig` correctly validates scenarios, tick counts, seeds, and parallel limits.
*   Asserts correct exception raising on invalid configurations.

#### `test_mining_dataset_builder.py`
*   Simulates three mock run output folders containing realistic `simulation_events.jsonl` and `metric_windows.jsonl`.
*   Asserts that `MiningDatasetBuilder` successfully processes the directories, writes standardized Parquet partition tables, and extracts accurate run features.

#### `test_determinism_auditor.py`
*   Mock groups of 5 repeat runs of the same seed.
*   Introduces artificial logical divergence (e.g. mismatched state hashes or event counts at tick 120).
*   Asserts that `DeterminismAuditor` correctly identifies `CONFIRMED_NONDETERMINISM` and pinpoint-identifies tick 120 as the earliest divergence coordinate.

#### `test_pattern_mining_engine.py`
*   Fills a mock DuckDB table with varying anomaly densities across 50 seeds.
*   Asserts that `PatternMiningEngine` correctly identifies outlier seeds, ranks recurring rules, and groups them accurately by gameplay domains.

#### `test_priority_scorer.py`
*   Verifies that `PriorityScorer` ranks P0 correctness anomalies (e.g. hard law violations) higher than P2 balance warnings.
*   Checks custom score multipliers based on frequency and blast radius.

#### `test_agent_output_validator.py`
*   Passes compliant and non-compliant JSON outputs through the `AgentOutputValidator`.
*   Asserts successful parsing of compliant payloads and strict rejection of speculative reports containing missing or invented SQL evidence keys.

---

## 3. Integration Tests (Full Loop)

#### `test_mining_experiment_flow.py`
*   Sets up a minimal test configuration (scenario: `RESOURCE_ECONOMY_10`, seeds: `[1, 2]`, ticks: `100`).
*   Runs the experiment using `MiningExperimentController`.
*   Ingests artifacts, builds the local DuckDB dataset, mines patterns, scores priorities, generates a complete `engineering_backlog.md`, and compiles a compact evidence pack folder.
*   Asserts the presence and integrity of all output manifest and report files.

#### `test_mining_quality_gate.py`
*   Verifies the CI quality gate behavior under three condition profiles:
    *   **Profile 1**: Flawless execution -> `PASS`.
    *   **Profile 2**: Multi-seed sweep with >10% recurring P1 liveness failures -> `WARNING`.
    *   **Profile 3**: Determinism divergency detected -> `FAIL`.

---

## 4. Invariants & Stability Gates

1.  **Zero Tick Pollution**: All mining, feature extraction, and prioritization executions must run strictly offline or post-run. Performance verification assertions will verify that the active simulation tick duration (`clock.tick_duration_ms`) remains completely identical with mining execution.
2.  **RNG Determinism Preservation**: Assert that running a complete mining sweep does not pollute or mutate standard xxhash random number generators. Seed-identical simulations must return exactly identical state hashes before, during, and after mining sweeps.
