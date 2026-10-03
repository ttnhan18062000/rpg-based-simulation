---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260409-PH1-STG1-STRATEGIC-STATE
artifact_type: test_plan
tags: [ph1, stg1, strategic, state]
---

# Test Plan: Strategic State Foundation (Phase 1)

## Core Scenarios

### 1. Model Validity
- Verify and validate all strategic records (Directive, Project, etc.) in `src/core/models/strategy.py`.
- Ensure they correctly inherit from `SimulationModel` and respect frozen/copy semantics.

### 2. Mind Integration
- Verify `MindAspect` initialization includes a valid `StrategicState`.
- Ensure entity generators/builders create entities with valid empty strategic state.

### 3. Authoritative Application
- Test `StrategicUpdate` with `ActionSystem`.
- **Scenarios**:
    - Add a new Directive.
    - Update an existing Project by ID.
    - Remove an Objective.
    - Handle multiple updates in one tick deterministically.

### 4. Isolation & Snapshot Safety
- Create an entity, add strategic state, create a snapshot. 
- Mutate the live entity and ensure the snapshot remains unchanged.
- Ensure no shared mutable references exist between snapshot and live state.

### 5. Serialization & Replay
- Serialize an entity with complex strategic state to JSON.
- Deserialization and verify all fields are restored correctly.
- Ensure replay functionality includes strategic updates.

## Automated Tests
- `tests/core/test_strategy_models.py`: Model level tests.
- `tests/systems/test_action_system_strategy.py`: Authoritative application tests.
- `tests/core/test_snapshot_strategic_isolation.py`: Snapshot/Isolation tests.

## Manual Verification
- Use the CLI inspector to verify strategic state visibility.
- Command: `python -m src.ui.cli.inspector --entity-id <ID>`
