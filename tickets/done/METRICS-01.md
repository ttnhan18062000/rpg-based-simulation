---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: METRICS-01
phase: done
date: unknown
tags: [metrics]
---

# Ticket METRICS-01: Grafana Dashboard & Metrics Overhaul

## Summary
Implement a comprehensive monitoring system for the RPG simulation, providing both "World Pulse" insights (RPG stats, economy) and "Admin Diagnostics" (exceptions, performance profiling).

## Motivation
- **Visibility**: The current dashboard is too basic and doesn't show the depth of the simulation (classes, gold, etc.).
- **Debugging**: Admins need "under the hood" metrics to identify logic bugs and performance bottlenecks without reading logs.
- **Customization**: Users need "preset views" to easily toggle between different simulation perspectives.

## Features

### F1: Simulation Depth Metrics
- Implement `sim_faction_population`, `sim_entity_level_distribution`, `sim_hero_class_total`.
- Implement economic metrics: `sim_gold_circulation_total`, `sim_shop_transactions_total`.
- Implement town health: `sim_building_durability_percent`.

### F2: Admin & Diagnostic Metrics
- Implement error tracking: `sim_errors_total`, `sim_invalid_actions_total`.
- Implement detailed profiling: `sim_tick_phase_duration_seconds`.
- Track infra health: `sim_worker_health`, `sim_redis_latency_seconds`.

### F3: Information-Rich Dashboards
- Redesign `grafana/dashboards/simulation.json` with new panels.
- Implement "Preset View" variables for easy switching.

## Implementation Status
- [/] Phase 1: Design Specification ([2026-03-20-grafana-metrics-overhaul-design.md](file:///d:/Projects/rpg-based-simulation/docs/superpowers/specs/2026-03-20-grafana-metrics-overhaul-design.md))
- [ ] Phase 2: Metric Implementation in `src/utils/metrics.py`
- [ ] Phase 3: World Loop & Combat Instrumentation
- [ ] Phase 4: Grafana Dashboard JSON Update
- [ ] Phase 5: Verification & Customization Presets

## Labels
`metrics`, `observability`, `admin-tools`, `grafana`, `inprogress`

**Tier:** standard
**Type:** chore
**Priority:** P1
