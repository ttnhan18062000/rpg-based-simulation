---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260409-PH4-STG1-CORE-MODELS
artifact_type: plan
tags: [ph4, stg1, core, models]
---

# Phase 4 Stage 1 Implementation Plan

## Intent
Establish the core data structures for Phase 4 (Inheritance and Succession) to enable long-term world memory and entity continuity.

## Affected Files/Modules
- `src/core/models/history.py` [NEW]
- `src/core/models/continuity.py` [NEW]
- `src/core/models/households.py` [NEW]
- `src/core/models/local_scars.py` [NEW]
- `src/core/models/regions.py` [NEW]
- `src/core/models/world_state.py` [MODIFY]
- `phase_4_ds_implementation_plan.md` [MODIFY]

## Intended Behavior
1.- No existing `InheritanceRecord`, `LocalScarRecord`, or `RegionConsequenceRecord` found.
- `HistoricalEvent` will be a new pattern for causal world memory.
3. `SuccessorRecord`: Links deceased legacy to Household/History.
4. `LocalScarRecord`: Spatial aftermath of events with recovery tracks.
5. `RegionConsequenceRecord`: Aggregated regional stability/danger.

## Architecture/Data-Flow Notes
- These records will be stored in registries within the `WorldState`.
- Entities will reference their `household_id`.
- `SuccessorRecord` will be created upon entity death (in later stages).
