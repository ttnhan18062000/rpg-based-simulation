# Investigation: Combat and Movement Milestone 1

## Existing Distance Logic
- `src/core/models/vectors.py`: `Vector2.manhattan` is implemented as `abs(dx) + abs(dy)`.
- `src/systems/gameplay/combat_system.py`: `_tick_engagement` uses Manhattan distance `<= 1` for adjacency.
- `src/actions/combat.py`: `CombatAction.validate` uses `manhattan` for range checks.

## Existing Adjacency Logic
- Primarily orthogonal adjacency check in `CombatSystem` (`dist <= 1`).
- No explicit "adjacency" helper found yet, often re-implemented as `dist <= 1`.

## Existing Occupancy Logic
- `src/core/models/world_state.py`: `is_occupied(pos)` checks the spatial index for living entities at a specific position.
- `src/actions/move.py`: `MoveAction.validate` uses `world.is_occupied(target)`.

## Existing AoE Logic
- Limited. `CombatAction` handles single targets.
- Skills are defined elsewhere (likely `src/core/gameplay/classes.py` or `src/core/gameplay/skills.py`).
- Need to ensure AoE legality (range to center, LOS to center, splash by Manhattan).

## Existing Time Model
- `src/engine/world_loop.py`: Phase-based tick.
- `SchedulingPhase`: Selects entities where `e.next_act_at <= current_time`.
- `PreSystemsPhase`: Runs systems every tick via `SystemManager.tick`.
- Increments `world.tick` at the end of every tick.
- Separation of world-time and entity turns is partially present but world-time doesn't have its own "advancement" step outside the phases.

## Missing or Ambiguous Areas
- Explicit documentation of the rulebook.
- Centralized rule contract and legality primitives.
- Structural separation of world-time advancement (Milestone 1 Task 3).

### AoE Targeting Decision
- Use Option C: Introduce `LocationTarget(pos: Vector2)` for AoE and positional targeting. This keeps `ActionProposal.target` clean and type-safe.

### LOS Semantics
- LOS check skipped for `dist == 1` (melee) as there are no intermediate tiles. Consistent with current grid implementation.
