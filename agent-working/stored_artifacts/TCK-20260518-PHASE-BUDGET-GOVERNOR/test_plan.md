---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260518-PHASE-BUDGET-GOVERNOR
artifact_type: test_plan
tags: [phase, budget, governor]
---

# Test Plan: Adaptive Phase Budget Governor

## Automated Tests

### 1. Unit Tests (`tests/unit/optimization/test_phase_budget_governor.py`)
- **Test Budget Throttling**: Provide `PressureSignals` with high `tick_compute_ms` and elevated phase p95 costs (e.g. `movement: 20ms`, `strategic: 25ms`). Assert that `PhaseBudgetGovernor.evaluate` reduces `movement_budget` and `strategic_budget` and increases `background_sweep_interval`.
- **Test Scan Policy Transition**: Assert transition from `ScanPolicy.FULL` to `ScanPolicy.THROTTLED` and `ScanPolicy.EXACT_DIRTY` under extreme pressure.
- **Test Candidate Filtering**: Call `StrategicWorkQueue.build` with `budget=10` and `sweep_interval=5`. Assert urgent Tier 1-6 entities are included first, and Tier 7 is properly spaced out.
- **Test Recovery**: Provide normalized pressure signals across a recovery window and verify budgets return to NORMAL baselines.

### 2. Integration Tests (`tests/integration/optimization/test_degraded_mode_correctness.py`)
- **Test Degraded Mode Correctness**:
  - Setup a scenario with 100 entities in combat/starvation and resource transactions.
  - Force governor into DEGRADED or SURVIVAL mode with extremely tight budgets (`movement_budget=5`, `strategic_budget=5`).
  - Run for 50 ticks.
  - Assert zero dropped correctness events: entities with zero health transition to dead/corpse, resource transactions complete, and inventory constraints hold.
  - Verify deterministic execution across two identical runs.

## Execution
Run tests with pytest:
```bash
pytest tests/unit/optimization/test_phase_budget_governor.py
pytest tests/integration/optimization/test_degraded_mode_correctness.py
```
