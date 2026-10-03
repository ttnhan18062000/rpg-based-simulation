---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260409-PH4-STG1-CORE-MODELS
artifact_type: investigation
tags: [ph4, stg1, core, models]
---

# Phase 4 Stage 1 Investigation

## Findings from Codebase
- `src/core/models/world_state.py`: Likely needs to hold the new records (households, scars, regions).
- `src/core/entities/entity.py`: Might need a reference to successor/inheritance if living entities track it.
- Existing building/storage concepts in `src/core/models/` will be the foundation for `HouseholdRecord`.

## Duplication/Conflict Scan Results
- No existing `InheritanceRecord`, `LocalScarRecord`, or `RegionConsequenceRecord` found in `ls -R src/core/models/`.
- `HouseholdRecord` might overlap with some building occupancy logic, but the goal is to make it a first-class memory container.

## Reused Patterns
- Typed models using Pydantic or basic dataclasses (need to check existing models).
- Registries for tracking global records.

## Assumptions
- Phase 4 focuses on continuity, so these models must be designed for long-term persistence in the `WorldState`.

## Known Risks
- Circular dependencies if `Entity` and `SuccessorRecord` point to each other.
- Performance impact if `WorldState` grows too large with scars and records.
