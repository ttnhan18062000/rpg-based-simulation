# TCK-20260513-PERF-CADENCE-INTEGRATION

## Title
Integrate System Cadence into Authoritative Pipeline

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Apply the cadence model to non-critical subsystems in the `AuthoritativeApplyPipeline` to reduce per-tick CPU load.

## Scope
- Modify `AuthoritativeApplyPipeline.refine` to consume a `SystemCadence` (or use defaults).
- Apply `should_run` checks to `StrategicIntelligenceSystem`, `WorldDynamicsSystem`, `TownResolutionSystem`, and `BuildingSabotageSystem`.
- Implement `tests/integration/pipeline/test_strategic_cadence.py`.

## Acceptance Criteria
- Strategic evaluation only runs on ticks satisfying the cadence.
- World dynamics (spawning/evolution) respects the cadence.
- All existing strategic and world tests pass (verify cadence doesn't break logic).

## Related Tickets
- TCK-20260513-PERF-CADENCE-CORE

## Related Code Areas
- `src/engine/pipeline.py`
