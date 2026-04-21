# Attach Gate 1: Movement Support Boundary (Milestone 2)

## Supported Behavior
- **Grid-Based Movement**: Movement is strictly tile-to-tile.
- **Manhattan Metric**: Adjacency and distance are calculated using Manhattan distance.
- **Authoritative Validation**:
  - Alive check for actor.
  - Walkability check via `world.grid`.
  - Occupancy check: 1 entity per tile.
  - Simultaneous claim resolution: If two entities move to the same empty tile in the same tick, both (or one, deterministically) must be rejected/resolved to prevent overlap.
- **Authoritative Apply**: 
  - Position mutation via `EntityUpdate`.
  - `moved_this_tick` flag for observability.
- **Visibility**:
  - `movement_count` signal in `PressureSignals`.
  - Replay capture of `new_position`.

## Explicitly Excluded
- **Diagonals**: No diagonal movement support in this slice.
- **Pathfinding**: BFS/A* is an AI concern. This slice only supports the *execution* of a single-step move proposal.
- **Complex Terrain**: Only basic walkability (Material.WALL vs others) is supported for parity. Terrain costs are excluded for Gate 1.
- **Pushes/Knockbacks**: Physics-driven movement is excluded.
- **Combat Interleaving**: Movement is processed as a "Local" work kind, independent of combat phase if possible (sequential resolution).

## Support Boundary
- Movement is officially supported for **all Hero and Mob entities** in the standard simulation loop.
- Supported in both **Local** and **Concurrent** execution modes (where concurrent is proven non-conflicting).

## Proof Path
- **Parity Proof**: `tests_v2/parity/test_movement_parity.py`
  - Enforces bit-identical behavior and error-reason parity against original `src` behavior for supported grid movement scenarios.
- **Contract Proof**: `tests_v2/gameplay/test_movement_contract.py`
  - Enforces authoritative state boundaries and V2-specific movement invariants.
