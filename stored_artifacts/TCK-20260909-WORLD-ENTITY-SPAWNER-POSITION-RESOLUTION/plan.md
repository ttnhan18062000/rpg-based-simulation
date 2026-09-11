# Plan — TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION

Approach reviewed and approved by `rpg-feature-planning` (2026-09-11), with two required additions
folded in: deterministic de-confliction (collisions are the normal case, not an edge case — see
investigation.md's real-corpus evidence), and filing (not just flagging) the declared-vs-spawned
population divergence (`TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`, already
filed).

## Step 1 — `ResolvedEntityProfile` gets a new `spawn_position` field

`src/worldassembly/models.py`: add
```python
spawn_position: Optional[Tuple[float, float]] = None
```
Default `None` — every existing test-constructed profile stays valid and falls back to
`WorldEntitySpawner`'s existing `default_position` parameter (Step 3).

## Step 2 — `CompileProfileResolver.resolve()` computes real, de-conflicted positions

`src/worldassembly/resolver.py`, inside `resolve()` (currently lines ~958-1069):

1. Before the entities loop, build `region_bounds: Dict[str, Tuple[int,int,int,int]]` from
   `spec.regions` (already iterated at line 985 for town ownership — extend that same loop rather
   than adding a second pass).
2. New pure helper (module-level, in `resolver.py`, no RNG, no spawner `seed` dependency):
   ```python
   def _hash_point_in_bounds(key: str, bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
       min_x, min_y, max_x, max_y = bounds
       digest = hashlib.sha256(key.encode("utf-8")).digest()
       width = max(max_x - min_x, 1)
       height = max(max_y - min_y, 1)
       x = min_x + (int.from_bytes(digest[0:4], "big") % (width + 1))
       y = min_y + (int.from_bytes(digest[4:8], "big") % (height + 1))
       return (x, y)
   ```
3. New pure helper for de-confliction, given the entities loop's own deterministic iteration order
   (`spec.entities`'s insertion order is already deterministic — investigation.md):
   ```python
   def _resolve_spawn_position(
       key: str,
       spawn_region: str,
       region_bounds: Dict[str, Tuple[int, int, int, int]],
       claimed: Dict[str, set],
   ) -> Optional[Tuple[float, float]]:
       bounds = region_bounds.get(spawn_region)
       if bounds is None:
           return None
       region_claimed = claimed.setdefault(spawn_region, set())
       candidate = _hash_point_in_bounds(key, bounds)
       if candidate not in region_claimed:
           region_claimed.add(candidate)
           return (float(candidate[0]), float(candidate[1]))
       # Deterministic fixed probe sequence, clipped to bounds. Small, bounded — real region
       # sizes (investigation.md: e.g. 60x20 = 1200 tiles) make collisions past the first probe
       # rare; if the sequence is exhausted (degenerate 1-tile region with 2+ populations), fall
       # back to the unclipped candidate — an unavoidable real collision, not a bug in this pass.
       min_x, min_y, max_x, max_y = bounds
       offsets = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1),
                  (2, 0), (-2, 0), (0, 2), (0, -2)]
       for dx, dy in offsets:
           probe = (
               min(max(candidate[0] + dx, min_x), max_x),
               min(max(candidate[1] + dy, min_y), max_y),
           )
           if probe not in region_claimed:
               region_claimed.add(probe)
               return (float(probe[0]), float(probe[1]))
       region_claimed.add(candidate)
       return (float(candidate[0]), float(candidate[1]))
   ```
4. A `claimed: Dict[str, set] = {}` local to one `resolve()` call (never module/instance state — stays
   a pure function of this call's `spec`).
5. In both `ResolvedEntityProfile(...)` construction branches (with-archetype and without, currently
   lines ~1019 and ~1047), pass
   `spawn_position=_resolve_spawn_position(key, pop_spec.spawn_region, region_bounds, claimed)`.

## Step 3 — `WorldEntitySpawner.spawn_from_context()` reads it

`src/worldassembly/entity_spawner.py:54-60`, one-line change to the existing loop:
```python
position = profile.spawn_position if profile.spawn_position is not None else default_position
spawn = EntitySpawnContext(
    position=position,
    spawn_region=None,
    initial_alive=True,
    initial_active=True,
)
```
No signature change. `default_position` remains the fallback for any profile without a real
`spawn_region` (e.g. hand-constructed test profiles).

## Step 4 — Delete the interim scatter workaround

`src/domains/campaigns/orchestrator.py`: delete `_scatter_catalog_entities()` and its call site
(docstring already says to, per the ticket's own Request Summary). Re-run
`TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own real-episode verification (a real,
uninstrumented Campaign episode) and confirm zero `LAW-OCCUPANCY-COLLISION` violations and a
plausible event mix — achieved via real placement, not the scatter workaround. Remove that ticket's
own "NOT valid for any spatial, proximity, or distance-dependent measurement" caveat once confirmed.

## Step 5 — Docs

Update `docs/world/assembly_contract.md`'s Entity Spawner Contract section: replace the
single-`default_position`-for-every-entity description with the real `spawn_region`-anchored,
de-conflicted placement behavior, noting the `default_position` fallback still applies to profiles
without a resolved `spawn_position`.

## Scope guards

- No change to `PopulationSpec`, `RegionSpec`, or any authoring schema/YAML — the fix is entirely in
  how already-existing data gets consumed.
- No change to `WorldEntitySpawner.spawn_from_context()`'s signature.
- Does not touch `EntitySpawnContext.spawn_region` (confirmed dead, recorded separately in
  `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`, not fixed here).
- Does not expand `PopulationSpec.count` into multiple individually-spawned entities — that's
  `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`'s own scope. This ticket
  places one point per population *group* (today's existing spawn granularity), which is exactly
  what closes this ticket's own AC (zero `LAW-OCCUPANCY-COLLISION` from co-located spawns across
  different populations/modules).
