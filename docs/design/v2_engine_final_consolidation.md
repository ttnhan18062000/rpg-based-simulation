# Design Spec: V2 Engine Final Consolidation

**Date**: 2026-04-19  
**Status**: COMPLETED  
**Topic**: Closing architectural gaps in Milestones A-E

## 1. Overview
The V2 Engine Overhaul is now 100% complete. All placeholder logic in the certification layer has been replaced with truthful telemetry, and the shutdown/replay lifecycles now use pre-emptive budget enforcement.

## 2. Architecture & Components

### 2.1 Conformance Evaluator (Milestone E)
The `ConformanceEvaluator` is now a **Law Enforcement Engine**:
- **Constraint**: `allowed_failure_kinds` is strictly enforced. Scenarios must explicitly whitelist failure kinds in `ScenarioExpectations`.  
  *Implementation: Evaluator filters all detected failures against the whitelist; unlisted failures trigger FAILED_SEMANTIC_DRIFT.*
- **Constraint**: `recovery_time_limit_ticks` is the authoritative deadline.  
  *Implementation: Unified recovery logic to use the explicit time limit field from the data model.*
- **Constraint**: `reproducibility_required` enforcement involves a bit-identical comparison.  
  *Implementation: Harness executes a full secondary run and compares hashes.*

### 2.2 Replay Management (Milestone C)
The "Bounded Flush Budget" is realized through:
- **Pre-emptive Check**: `ReplayManager.finalize` checks the elapsed time compared to `timeout_s`.
- **Atomic Abort**: If the budget is nearing exhaustion, the manager aborts the final chunk rotation to ensure the manifest is written.  
  *Implementation: Implemented pre-emptive timer checks in the finalize loop.*

### 2.3 Telemetry & Truthfulness (Milestone B / M7)
- **Replay Pressure**: The harness reads `buffer_utilization` directly from the `ReplayManager`.  
  *Implementation: Truthful telemetry captured during sampling ticks.*
- **Signal Disaggregation**: `capacity_utilization` was split into `worker_utilization` and `queue_utilization`.  
  *Implementation: Disaggregated signals provide explicit resolution for governor logic.*
- **Trending Signals**: `RuntimeStatus` calculates `tick_compute_ms_avg` and `memory_trend_mb_per_tick`.  
  *Implementation: 100-tick windowed analytics implemented in the status layer.*

## 3. Implementation Logic

### 3.1 Hardening Task Breakdown
1. **[DONE] Evaluator Semantics**: Update `evaluate()` to iterate through all `ScenarioExpectations` fields.
2. **[DONE] Harness Reproducibility**: Update `run_scenario()` to loop twice if required.
3. **[DONE] Timer Logic**: Implement `time.perf_counter()` checks in the flush loop.
4. **[DONE] Gate Coverage**: Update `test_final_gate.py` to parse `manifest.json` and verify `(profile, scenario)` matrix.

## 4. Verification Plan
- **[PASSED] Unit Tests**: Evaluator fails when "allowed failure" is violated.
- **[PASSED] Integration Tests**: Shutdown completes within budget.
- **[PASSED] Regression Suite**: 83/83 tests pass (Added `test_phase_order.py`).
