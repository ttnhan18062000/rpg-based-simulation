# Enhance 03: Extend Simulation Maximum Tick to 50000

## Summary

The simulation maximum tick limit should be extended from 1000 to 50000 to allow longer-running simulations with more emergent behavior and progression.

## Current State

`SimulationConfig.max_ticks` defaults to 1000. This limits observation of late-game progression, economy cycles, and faction dynamics.

## Proposed Changes

1. Update `src/config.py` — change `max_ticks` default from 1000 to 50000
2. Update CLI `--ticks` default to 50000 (or keep 200 for quick testing)
3. Verify no performance issues with the event log at 50000 ticks:
   - `EventLog` is unbounded — may need a ring buffer or max size cap for very long runs
   - Frontend event list may lag with 50k+ events — consider pagination or virtualized scroll
4. Verify frontend `useSimulation` poll loop handles long-running state correctly (no integer overflow, no memory leak from accumulated events)

## Affected Code

- `src/config.py` — `max_ticks` default
- `src/__main__.py` — CLI argument default (optional)
- `src/utils/event_log.py` — consider ring buffer cap (optional)
- `frontend/src/components/EventLog.tsx` — performance with large event lists (optional)

## Risk

Low risk for the config change itself. Medium risk for performance at scale — may need follow-up optimize tickets.

## Labels

`enhance`, `config`, `small`
