---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260409-PH4-STG2-SUCCESSION-LOGIC
artifact_type: plan
tags: [ph4, stg2, succession, logic]
---

# Plan: Phase 4 Stage 2 — Succession Logic

## Proposed Changes

### [Component] Models
#### [MODIFY] [households.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/households.py)
- Add `heirloom_ids: list[str] = Field(default_factory=list)` to `HouseholdRecord`.

#### [MODIFY] [world_state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/world_state.py)
- Add `successor_registry: dict[int, SuccessorRecord] = {}` to `WorldState` (keyed by `source_entity_id`). Update `freeze()` and `from_snapshot()` accordingly.

### [Component] Lifecycle System
#### [MODIFY] [hero_lifecycle_system.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/lifecycle/hero_lifecycle_system.py)
- **`process_hero_death`**:
    - Extract "motive fragments" (e.g., identity of the killer).
    - Create `HistoricalEvent` (DEATH).
    - Create `SuccessorRecord`.
    - Identify `HouseholdRecord`. Transfer "Heirloom" items to `household.heirloom_ids`.
- **`_process_hero_replacements`**:
    - Lookup `SuccessorRecord` using the scheduled replacement info.
    - If found, apply legacy data to the new hero (household_id, motive fragments).
    - Clean up `SuccessorRecord` once consumed.

## Verification Plan
### Automated Tests
- Integration test: `test_succession_flow.py`
    - Verify hero death creates history and successor records.
    - Verify successor hero inherits household and items.
    - Verify motive transfer (resentment/grudge).
