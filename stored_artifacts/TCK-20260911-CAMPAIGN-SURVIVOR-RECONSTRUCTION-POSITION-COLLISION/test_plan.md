# Test Plan — TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION

## Unit tests (new)
1. `EntityCarryForward.last_position` round-trips through `to_dict()`/`from_dict()`, including the
   `None` case (pre-existing records without the field).
2. `_extract_entity_carry_forwards()` populates `last_position` from `entity.navigation.position`
   for every entity, unconditionally (not gated by a `rules.carry_*` flag).
3. **`test_reconstruction_context_slots_force_uncached_occupancy_scan`** (exact name, referenced by
   the `__slots__` declaration's own comment): construct the reconstruction context, call
   `verify_occupancy()` once (tile free → legal), mutate `.entities` to add an entity on a
   *different* tile, call `verify_occupancy()` again on that tile on the *same* context object,
   assert it's now rejected — proving the uncached path is taken deterministically, not the stale
   cached path. Encodes the exact reproduction done during this ticket's own investigation.
4. Position-resolution helper: carried position free → used as-is. Carried position occupied by
   another survivor already placed in this pass → deterministic probe finds a different free tile
   (not the same for two colliding survivors — no double-collapse to one tile). Carried position
   `None` → deterministic fallback origin still resolves to a real, distinct tile per entity.
5. **Terrain-instability edge case, built from a real seed disagreement, not a fixture**: compile
   the same world composition at two different `episode_seed` values, scan for a real tile that is
   walkable in the first compile and blocked (`WALL` terrain, `blocked_tiles`, or a building) in the
   second. Construct a survivor whose `last_position` is that tile, run reconstruction against the
   second compile, assert the fallback chain relocates them to a real free tile rather than
   accepting the blocked one.
6. Exhaustion path: force a scenario where the fixed `_DECONFLICT_PROBE_OFFSETS` ring is fully
   occupied (small world, many survivors) and confirm the expanding search finds a legal tile
   beyond that ring, or — if the world is deliberately packed with no free tile at all — that a
   warning is logged (matching `compiler.py:489-495`'s message shape) and a tile is still assigned
   rather than the process hanging or raising.

## Regression
- `pytest tests/unit/domains/campaigns/` — must pass unchanged.
- `pytest tests/integration/campaigns/` — must pass unchanged.

## Acceptance-bar test (the real claim, not just unit coverage)
A real 3-episode `campaign_life_arc` run (matching the scenario that originally surfaced this bug)
must show:
- All three episodes reach their configured length — no stall attributable to
  `LAW-SPAWN-OCCUPANCY` around tick 52 the way episodes 1-2 previously did.
- Zero `LAW-SPAWN-OCCUPANCY` violations logged in episode 1+ (where survivors from episode 0 get
  reconstructed).
- Reported with real evidence (violation counts, episode completion ticks), not just "tests pass."

If this run surfaces something new, that gets reported before this ticket closes, not silently
absorbed into the fix.
