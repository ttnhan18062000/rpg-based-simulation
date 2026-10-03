---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH7-M1-TOWN
artifact_type: plan
tags: [ph7, m1, town]
---

# PH7 M1: Town Return and Building Registry

Establish the town as a navigable destination with explicit building objects.

## Proposed Changes

### [Building Substrate] [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Ensure `BuildingState` has `is_town_hub` flag or similar.
- Add `town_center: tuple[float, float]` to `AuthoritativeState`.

### [Building Logic] [NEW] [buildings.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/buildings.py)
- Implement `BuildingRegistry` for static building templates.
- Define service handlers for different building types.

### [Town Navigation] [NEW] [town_navigation.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/town_navigation.py)
- Implement `TownNavigation.get_nearest_service(entity, service_kind, state)`.
- Helper for AI to find the shop/blacksmith/inn.

### [Verification Plan]

#### Automated Tests
- `tests/town/test_town_building_contract.py`:
  - Verify buildings are correctly registered in the world state.
  - Verify entities can locate services by kind.
  - Verify distance checks for building interaction.

#### Manual Verification
- Visual audit of town layout snapshots to ensure building tiles and objects align.
