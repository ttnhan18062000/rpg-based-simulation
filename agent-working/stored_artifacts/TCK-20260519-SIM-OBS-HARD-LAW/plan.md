---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-HARD-LAW
artifact_type: plan
tags: [sim, obs, hard, law]
---

# Implementation Plan - HardLawMonitor V1 & Observability Mode Config

This document outlines the detailed implementation steps for introducing the lightweight `HardLawMonitor` and a clean `ObservabilityConfig` to the RPG engine.

## 1. Observability Mode and Config
We will define an enum `ObservabilityMode` representing the current observability pressure of the simulator:
- `OFF`: Disable checks or critical only.
- `LIGHT`: Logs/counts violations safely (Default).
- `DEBUG`: Raises an exception on the first violation immediately.
- `CERTIFICATION`: Fails the current running scenario on violations.
- `LONG_RUN`: Configurable behavior.

We will introduce a configurable `ObservabilityConfig` that resolves the active mode using precedence:
1. Direct programmatic override (useful for tests/scenarios).
2. Environment Variable `SIM_OBS_MODE` or `RPG_OBS_MODE`.
3. Default `LIGHT`.

## 2. HardLawMonitor Design
`HardLawMonitor` will execute the following lightweight, O(1)-efficient, DirtySet-scoped checks:
- **Entity State Checks** (only if the entity is dirty and active/alive):
  - `hp >= 0` (Combat Component)
  - `gold >= 0` (Inventory Component)
  - `stamina >= 0` (Biological Component)
  - `readiness >= 0` (Attribute Component)
  - `position` is finite (Navigation Component)
- **Occupancy Collision Checks** (only for dirty moving entities):
  - Verify that no two solid alive entities occupy the same tile.

## 3. Tick Integration
We will hook `HardLawMonitor` into `Kernel.tick_once()`:
- Executed immediately after `self._phase_advancement()` completes.
- Statically gets `self._state` and `self._status.dirty_set`.
- If a violation occurs, the mode policy determines the next step:
  - In `DEBUG`: raise a custom `HardLawViolationError` exception.
  - In `CERTIFICATION`: fail the scenario.
  - In `LIGHT`: log the violation and increment the metrics.

## 4. Metrics Export
- `sim_hard_law_violations_total{law_id, severity}`: Cumulative counter.
- `sim_hard_law_last_violation_tick`: Gauge representing the last tick a violation occurred.
