---
ticket_id: TCK-20260619-E31-SCENARIO-RUNTIME
phase: test_plan
date: 2026-06-20
---

# Test Plan: Scenario Runtime Service

## Integration Tests (new file: tests/integration/scenarios/test_scenario_runtime_service.py)

### test_scenario_reaches_objective_met
- Configure victory condition `{kind: "tick_limit", value: 50}`; run via service; assert OBJECTIVE_MET state

### test_scenario_pause_resume_identical_outcome
- Pause at tick 25, resume; assert same subsequent events as uninterrupted run

### test_checkpoint_restore_determinism
- Checkpoint at tick 25, restore to fresh service, run to tick 50; assert identical events to non-checkpoint run

### test_stall_detector_fires_on_no_events
- Run with all entities frozen (no movement); assert STALLED after N ticks

## API Tests (new file: tests/api/test_scenario_runtime_api.py)
### test_status_endpoint_returns_live_state
- GET status mid-run; assert `tick_count` and `alive_entity_count` non-zero

## Validation
```bash
pytest tests/integration/scenarios/test_scenario_runtime_service.py -x -v -m slow
pytest tests/api/test_scenario_runtime_api.py -x -v
```
