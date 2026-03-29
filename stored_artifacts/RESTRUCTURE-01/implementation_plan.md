# Implementation Plan: Static vs. Dynamic State Separation

This plan addresses the "Mixing Static vs. Dynamic State" issues identified in the architecture audit. It decouples invariant world data from frequently changing simulation variables.

## Proposed Changes

### [Backend] API Schema Updates
Update `src/api/schemas.py` to reflect the separation of concerns.

#### [MODIFY] [schemas.py](file:///d:/Projects/rpg-based-simulation/src/api/schemas.py)
- **[MODIFY] `BuildingSchema`**: Remove storage-related fields (`storage_items`, `storage_used`, `storage_max`, `storage_level`).
- **[MODIFY] `ResourceNodeSchema`**: Remove `remaining` and `is_available`.
- **[MODIFY] `TreasureChestSchema`**: Remove `looted` and `guard_entity_id`.
- **[NEW] `ResourceNodeStateSchema`**: Fields `node_id`, `remaining`, `is_available`.
- **[NEW] `TreasureChestStateSchema`**: Fields `chest_id`, `looted`, `guard_entity_id`.
- **[NEW] `BuildingStateSchema`**: Fields `building_id`, `storage_items`, `storage_used`, `storage_max`, `storage_level`.
- **[MODIFY] `WorldStateResponse`**: Add lists for `resource_nodes`, `treasure_chests`, and `buildings` using the new State schemas.

### [Backend] API Route Refactoring
Update `src/api/routes/state.py` to correctly populate the split data.

#### [MODIFY] [state.py](file:///d:/Projects/rpg-based-simulation/src/api/routes/state.py)
- **[MODIFY] `get_static`**: Remove dynamic field calculation and mapping. It will now only return positions, types, and invariant metadata.
- **[MODIFY] `get_state`**: Add logic to populate the dynamic lists for resource nodes, chests, and building storage from the current snapshot.

### [Frontend] Type Definitions
Update `frontend/src/types/api.ts` to match the split backend schemas.

#### [MODIFY] [api.ts](file:///d:/Projects/rpg-based-simulation/frontend/src/types/api.ts)
- Update `WorldState` to include `resource_nodes`, `treasure_chests`, and `buildings` (dynamic state).
- Update `Building`, `ResourceNode`, and `TreasureChest` interfaces to remove dynamic fields (leaving them in their State counterparts or marking as optional).

### [Frontend] State Management
Update `frontend/src/hooks/useSimulation.ts` to merge dynamic state updates.

#### [MODIFY] [useSimulation.ts](file:///d:/Projects/rpg-based-simulation/frontend/src/hooks/useSimulation.ts)
- Update the `/state` poll to extract the new dynamic lists.
- Implement logic to merge `remaining` counts, `looted` status, and `storage` data into the existing state variables.

## Verification Plan

### Automated Tests
- Update `tests/test_api_payload.py` to verify that dynamic fields are present in `/state` and absent in `/static`.
- Ensure that the total payload size of `/state` remains manageable.

### Manual Verification
- Inspect the output of `GET /api/v1/metadata/static` and `GET /api/v1/state` using `curl` or a browser.
- Verify that changing world state (e.g., harvesting a node) is reflected in the `/state` response but does not change the `/static` response.
- Verify that the frontend UI still correctly displays resource counts and chest status.
