# Investigation — TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION

The bulk of this ticket's investigation happened pre-implementation, across several rounds of
peer review, and is recorded directly in the ticket's own Scope/Assumptions sections rather than
duplicated here. Summary of what was established, in order:

1. **Root cause confirmed**: `CampaignOrchestrator._build_initial_state()`'s survivor-reconstruction
   branch (`orchestrator.py:733-772`) builds every reconstructed `EntityState` with no position
   override, so `NavigationComponent.position` stays at its dataclass default `(0.0, 0.0)` for
   every survivor, unconditionally. Confirmed at real scale (13/16 survivors in a real
   `frontier_living_world` episode 0), tripping `LAW-SPAWN-OCCUPANCY` and stalling episodes 1-2 at
   ~tick 52.

2. **`_resolve_spawn_position()` (Batch B's mechanism) is not reusable**: it requires a
   `spawn_region` string. `EntityCarryForward` never captured one, and tracing further upstream
   found `spawn_region` never reaches a campaign-spawned entity in the first place —
   `WorldEntitySpawner.spawn_from_context()` hardcodes `EntitySpawnContext(spawn_region=None, ...)`.
   Filed `TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP` for that separate gap.

3. **Real fix basis**: `entity.navigation.position` — the entity's actual last position when the
   episode ended — is live, already-computed data. Carrying that forward
   (`EntityCarryForward.last_position`) is both cheaper and more directly supported by what's
   actually available than region-anchoring would have been.

4. **Geometry is not stable across episodes**: region bounds are authored (`RegionSpec.bounds`,
   stable), but per-tile terrain and building placement both draw from
   `DeterministicRNG(episode_seed)`, and `episode_seed = base_seed + episode_index` differs every
   episode. A carried `last_position` can be in-bounds but on newly-blocked terrain next episode —
   `blocked_tiles` is a real legality gate (`src/engine/legality.py`), not cosmetic. Requires a
   validity check with fallback, not a bare carry-through.

5. **Single authority for occupancy**: `LegalityServiceV2.verify_occupancy()` already checks WALL
   terrain, `blocked_tiles`, buildings, transient claims, and dynamic entity occupancy — reuse it
   directly rather than hand-rolling a duplicate check (matches this whole audit arc's own
   discipline against parallel implementations). Its dynamic-entity check has 3 staleness-prone
   sub-paths; `SpatialQueryService.get_occupancy_map()` caches onto the passed context by object
   identity with no invalidation — **reproduced directly**: a plain context's second
   `verify_occupancy()` call on a newly-occupied tile silently returned `True`/`LEGAL`. A
   `__slots__`-only reconstruction context (no room for the cache attribute) forces the deterministic
   uncached `.entities` scan instead — also reproduced directly, correctly rejecting the same
   scenario.

6. **Fallback chain must never collapse to a shared constant** — that reproduces the original bug
   in a narrower form. Chain: carried position → `verify_occupancy()` → deterministic probe via
   `_DECONFLICT_PROBE_OFFSETS` → expand the search (growing-radius spiral, clamped to
   `world_spec.topology.width`/`.height`, the only world-level bound available — region-bounds
   clamping was deliberately rejected since this fix anchors on last-known-position, not an
   authored region) → log a warning naming the entity/region if truly exhausted, mirroring
   `compiler.py:489-495`'s own `LAW-SPAWN-OCCUPANCY` exhaustion-warning message shape.

Full detail, including the two reproduction scripts run against the real `verify_occupancy()`/
`get_occupancy_map()` functions, is in the ticket's own Scope and Assumptions/Open Questions
sections — not re-derived here.
