# Adjust 01: Action Speed Balance Review

## Summary

Review and rebalance the speed/duration of specific actions across the simulation. Some actions may take too many or too few ticks relative to others, creating unnatural pacing.

## Current State

Each AI state handler has implicit or explicit action durations (how many ticks an action takes). These may not be well-balanced against each other.

## Areas to Review

| Action | Current Duration | Notes |
|--------|-----------------|-------|
| Basic attack | ? ticks | Should feel snappy |
| Skill use | ? ticks (cooldown-based) | Cooldown vs cast time |
| Looting | ? ticks | Should be quick but not instant |
| Resting | ? ticks | Should feel meaningful but not boring |
| Trading (buy/sell) | ? ticks | Shopping shouldn't dominate gameplay |
| Crafting | ? ticks | Should be longer than trading |
| Harvesting | ? ticks per resource node | Should match resource value |
| Movement | 1 tick per tile | Baseline — is this right for map scale? |

## Proposed Process

1. Audit all state handlers in `src/ai/states.py` for implicit durations
2. Document current values in a table
3. Present findings to developer for decision on adjustments
4. Implement agreed changes

## Affected Code

- `src/ai/states.py` — action durations in state handlers
- `src/config.py` — if durations become configurable
- `src/core/buildings.py` — shop/blacksmith/guild interaction times

## Notes

> **Decision required from developer** on all balance values. This ticket is an audit + proposal, not an implementation.

## Labels

`adjust`, `balance`, `ai`, `needs-decision`
