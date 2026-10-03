---
content_type: doc
status: historical
layer: observability
authority: P2
audience: agent
tags: [metrics]
---

# Design Spec: Grafana Dashboard & Metrics Overhaul

**Date:** 2026-03-20
**Author:** Antigravity (AI Assistant)
**Status:** DRAFT (Approved by User)

## 1. Goal Description

Revise the simulation's monitoring infrastructure to provide "information-rich" insights and "under the hood" diagnostic capabilities. The goal is to move beyond basic TPS/Entity counts and provide a deep, real-time look into the world's RPG systems, economy, and technical health.

### Success Criteria:
- Unified "Simulation Pulse" dashboard for high-level world monitoring.
- Dedicated "Admin Diagnostic" dashboard with error tracking and performance profiling.
- High-level "Preset Views" to easily switch focus (e.g., Faction War, Economy, Tech).

---

## 2. Proposed Metrics

### 2.1 Simulation Depth Metrics
These metrics capture the "life" of the simulation.

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `sim_faction_population` | Gauge | `faction` | Current headcount per faction (Hero Guild, Goblins, etc.) |
| `sim_entity_level_distribution` | Gauge | `kind`, `level` | Number of entities at each level bracket |
| `sim_hero_class_total` | Gauge | `class`, `tier` | Total heroes in each class (Warrior, Mage, etc.) and tier |
| `sim_gold_circulation_total` | Gauge | `faction` | Total gold held by all entities in a faction |
| `sim_building_durability_percent` | Gauge | `building_id` | Health of town infrastructure (0-100%) |
| `sim_quest_status_total` | Counter | `type`, `status` | Tracking GATHER/HUNT/EXPLORE success/failure rates |
| `sim_items_crafted_total` | Counter | `item_id`, `tier` | Tracking blacksmith activity and gear quality |
| `sim_world_difficulty_mult` | Gauge | - | Current global stat multiplier based on world age |
| `sim_calamity_active` | Gauge | `region_id` | 1 if a world boss is active, 0 otherwise |

### 2.2 Technical (Admin) Metrics
These metrics track "under the hood" health and bugs.

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `sim_errors_total` | Counter | `type`, `module` | Caught exceptions in world loop, AI, or networking |
| `sim_invalid_actions_total` | Counter | `action_type`, `reason` | Actions proposed by AI that failed validation |
| `sim_state_transition_failures` | Counter | `from_state`, `to_state` | Failures in AI state logic transitions |
| `sim_tick_phase_duration_seconds` | Histogram | `phase` | Detailed (sub-millisecond) profiling of Scheduler, AI, Combat, Physics, and Serialization phases |
| `sim_worker_health` | Gauge | `worker_id` | Health/Status of distributed AI worker processes |
| `sim_redis_latency_seconds` | Histogram | `op` | Latency of state delta publishing and snapshot storage |

---

## 3. Dashboard Design (Grafana)

### 3.1 Preset Views (Variables)
A top-level variable `$view_preset` will control panel visibility:
- **General**: Summary stats (TPS, Entities, Ticks).
- **Faction War**: Headcount, survival ratios, Calamity health.
- **Economic Focus**: Gold distribution, trade volume, building health.
- **Hero Progress**: Level brackets, class distribution, monuments.
- **Deep Tech (Admin)**: Errors, Profiling, Worker latency.

### 3.2 Layout (Simulation Overview)
- **Top Row**: TPS (Gauge), Active Entities (Graph), World Age (Stat), Difficulty Mult (Stat).
- **Row: Faction Dynamics**: Headcount by Faction (Stacked Graph), Deaths vs Spawns per Faction (Rate).
- **Row: RPG State**: Class distribution (Pie Chart), Level brackets (Bar Gauge), Average Fame (Stat).
- **Row: Economy & Town**: Building Durability (Polystat), Gold circulation (Gauge), Shop transactions (Rate).

### 3.3 Layout (Admin & Health)
- **Row: Stability**: Errors/m (Graph), Unhandled Exceptions (Table), Uptime (Stat).
- **Row: Performance**: Phase Breakdown (Stacked Area), Tick duration variance (Histogram).
- **Row: Pipeline**: Action Queue Depth (Graph), Worker Dispatch Delay (Heatmap).

---

## 4. Implementation Strategy

1.  **Metric Definition**: Update `src/utils/metrics.py` with the new Counter/Gauge/Histogram definitions.
2.  **Instrumentation**:
    - Add metric updates in `WorldLoop._update_world_evolution()` for world-wide stats.
    - Instrument `CombatAction.apply()` for death and faction stats.
    - Instrument `ActionSystem` and `AI states` for error/validation tracking.
    - Use `SIM_TICK_DURATION` precisely around each loop phase.
3.  **Grafana Provisioning**: Update `grafana/dashboards/simulation.json` with the new panel definitions and variables.
4.  **Verification**: Run the simulation and verify metrics show up in Prometheus targets (`:8000/metrics`) and Grafana panels.
