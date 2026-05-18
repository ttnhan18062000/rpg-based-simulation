# Investigation — PH7 M4: Building Damage and Sabotage

## Goal
Implement authoritative building damage and sabotage logic.

## Requirements
- **Target Validation**: Actions must target a valid `BuildingState`.
- **Damage Logic**: Apply `hp_delta` to buildings.
- **Consequences**: If HP falls to 0, `functional` is set to `False`. This disables services (already handled in `TownNavigation.get_nearest_service`).
- **Strategic Impact**: Sabotage should be an authoritative action that can be emitted by "Raider" archetypes.

## Proposed Architecture

### 1. Building Combat/Sabotage Action (`town/sabotage.py`)
- `SabotageAction.apply(entity, target_building_id, state) -> StateUpdate`:
  - Validates proximity and target existence.
  - Emits `BuildingUpdate` with `hp_delta`.

### 2. Update Application
- `ApplyPath.apply_generation` already handles `building_updates`.

## Questions
- Should there be a "repair" action?
  Yes, Blacksmith template had `REPAIR` service.
- Does building damage cause "Trauma"?
  Roadmap says "Damage can produce local concern/scar if supported". We have `RegionState.trauma_score`. We can increment it on building death.
