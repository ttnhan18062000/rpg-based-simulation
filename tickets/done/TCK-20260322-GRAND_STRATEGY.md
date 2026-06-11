---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260322-GRAND_STRATEGY
phase: done
date: 2026-03-22
tags: [grand_strategy]
---

# TCK-20260322-GRAND_STRATEGY

## Title
Grand Strategy: Faction Wars, Territory Conquest, and Siege Mechanics

## Description
This ticket implements the strategic layer of the world. Factions no longer just exist; they compete for territory. Heroes must now defend the land, not just their own lives.

## Scope
- **Faction Wars**: Dynamic aggression levels that lead to formal "War" states, changing spawn ratios and AI behavior.
- **Territory Conquest**: A region-based control system where faction influence shifts based on combat outcomes.
- **Siege Mechanics**: The ability to "Conquer" and "Liberate" regions, including the introduction of "Strongholds".

## Acceptance Criteria
- [x] `WorldState` tracks `RegionControl` for all regions.
- [x] Factions enter `WAR` state at high aggression, increasing spawn rates of elite units.
- [x] Regions can be "Conquered" by monsters, applying global debuffs to heroes and disabling resources.
- [x] Heroes can "Liberate" regions by destroying a Stronghold object.
- [x] Replay/Telemetry reflects territory shifts in real-time.

## Related Artifacts
- [Final Plan](file:///d:/Projects/rpg-based-simulation/stored_artifacts/TCK-20260322-GRAND_STRATEGY/plan.md)
- [Walkthrough](file:///d:/Projects/rpg-based-simulation/stored_artifacts/TCK-20260322-GRAND_STRATEGY/walkthrough.md)
- [Technical Documentation](file:///d:/Projects/rpg-based-simulation/docs/grand_strategy.md)

## Final Status
**DONE**

### Summary of Changes
- Implemented `StrategySystem` to process regional influence and war states.
- Integrated death tracking in `CombatAction.apply_damage`.
- Added `CONQUERED_DEBUFF` and stronghold spawning logic.
- Updated `EntityGenerator` to respect regional control and war states for spawn distribution.
- Verified with comprehensive unit test suite in `tests/unit/systems/test_strategy.py`.

**Tier:** standard
**Type:** chore
**Priority:** P1
