---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-OBSERVATORY-INTEGRATION
artifact_type: test_plan
tags: [lab, observatory, integration]
---

# Test Plan - Milestone 79 Observatory Integration

## Objective
Establish a rigorous suite of integration tests verifying the full flow from dynamic compilation -> simulation ticking -> Observatory reporting -> lab summary aggregation.

## Test Target
File: `tests/integration/lab/test_lab_observatory_integration.py`

## Test Cases
1. **Successful Single Run Integration**:
   - Compiles a valid `WorldSpec` and ticks it under a lightweight `ExperimentSpec`.
   - Asserts child run contains `simulation_events.jsonl`, `anomalies.json`, `run_report.json`, and `run_report.md`.
   - Asserts the final `lab_summary.json` and `lab_summary.md` are created.
   - Verifies the aggregations (`average_health_score == 100.0`, `critical_count_total == 0`, `top_anomalies` is correct).
2. **Aggregating Sweep Anomalies**:
   - Inject anomalous events or simulate a failing condition (e.g. hard law violation or stuck entity).
   - Verify that the health score degrades accordingly in the summary.
   - Verify `top_anomalies` correctly prioritizes and lists the most frequent rules triggered.
   - Verify `best_run_id` and `worst_run_id` are resolved accurately.
3. **Graceful Handling of Failed/Missing Run Reports**:
   - Simulate a child run failure that aborts execution.
   - Assert overall status changes to `PARTIAL` (if some succeed) or `FAILED` (if all fail).
   - Assert that the summary logs and identifies the failing seed run without crashing the orchestrator.
4. **All Failed Sweep Fail-Safe**:
   - Configure a sweep where all seeds fail immediately (e.g., compile error or runtime exception).
   - Verify that the lab status transitions to `FAILED` and `lab_summary.json` correctly reflects 0 completed runs and 100% failure rate.
