---
status: active
artifact_type: test_plan
ticket_id: TCK-20260619-E21D-SCARCITY-VERIFY
date: 2026-06-20
---

# Test Plan — TCK-20260619-E21D-SCARCITY-VERIFY

## Regression Surface (existing tests that must pass)

- `tests/unit/world/test_resource_ecology.py` — all tests (Group A–D from E21B)
  - `test_depleted_event_emitted_when_last_charge_harvested`
  - `test_regen_increments_charges_per_ecology_interval`
  - `test_recovered_event_emitted_when_depleted_node_regens`
  - `test_regen_capped_at_max_charges`, `test_regen_skipped_*`
- `tests/integration/scenarios/test_phase8_world_emergence_scenarios.py` — all tests (ScarcityModel consumer is touched indirectly)

## New Tests Required (per AC)

### File: `tests/integration/scenarios/test_resource_depletion.py`

#### Test 1: `test_depletion_and_recovery_in_1000_tick_run`
- **Marks**: `@pytest.mark.slow`, `@pytest.mark.integration`
- **Setup**: Minimal world with 1 resource node (`regen_rate_per_tick=1`, `max_charges=2`, `remaining_charges=2`), 1 harvester entity near the node, `ENABLE_ADVENTURE_ROUTING=ON`
- **Approach**: Use kernel (`tick_once()` × 1000), `try/finally kernel.shutdown()`
- **Assert**:
  - At least 1 `RESOURCE_DEPLETED` event in `kernel.state.recent_world_events` at any point, OR captured across ticks
  - At least 1 `RESOURCE_RECOVERED` event across the run
- **Note**: Track events across ticks by accumulating `kernel.state.recent_world_events` each tick (it's a sliding window); OR check that both event categories appear in the final window. Given `max_charges=2` and `regen_rate_per_tick=1`, the ecology fires at tick 200, 400, 600, 800, 1000 — recovery is guaranteed if depletion occurs.

#### Test 2: `test_regional_scarcity_rises_after_depletion`
- **Marks**: no slow mark (pure in-process, no kernel)
- **Setup**: Minimal `AuthoritativeState` with 1 region (`"test_region"`), inject `RESOURCE_DEPLETED` events for that region in `recent_world_events`
- **Approach**: Call `WorldEmergencePhase.execute(state, StateUpdate(), state.recent_world_events)` directly
- **Assert**:
  - `result.scarcity` is non-empty
  - At least one `ResourceScarcitySignal` has `scarcity_level > 0.0`
  - `result.pressures` contains a `RegionalPressure(pressure_kind="resource")` with `intensity > 0.0`

## Scoped Pytest Commands

```bash
# New integration tests
pytest tests/integration/scenarios/test_resource_depletion.py -x -v

# Regression: unit ecology tests
pytest tests/unit/world/test_resource_ecology.py -x -v

# Regression: world emergence integration scenarios
pytest tests/integration/scenarios/test_phase8_world_emergence_scenarios.py -x -v

# Combined (excluding slow)
pytest tests/integration/scenarios/test_resource_depletion.py tests/unit/world/test_resource_ecology.py tests/integration/scenarios/test_phase8_world_emergence_scenarios.py -v -m "not slow"

# Full with slow
pytest tests/integration/scenarios/test_resource_depletion.py tests/unit/world/test_resource_ecology.py -v
```

## Anti-Drift Test Guards

- Test 1 must use `try/finally: kernel.shutdown()` to prevent thread leak (per ticket Implementation Notes)
- Test 2 must NOT call the kernel — pure `WorldEmergencePhase.execute()` call
- Both tests must NOT modify `RegionalPressureModel` or `ScarcityModel` source — read/verify only
- `regen_rate_per_tick=1`, `max_charges=2` ensures depletion + recovery within < 200 ticks of a harvest
