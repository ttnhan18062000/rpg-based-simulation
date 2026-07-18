---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260322-GRAND_STRATEGY
artifact_type: plan
tags: [grand-strategy]
---

# Milestone 11: Grand Strategy - Faction Wars & Territory Conquest

This milestone introduces a strategic overlay where factions compete for regional control, enter formal war states, and engage in siege mechanics.

## User Review Required

> [!IMPORTANT]
> This change introduces regional "Conquest" states which can disable resource harvesting and apply global debuffs (reduction in HP/ATK) to heroes within those regions until liberated.

## Proposed Changes

### Core Models & State
#### [MODIFY] [world_state.py](file:///d:/Projects/rpg-based-simulation/src/core/world_state.py)
- Ensure `region_control` and `war_status` are fully utilized and serialized.
- Add `conquered_regions: set[str]` to track highly suppressed areas.

### Strategy System
#### [NEW] [strategy_system.py](file:///d:/Projects/rpg-based-simulation/src/systems/strategy.py)
- `StrategySystem.update(world)`:
    - Processes `faction_deaths_per_region` to shift `region_control`.
    - Kills of monsters increase hero influence; kills of heroes decrease it.
    - Threshold checks:
        - `> 80.0`: Secure Region (Safe zone).
        - `< -80.0`: Conquered Region (Hostile stronghold potential).
    - Toggles `war_status` based on `faction_aggression` thresholds.

### Combat Integration
#### [MODIFY] [combat.py](file:///d:/Projects/rpg-based-simulation/src/actions/combat.py)
- Update `faction_deaths_per_region` on every lethality event.

### Spawning & Generator
#### [MODIFY] [generator.py](file:///d:/Projects/rpg-based-simulation/src/systems/generator.py)
- Formalize the "War Bonus" for elite unit spawns.
- Implement "Conquered" spawning: Spawns special "Stronghold" entities in highly contested regions.

### Siege Mechanics
#### [NEW] [Stronghold Entity]
- A stationary, high-HP entity that anchors monster control in a region.
- Its presence disables resource nodes in the region.
- Destruction triggers a `REGION_LIBERATED` event and resets influence.

## Verification Plan

### Automated Tests
- `tests/unit/systems/test_strategy.py`:
    - Test influence shift calculation.
    - Test transition from `PEACE` to `WAR`.
    - Test "Conquered" state triggers and debuff application.
    - Test "Liberation" event upon stronghold destruction.

### Manual Verification
- Observe the "AI Goals" visualizer to see entities moving toward contested regions.
- Verify territory color shifts (if implemented in frontend) or log output for "Region X has been CONQUERED".
