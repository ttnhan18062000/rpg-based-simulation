---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260412-STRATEGY-IMPLEMENTATION
artifact_type: test_plan
tags: [strategy, implementation]
---

# Test Plan - TCK-20260412-STRATEGY-IMPLEMENTATION

## Target Areas
- `StrategicState` lifecycle (creation, snapshotting, serialization).
- Project continuity over multi-tick scenarios.
- Cognition graph export structure and stability.
- End-to-end CLI headless verification.

## Verification Steps

### 1. Milestone 0-2 (Foundation)
- `pytest tests/integration/strategy/test_strategic_determinism.py`
- Verify that same seed produces identical strategic state snapshots.

### 2. Milestone 3-5 (Scenarios)
- `pytest tests/e2e/test_strategic_scenarios.py`
- `pytest tests/e2e/test_strategic_reprioritization.py`
- Verify: Leads are followed, allies are recruited, and "Near Death" causes a strategic pivot.

### 3. Milestone 6 (Observation)
- Run headless CLI and check `cognition_graph.json` output.
- Assert nodes for `projects` and `directives` exist.

### 4. Milestone 7 (Full Regression)
- `pytest tests/e2e/test_strategic_regression.py`
- Verify 100% pass on all 4 continuity tests.

## Criteria for Success
- No regression in tactical combat performance.
- Entities demonstrate persistent, explainable behavior over 50+ ticks.
- 100% pass rate on all strategic tests.
