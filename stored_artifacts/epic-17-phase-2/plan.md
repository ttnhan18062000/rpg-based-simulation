---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: epic-17-phase-2
artifact_type: plan
tags: [epic, phase]
---

# Implementation Plan: Epic 17 Phase 2

## 1. F6: World Age & F8: Enemy Scaling
**Target:** `src/core/world_state.py`, `src/systems/generator.py`, `src/config.py`
- Add `world_day` to `WorldState` as a computed property (`self.tick // 100`).
- Update the API Schema logic if necessary.
- In `generator.py::spawn_race`: Compute `world_age_mult = 1.0 + (world.world_day / 200) * 0.5`.
- Multiply `hp`, `atk`, `def` by `world_age_mult`.
- Adjust generated `level` boundings by `+ world_day//50` and `+ world_day//30`.

## 2. F7: Faction Raids on Town
**Target:** `src/systems/calamity_system.py`, `src/core/enums.py`
- Expose configurations `raid_interval_days: int = 20` and `raid_base_strength: int = 5`.
- Inside `CalamitySystem.on_tick`, add an intercept `if tick % (raid_interval_days * 100) == 0`.
- Identify a random hostile faction (e.g. Goblin).
- Spawn `raid_base_strength + world_day // 10` enemies at the edge of the sanctuary.
- Assign them to `AIState.RAID` (which triggers `src/actions/raid.py`).
- Fire `raid` domain telemetry events.

## 3. F10: Camp Reinforcement
**Target:** `src/core/regions.py`, `src/engine/world_loop.py` (or a dedicated system like `CampSystem`)
- Add `reinforcement_level: int = 0` to `Location` objects.
- Intercept the system tick interval every `500` ticks.
- Count guards using SpatialHash query around the camp's center.
- If guards < 3, spawn +1 guard at `tier + reinforcement_level`.
- If full guards, `reinforcement_level = min(3, reinforcement_level + 1)`.
