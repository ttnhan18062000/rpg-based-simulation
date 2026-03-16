# Phase F: Fault Injection (Chaos)

## Objective
Verify that the engine handles partial AI results without stalling or losing determinism.

## Implementation Details
1. **Config**: Add `chaos.enabled` and `chaos.drop_rate` to `src/config.py`.
2. **WorkerPool Injection**: 
    - In the collection phase, if `chaos.enabled`, roll a random check against `drop_rate`.
    - If it hits, "forget" that entity's result.
3. **WorldLoop Resilience**:
    - Modify the "collect" phase to detect missing results.
    - Inject an `IdleActionProposal` for any missing result.
    - Ensure `EventLog` records a "Worker Timeout/Chaos Drop" event for visibility.

## Success Criteria
- Simulation successfully completes 1,000 ticks with 10% packet loss simulated.
- Replay is verified to be 100% deterministic even when the "random drops" occur (seed-controlled).
