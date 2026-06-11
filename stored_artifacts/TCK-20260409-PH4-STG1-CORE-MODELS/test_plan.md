---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260409-PH4-STG1-CORE-MODELS
artifact_type: test_plan
tags: [ph4, stg1, core, models]
---

# Phase 4 Stage 1 Test Plan

## Existing Tests to Run
- `pytest tests/core/test_world_state.py`: Ensure that adding new fields to `WorldState` doesn't break existing persistence/serialization.

## New Tests to Add
- `tests/core/models/test_continuity_models.py`: Verify that `InheritanceRecord` can be instantiated and serialized.
- `tests/core/models/test_household_models.py`: Verify that `HouseholdRecord` correctly links members and buildings.
- `tests/core/models/test_scar_models.py`: Verify that `LocalScarRecord` tracks severity and recovery.
- `tests/core/models/test_region_models.py`: Verify that `RegionConsequenceRecord` stores regional metrics.

## Core Scenarios
- Creating a `SuccessorRecord` with multiple inheritance channels (gear, reputation).
- Initializing a `HouseholdRecord` for a set of entities sharing a building.
- Recording a `LocalScar` after a simulated raid and verifying its recovery tick logic.

## Edge Cases
- Serialization of optional fields in `InheritanceRecord`.
- Household with zero members (cleanup scenario).
- Region boundaries and coordinate-based scar lookups.
