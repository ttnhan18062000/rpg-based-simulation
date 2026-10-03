---
content_type: doc
status: historical
layer: observability
authority: P2
audience: agent
tags: [metrics]
---

# Implementation Plan - Grafana & Metrics Overhaul (METRICS-01)

## Goal Description
Implement a comprehensive monitoring system for the RPG simulation, providing both "World Pulse" insights and "Admin Diagnostics," with high-level customization via preset views.

## User Review Required
> [!IMPORTANT]
> The implementation involves instrumenting core systems (`WorldLoop`, `CombatAction`, etc.). While this adds minimal overhead, it is a broad set of changes.

## Proposed Changes

### Metrics Definition
#### [MODIFY] [metrics.py](file:///d:/Projects/rpg-based-simulation/src/utils/metrics.py)
Define all new Prometheus counters, gauges, and histograms:
- `sim_faction_population`
- `sim_entity_level_distribution`
- `sim_hero_class_total`
- `sim_gold_circulation_total`
- `sim_building_durability_percent`
- `sim_errors_total`
- `sim_invalid_actions_total`
- `sim_tick_phase_duration_seconds` (expanded labels)

### System Instrumentation
#### [MODIFY] [world_loop.py](file:///d:/Projects/rpg-based-simulation/src/engine/world_loop.py)
- Instrument `_update_world_evolution` to collect population, gold, and building health stats once per tick.
- Wrap core loop phases with `sim_tick_phase_duration_seconds` timers.
- Add error handling blocks to increment `sim_errors_total`.

#### [MODIFY] [combat.py](file:///d:/Projects/rpg-based-simulation/src/actions/combat.py)
- Record faction deaths and kill rates within `CombatAction.apply()`.
- Track skill usage distribution.

#### [MODIFY] [buildings.py](file:///d:/Projects/rpg-based-simulation/src/core/buildings.py) & [buildings_state.py]
- Record building repair and sabotage events.
- Track shop transaction volume (buys/sells).

### Dashboard & Customization
#### [MODIFY] [simulation.json](file:///d:/Projects/rpg-based-simulation/grafana/dashboards/simulation.json)
- Full redesign of the dashboard layout.
- Implementation of the `$view_preset` variable for High-level/Combat/Economy/Admin views.
- Configuration of Faction/Entity/Region filters.

## Verification Plan
### Automated Tests
- Run `pytest tests/integration/test_world_progression.py` to ensure instrumentation doesn't break world ticks.
- Verify metrics endpoint: `curl http://localhost:8000/metrics | grep sim_`.

### Manual Verification
- **Grafana**: Open the dashboard and verify panels populate correctly.
- **Presets**: Test switching between `$view_preset` values to confirm correct panels are shown/hidden.
- **Admin**: Trigger a simulated error (or check logs) and verify `sim_errors_total` increments.
