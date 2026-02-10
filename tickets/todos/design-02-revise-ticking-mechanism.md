# Design 02: Revise Ticking Mechanism

## Summary

Review the current tick cycle and propose improvements. The current 4-phase tick loop may need revision for better pacing, action resolution, or performance at scale.

## Current Ticking Mechanism

The engine runs a `WorldLoop` with a 4-phase tick cycle:

1. **Schedule** — AI workers evaluate goals and produce `ActionProposal` for each entity
2. **Collect** — All proposals gathered from the thread-safe MPSC queue
3. **Resolve** — `ConflictResolver` arbitrates conflicting proposals deterministically
4. **Cleanup** — Apply resolved actions, update world state, tick status effects, spawn entities, log events

Each tick:
- All entities act simultaneously (turn-based, not real-time)
- One action per entity per tick
- Tick rate configurable via `tps` (ticks per second) for visualization

## Areas to Discuss

1. **Action granularity** — Should some actions span multiple ticks (e.g., crafting = 5 ticks)?
2. **Speed-based initiative** — Should faster entities act more often? (e.g., SPD 15 entity acts every tick, SPD 8 entity acts every 2nd tick)
3. **Action points** — Should entities have AP per tick that determines how much they can do?
4. **Tick subdivisions** — Should a tick have sub-phases (move phase, then combat phase) for more realistic resolution?
5. **Variable tick rate** — Should the engine support different tick rates for different subsystems?

## Proposed Process

1. Document current tick logic with timing data
2. Identify pain points (what feels wrong?)
3. Propose 2–3 alternative approaches
4. Present to developer for decision
5. Implement chosen approach

## Affected Code (if changes are made)

- `src/engine/world_loop.py` — tick cycle phases
- `src/engine/conflict_resolver.py` — resolution logic
- `src/ai/brain.py` — action proposal frequency
- `src/ai/states.py` — state handler tick awareness
- `src/config.py` — tick configuration

## Notes

> **Decision required from developer** on the ticking approach. This starts as a design review, then becomes implementation.

## Labels

`design`, `engine`, `core`, `needs-decision`
