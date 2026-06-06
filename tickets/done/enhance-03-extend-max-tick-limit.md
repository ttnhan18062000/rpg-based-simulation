# Enhance 03: Extend Simulation Maximum Tick to 50000

## Summary
The simulation maximum tick limit should be extended from 1000 to 50000 to allow longer-running simulations with more emergent behavior and progression.

## Current State
`SimulationConfig.max_ticks` defaults to 1000. This limits observation of late-game progression, economy cycles, and faction dynamics.

## Status
DONE

## Final Status
**DONE**: Extended the default simulation maximum tick limit to 50,000 in `src/config.py`. Verified that the authoritative world loop and event logging systems handle long-running simulations gracefully.

**Tier:** standard
**Type:** chore
**Priority:** P1
