---
status: archived
layer: systems
authority: P1
audience: developer
---

> **ARCHIVED (2026-06-23):** This document describes the V1 StrategySystem (`src/systems/strategy_system.py`, `src/core/world_state.py`) which was replaced by the V2 Faction & Diplomacy System (Epic 5.3). See `docs/systems/faction_contract.md` for the authoritative V2 reference.

# Grand Strategy System

Technical documentation for the macroscopic faction simulation, including regional control, war states, and siege mechanics.

---

## Overview

The Grand Strategy system is the macroscopic simulation layer that manages long-term world evolution, faction dynamics, and regional control. It transforms individual combat outcomes into world-altering events like wars and territory conquests.

**Primary files:** `src/systems/strategy_system.py`, `src/core/world_state.py`, `src/systems/generator.py`, `src/actions/combat.py`

---

## Strategic State (`WorldState`)

The simulation tracks strategic data globally in the `WorldState`. This state is persistent and updated every tick (influence/aggression) or every 10 ticks (processing logic).

| Field | Type | Description |
|-------|------|-------------|
| `region_control` | `dict[str, float]` | Influence score for each region (-100.0 to 100.0). Positive = Hero Guild; Negative = Monsters. |
| `faction_aggression` | `dict[int, float]` | Current aggression level (0.0 to 100.0) per faction. |
| `war_status` | `dict[int, bool]` | Current diplomatic state per faction. `True` = War; `False` = Peace. |
| `faction_deaths_per_region` | `dict[tuple, int]` | Temporary buffer for death events: `(faction_id, region_id) -> count`. |

---

## StrategySystem (`src/systems/strategy_system.py`)

The `StrategySystem` processes the strategic buffer into world state changes. It runs every 10 ticks to provide responsive strategic feedback.

### Influence Calculation

When an entity dies in a region, its faction contributes to the regional influence score:

| Faction Group | Death Weight | Effect on Influence |
|---------------|--------------|-------------------|
| `HERO_GUILD`  | `-5.0`       | Decreases influence (Conquest) |
| `MONSTERS`     | `+5.0`       | Increases influence (Liberation) |

**Logic Flow:**
1.  **Death Attribution**: `CombatAction` records the death in `faction_deaths_per_region`.
2.  **Processing**: Every 10 ticks, `StrategySystem` sums these weights and updates `region_control`.
3.  **Clamping**: Scores are clamped between `-100.0` and `100.0`.
4.  **Cleanup**: The death buffer is cleared after processing.

---

## War & Aggression

Factions track an `aggression` level that influences their diplomatic state.

### Diplomacy Thresholds

| Transition | Threshold | Result |
|------------|-----------|--------|
| **Peace → War** | `aggression >= 80.0` | `war_status` becomes `True` |
| **War → Peace** | `aggression < 50.0` | `war_status` becomes `False` |

### Strategic Impact
When a faction is at **WAR**:
- **Tier Escalation**: The `EntityGenerator._roll_tier()` applies a `war_bonus` (default `0.15`), shifting the spawn distribution towards higher tiers (more Warriors/Elites).
- **Aggression Gain**: Factions typically gain `+0.001` aggression per tick via world evolution.

---

## Siege Mechanics & Strongholds

Regions can fall under monster control if influence drops significantly, triggering a "Conquered" state.

### Conquest & Liberation

| Event | Condition | Consequence |
|-------|-----------|-------------|
| **Region Conquered** | `influence <= -80.0` | Stronghold spawns; `CONQUERED_DEBUFF` enabled. |
| **Region Liberated** | `influence > 50.0` | Stronghold removed; debuff cleared. |

### Conquered Debuff (`CONQUERED_DEBUFF`)
When a region has an active **Stronghold**, all heroes within that region receive a status effect penalty.

- **Impact**: Multiplies `stats.atk` and `stats.def_` by `0.8`, and `stats.spd` by `0.9`. 
- **Persistence**: The debuff is refreshed every strategic tick as long as the hero is in the conquered region.

---

## Integration with Other Systems

The Grand Strategy system connects multiple components:

1.  **WorldLoop**: Orchestrates the `StrategySystem.on_tick` every 10 ticks.
2.  **CombatAction**: Specifically `apply_damage`, which finds the region of the defeated entity and updates the `world.faction_deaths_per_region` buffer.
3.  **EntityGenerator**:
    *   **Safe Zones**: Regions with `influence > 80.0` have a 50% reduced spawn rate and cap enemy tiers at `SCOUT`.
    *   **War Readiness**: Shifts spawn probabilities towards higher tiers during active war states.

---

## Extension Guide

The Grand Strategy system is designed to be extensible through the `StrategySystem`.

### 1. Adding New Strategic Objectives
To add a new objective (e.g., "Slay the Dragon" or "Build a Trade Hub"), you should:
- Define a new field in `WorldState` to track progress.
- Implement the logic in `StrategySystem.on_tick`.
- Use `context.emit` to broadcast status changes to the UI/Logging layers.

### 2. Modifying Influence Weights
The death weights are currently hardcoded in `StrategySystem._process_deaths`. To make them data-driven:
- Add a `strategic_weight` field to `FactionProfile` in `src/core/faction.py`.
- Update the system to query the registry instead of using fixed constants.

### 3. Adding New Diplomacy States
To add states like "Truce" or "Alliance":
- Expand the `war_status` dict to a more robust `diplomatic_state` enum.
- Update `_update_war_status` to handle the new transitions.

---

## References & Testing
For further understanding and verification, refer to the following:

- **Unit Tests**: [test_strategy.py](file:///d:/Projects/rpg-based-simulation/tests/unit/systems/test_strategy.py)
- **Combat Logic**: [combat.py](file:///d:/Projects/rpg-based-simulation/src/actions/combat.py)
- **Status Effects**: [effects.py](file:///d:/Projects/rpg-based-simulation/src/core/effects.py)
