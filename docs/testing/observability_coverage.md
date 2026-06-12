---
status: historical
layer: testing
authority: P2
audience: developer
---

# Phases 19–28 — Observability & Behavior Profiling Test Coverage

This document outlines the detailed test coverage audit matrix for the Observability & Behavior Profiling module (Phases 19 through 28). It maps each feature requirements area to its respective test files and validates that behavior metrics are decoupled from the simulation hot path under budget constraints.

## Decoupling & Queue Core (Phases 19–21)

- **Observability Safety Boundary & Architectural Isolation**:
  - Validates that behavior metrics are isolated from performance-critical memory records and run asynchronously.
  - Test File: [test_phase19_observability_boundaries.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/architecture/test_phase19_observability_boundaries.py)
- **Feature Flags & Global Controls**:
  - Toggles behavior logging systems safely across engine configurations.
  - Test File: [test_phase19_observability_feature_flags.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/config/test_phase19_observability_feature_flags.py)
- **Non-Blocking Bounded Queue**:
  - Verifies event buffering, lockless multi-producer single-consumer emission, and drop safety under backpressure.
  - Test File: [test_phase21_bounded_observability_queue.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/stream/test_phase21_bounded_observability_queue.py)
- **QueueDrainWorker Singleton Guard** _(added 2026-06-11)_:
  - Verifies that `get_or_start_global_worker()` returns the same worker on repeated calls and that at most one worker drains the global queue at a time. Covers dead-worker replacement and `get_active_global_worker_count()`.
  - Test File: [test_queue_worker_singleton.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/test_queue_worker_singleton.py)
  - Parity: INFRA-179

## Normalization, Worker & Timeline Ingestion (Phases 22–24)

- **Behavior Event Schemas & Normalization**:
  - Tests event validation, serialization parity, and domain tuple standardizers.
  - Test Files: 
    - [test_phase22_behavior_event_model.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase22_behavior_event_model.py)
    - [test_phase22_behavior_event_normalizer.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase22_behavior_event_normalizer.py)
- **Asynchronous Workers**:
  - Tests ingestion processing from stream and JSONL log sources without stalling main threads.
  - Test Files: 
    - [test_phase22_behavior_worker_from_stream.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/observability/test_phase22_behavior_worker_from_stream.py)
    - [test_phase22_behavior_worker_from_jsonl.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/observability/test_phase22_behavior_worker_from_jsonl.py)
- **Chronological Timeline & Episode Models**:
  - Tests timeline reconstructions, chronological ordering, and episode boundary splits.
  - Test Files:
    - [test_phase23_behavior_episode_model.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase23_behavior_episode_model.py)
    - [test_phase23_behavior_timeline_store.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase23_behavior_timeline_store.py)
    - [test_phase23_behavior_timeline_episode_artifacts.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/observability/test_phase23_behavior_timeline_episode_artifacts.py)
- **Semantic Metric Aggregators & Windows**:
  - Computes sliding window behavior metrics (frequency, entropy, diversity) asynchronously.
  - Test Files:
    - [test_phase24_behavior_metric_window.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase24_behavior_metric_window.py)
    - [test_phase24_behavior_metrics_aggregator.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase24_behavior_metrics_aggregator.py)
    - [test_phase24_behavior_metric_artifacts.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/observability/test_phase24_behavior_metric_artifacts.py)

## Advanced Pattern Detection & Scorecards (Phases 25–26)

- **Loop & Stagnation Detection**:
  - Verifies repeated failure loop, successful adaptation, and omniscience detectors.
  - Test Files:
    - [test_phase25_behavior_pattern_detectors.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase25_behavior_pattern_detectors.py)
    - [test_phase25_behavior_insight_generator.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase25_behavior_insight_generator.py)
    - [test_phase25_postrun_behavior_analysis.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/observability/test_phase25_postrun_behavior_analysis.py)
- **Scorecards, Cohorts & Comparison Verdicts**:
  - Tests individual scorecard compiling, demographic cohort divisions, and run comparisons.
  - **Delta Rule**: Explicitly validates that event volume increases do not trigger a false-positive verdict of behavior improvement.
  - Test Files:
    - [test_phase26_entity_behavior_scorecard.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase26_entity_behavior_scorecard.py)
    - [test_phase26_run_behavior_scorecard.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase26_run_behavior_scorecard.py)
    - [test_phase26_run_behavior_comparison.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/behavior/test_phase26_run_behavior_comparison.py)
    - [test_phase26_behavior_scorecard_artifacts.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/observability/test_phase26_behavior_scorecard_artifacts.py)

## Storage, API, Budgets & Degradation (Phases 27–28)

- **Query Warehouses & API Paths**:
  - Validates SQLite/ClickHouse adapter queries, FastAPI behavior routing, and schema path compliance.
  - Test Files:
    - [test_phase27_behavior_warehouse_schema.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/warehouse/test_phase27_behavior_warehouse_schema.py)
    - [test_phase27_behavior_artifact_paths.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/reporting/test_phase27_behavior_artifact_paths.py)
    - [test_phase27_behavior_dataset_builder.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/observability/test_phase27_behavior_dataset_builder.py)
- **Observability Budget & Graceful Throttling**:
  - Tests upper budget bounds (TPS impact < 2%, memory caps), sampling rules, and self-healing degradation.
  - Test Files:
    - [test_phase28_observability_budget_profile.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/budget/test_phase28_observability_budget_profile.py)
    - [test_phase28_observability_degradation.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/observability/test_phase28_observability_degradation.py)
- **Rollout Parity & Release Gate Verification**:
  - Certifies release readiness by ensuring zero loss of determinism parity when logging.
  - Test File: [test_phase28_observability_determinism.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/observability/test_phase28_observability_determinism.py)

## Worker Lifecycle & Leak Regression (added 2026-06-11)

These tests and infrastructure guard against observability worker thread accumulation across the test suite — the root cause of the historical MemoryError / Fatal abort crashes on full-suite runs.

- **Memory Probe Helpers**:
  - `snapshot_start/end`, `count_drain_workers`, `count_event_recorders`, `assert_no_worker_leak` — importable from `tests/tools/memory_probe.py` for targeted per-test assertions.
  - Test File: [test_memory_probe.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/test_memory_probe.py)
- **Session-Level Leak Sentinel**:
  - `_observability_worker_thread_sentinel` autouse fixture in `tests/conftest.py` counts `QueueDrainWorker` threads at session start and end; `pytest.fail()` if count grows. Catches any future test that starts a worker without teardown.
  - Location: `tests/conftest.py`
- **Standalone Diagnostic Script**:
  - `scripts/memory_probe.py` — run with `--flamegraph` to produce an HTML memray allocation flamegraph, or default mode for RSS + tracemalloc report. `--simulate-leak` demonstrates the accumulation pattern.
