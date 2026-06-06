# TCK-20260529-COG-PHASE13-MEMORY

## Title

Temporal, Causal, and Spatial Memory Domain Implementation

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the Phase 13 Memory Domain consisting of TemporalModel, CausalMemory, and SpatialMemory, enabling entities to remember recent events, interpret causal outcomes, and update spatial mappings.

## Scope

- Define structural memory schemas (`DeadlineEntry`, `CooldownEntry`, `StalenessEntry`, `DelayRiskEntry`, `CausalMemoryEntry`, `RegionVisitMemory`, `RouteMemory`, `ResourceSiteMemory`, `FailedSearchMemory`) in `src/core/cognition.py`.
- Update `TemporalModel`, `CausalMemory`, and `SpatialMemory` nested components in `src/core/cognition.py`.
- Implement `TemporalPressureService` converting temporal data into dynamic urgency ratings.
- Implement `CausalAttributionService` mapping simulation failure events to subjective causal theories.
- Implement `SpatialMemoryUpdateService` updating visited counts, region familiarity, and hazard boundaries.
- Orchestrate integration checks inside a dedicated memory pipeline phase.
- Write robust unit, integration, and scenario tests under `tests/`.

## Out of Scope

- Bounding full multi-year history logs, persistent pathfinding cache dumps across multiple sessions.

## Acceptance Criteria

- Dataclasses successfully integrated inside `src/core/cognition.py`.
- `TemporalPressureService`, `CausalAttributionService`, and `SpatialMemoryUpdateService` implemented and verified.
- Causal memory entries bounded strictly by capacity metrics.
- Scenario tests verify retry adjustments after a simulated combat loss.

## Related Tickets

- `TCK-20260529-COG-PHASE11-HIERARCHY`
- `TCK-20260529-COG-PHASE12-PERCEPTION`

## Related Docs

- `docs/entity/entity_base.md`

## Related Code Areas

- `src/domains/memory/` (created)
- `src/domains/time/` (created)
- `src/core/cognition.py`
- `tests/unit/entity/test_phase13_temporal_model.py` (created)
- `tests/unit/domains/time/` (created)
- `tests/unit/domains/memory/` (created)
- `tests/integration/domains/memory/` (created)
- `tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py` (created)

