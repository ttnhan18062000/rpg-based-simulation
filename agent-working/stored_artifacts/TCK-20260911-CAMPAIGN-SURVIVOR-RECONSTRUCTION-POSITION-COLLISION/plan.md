# Plan — TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION

## Steps

1. **`EntityCarryForward.last_position`** (`src/domains/campaigns/state.py`): add
   `last_position: Optional[Tuple[float, float]] = None` (Optional — pre-existing carry-forward
   records/save data won't have it). Thread through `to_dict()`/`from_dict()`.

2. **Capture at extraction** (`orchestrator.py::_extract_entity_carry_forwards()`): read
   `entity.navigation.position` for each entity and populate `last_position` unconditionally (not
   gated by any `rules.carry_*` flag — position isn't an opt-in carry-forward rule, it's required
   for the entity to exist at all next episode).

3. **`__slots__`-only reconstruction context** (new, in `orchestrator.py` or a small helper module
   colocated with it): a class exposing exactly `terrain`, `blocked_tiles`, `buildings`,
   `building_tiles`, `transient_claims`, `entities` via `__slots__`. Comment marks the list
   deliberately exhaustive and names
   `test_reconstruction_context_slots_force_uncached_occupancy_scan` directly. Constructed once
   per `_build_initial_state()` call from `compiled_state`'s terrain/blocked_tiles/buildings (
   `building_tiles=None` so `verify_occupancy()` falls back to its own `buildings` dict scan),
   `transient_claims=[]`, and `entities` = the dict being built incrementally in the survivor loop
   (mutated in place, same object reused for every check — this is exactly what the `__slots__`
   restriction exists to make safe).

4. **Position-resolution helper**, e.g. `_resolve_survivor_position(entity_id, last_position, ctx,
   world_width, world_height) -> Tuple[float, float]`:
   - Candidate origin: `last_position` if not `None`, else a deterministic per-entity fallback
     origin (e.g. `_hash_point_in_bounds(str(entity_id), (0, 0, world_width-1, world_height-1))` —
     reusing the existing deterministic-hash helper from `resolver.py` rather than inventing a new
     one, for an entity carried forward without a `last_position`, an edge case expected to be rare
     given step 2 makes capture unconditional going forward).
   - `verify_occupancy(origin, ctx)` — if legal, use it, add to `ctx.entities` (a placeholder or the
     real constructed entity), done.
   - Else probe `_DECONFLICT_PROBE_OFFSETS` (imported from `src.worldassembly.resolver`) around the
     origin, `verify_occupancy()` at each, clamped to `[0, world_width-1] x [0, world_height-1]`
     (world-level clamp, not region — this fix anchors on last-known-position, not an authored
     region, so region bounds aren't the right clamp here).
   - Else expand: growing-radius ring search outward (radius 3, 4, 5, ... up to a bounded cap, e.g.
     `max(world_width, world_height)` as the absolute ceiling — guarantees termination), clamped the
     same way, `verify_occupancy()` at each candidate.
   - If the expansion exhausts without a legal tile: log a warning naming the entity and its region
     (if resolvable via `LegalityServiceV2.get_region_for_position`, else "unknown"), mirroring
     `compiler.py:489-495`'s message shape, and use the last-probed candidate anyway (matching that
     same precedent's own behavior — a known, warned-about degraded placement beats indefinite
     search or a silent shared-default collision).
   - Every accepted candidate is written into `ctx.entities` (so the next survivor's
     `verify_occupancy()` sees it) before returning.

5. **Wire into the survivor branch** (`orchestrator.py::_build_initial_state()`): after building
   `EntityState` objects (as today), resolve and set each one's `navigation.position` via the new
   helper, in survivor-iteration order (matching the existing `alive_carry_forwards.items()` loop
   order — deterministic given dict insertion order is preserved).

6. **Fix the misleading comment** at `orchestrator.py:733-736` — no longer describes
   `world_composition` as governing survivor placement; describes the real mechanism (last-position
   carry-forward + validity/fallback chain).

## Test Plan Summary
See `test_plan.md`. Headline: unit tests for the helper and the `__slots__` mechanism, plus the
real acceptance bar — a 3-episode `campaign_life_arc` run completing all three episodes with zero
`LAW-SPAWN-OCCUPANCY` violations, replacing the current stall at ~tick 52.

## Scope Guards
- No change to `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s own episode-0 path.
- No change to `get_occupancy_map()`'s own caching behavior — routed around via the `__slots__`
  context, not fixed at the source (out of this ticket's blast radius, noted in the ticket's own
  Assumptions for whoever picks that up separately).
- `TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP` stays a separate ticket, not folded
  in here.
