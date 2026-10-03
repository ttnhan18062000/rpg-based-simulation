---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH7-M1-TOWN
artifact_type: investigation
tags: [ph7, m1, town]
---

# Investigation — PH7 M1: Town Return and Building Registry

## Goal
Establish the town as a physical destination with explicit buildings and navigation rules.

## Requirements
- **Town Region**: Define a region in `AuthoritativeState` that represents the town hub.
- **Building Records**: Formalize `BuildingState` (already exists in `state.py` but may need refinement).
- **Travel Logic**: Movement rules for returning to town (e.g., pathfinding or teleportation if "teleport back" is a mechanic, but V2 prefers real travel).
- **Spatial Mapping**: `building_tiles` already maps tiles to services. We need to reconcile this with `BuildingState` objects.

## Proposed Architecture

### 1. Building Registry (`town/buildings.py`)
- Define building types (INN, GUILD, SHOP, etc.).
- `BuildingState` refinement: Ensure it has `kind`, `position`, `hp`, and `functional` status.

### 2. Town Region Logic
- A specific `RegionState` with `is_town=True`.
- Entities in this region have access to town services.

### 3. Return-to-Town Action
- `MovementAction` should allow targeting a town landmark.
- AI should prioritize town when biological needs (sleep/hunger) are high or inventory is full.

### 4. Integration
- Reconcile `AuthoritativeState.buildings` with `building_tiles`.
- `ApplyPath` already handles building HP/functionality updates.

## Questions
- Is "Return to Town" a specific action or just movement?
  V2 prefers "real travel". So it's a `MovementAction` with the town center as the target.
- How do we handle "Service Handlers"?
  Mapping `BuildingState.kind` to a system (e.g. `INN` -> `InnSystem`).
