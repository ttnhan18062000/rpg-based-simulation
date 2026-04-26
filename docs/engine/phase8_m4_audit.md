# Phase 8 Milestone 4: Environment & World-Interaction Audit

## 1. Current State of World Interaction
The `src` engine has implemented high-level world dynamics (hazards/calamities) and building sabotage, but lacks local spatial interaction rules.

- **Terrain**: Currently non-existent. All tiles are "Open". There is no logic for blocked movement (walls) or movement penalties (forests).
- **Buildings**: `BuildingState` exists with HP and `functional` status. `BuildingSabotageSystem` handles damage. However, "Local Access" or "Usage" (e.g., entering a shop to buy) is currently implicit or handled via high-level `town_resolution.py`.
- **Resource Nodes**: `ResourceNodeState` exists but interaction is largely handled by Phase 5 logic which might need refinement for Phase 8 "Local Action" rules.
- **Position-Sensitive**: `SpatialHash` exists in `LegalityService` but is used only for adjacency/occupancy. No logic for chokepoints or flanking bonuses.

## 2. Identified Strategy Leakage
- **Risk**: Using `regions` for high-level "Safe Zone" checks is fine, but if `regions` are used to determine combat bonuses without local tile awareness, it becomes too coarse.
- **Remedy**: Implement a simple `TerrainType` or `LocalModifier` system that can be queried by the `CombatResolutionSystem`.

## 3. Gap Audit vs Phase 8 Backlog

| Gap ID | Description | Backlog Row Ref | Priority |
| :--- | :--- | :--- | :--- |
| **GAP-W01** | Missing local terrain types (Blocked/Slow/Cover) | LEG-RPG-075/094 | HIGH |
| **GAP-W02** | Missing high-ground/flanking bonuses | LEG-RPG-091/092 | MEDIUM |
| **GAP-W03** | Missing building interaction legality (Entry/Use) | LEG-RPG-033 | HIGH |
| **GAP-W04** | Missing chokepoint detection logic | LEG-RPG-076 | LOW |

## 4. Proposed Integration
- **Terrain**: Add `terrain_map: Dict[Tuple[int, int], str]` to `AuthoritativeState`.
- **Combat**: Update `CombatResolutionSystem` to check terrain at `attacker.position` and `target.position`.
- **Legality**: Update `LegalityServiceV2` to enforce building access and blocked terrain.
