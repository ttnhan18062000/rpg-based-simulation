# Investigation — TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION

## The data already exists and is already threaded through

- `PopulationSpec.spawn_region: str` (`src/worldbuilding/schema.py:210`) is already populated per
  population during merge:
  - Archetype-native path: `resolver.py:889-907` (`resolve_module_contribution`) resolves
    `preferred_regions[0]` (or the module's own first region as fallback) into a namespaced
    `spawn_region` string, raising `ResolverError` if a preferred region isn't actually in scope
    (`resolver.py:882-887`).
  - v1-recipe path: `resolver.py:470` does the same namespacing.
- `RegionSpec.bounds: tuple[int,int,int,int]` (`src/worldbuilding/schema.py:89`, `[min_x, min_y,
  max_x, max_y]`) is real per-module geometry, confirmed two ways: (1) direct YAML read —
  `grid_bounds: [130, 30, 160, 70]` in `data/content/world_modules/river_crossing.yaml`; (2) its
  mapping into `RegionSpec(bounds=reg.grid_bounds, ...)` at `resolver.py:102` and `:803`.
- Both land in one merged `world_spec` (`resolver.py:673-688`: `world_spec.regions =
  list(regions.values())`, `world_spec.entities = list(entities.values())`), which is exactly the
  `spec` argument `CompileProfileResolver.resolve()` receives (`resolver.py:750`) — the function that
  builds `ResolvedEntityProfile`, and which already iterates `spec.regions` today (`resolver.py:985`,
  currently only for town ownership).

Conclusion: the ticket's own "central design question" (declarative-per-module vs.
procedural-from-region-bounds) is already answered by existing data — no new authoring format
needed. Position = region anchor (declarative, authored) + a deterministic point within that
region's bounds (procedural, derived).

## `EntitySpawnContext.spawn_region` is a dead, unrelated mechanism — not the intended hook

Checked before adding a new field, per peer review. `EntitySpawnContext.spawn_region: Optional[str]
= None` (`src/entities/archetype_factory.py:24`) — when non-`None`, gets written into the built
entity's `properties["spawn_region"]` (`archetype_factory.py:66-67`). But:
- The only real caller, `WorldEntitySpawner.spawn_from_context()` (`entity_spawner.py:57`), hardcodes
  `spawn_region=None` on every construction — the write path never fires today.
- A repo-wide grep for any reader of `properties["spawn_region"]` / `properties.get("spawn_region")`
  found zero consumers.
- Even if wired, it stores a region-name *string tag* on entity metadata — not spatial coordinates —
  so it would not have served this ticket's purpose regardless.

Genuinely dead on both ends. Recorded as an 8th instance in
`TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT.md` rather than fixed here, per that ticket's own
Out of Scope. This ticket adds a new, separate `spawn_position` field.

## Population count does not expand to individuals (pre-existing, separate gap)

`ctx.entities` / `ResolvedEntityProfile` is one entry per population *group*, not per individual.
`resolve_module_contribution()` (`resolver.py:900-907`) sets `PopulationSpec.count` but never
expands it; `ResolvedEntityProfile` (`models.py`) has no `count` field at all;
`WorldEntitySpawner.spawn_from_context()` spawns exactly one `EntityState` per `ctx.entities` key
regardless of count. Confirmed structurally.

Filed as its own ticket per peer review:
`TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` — `WorldCompiler.compile()`
independently sums `PopulationSpec.count` per `spawn_region` into `region_declared_population`
(`compiler.py:267-277`) and seeds `RegionState.population_cohorts` from that sum
(`compiler.py:362`), which is real, live-consumed state (demographics migration
`src/domains/demographics/cohort.py`, camp/reproduction gating `src/world/camp.py:148-150`,
`src/world/reproduction_humanoid.py:68-70`). Declared and spawned population counts diverge whenever
`count != 1` — out of this ticket's own scope (spatial placement, not count), but a real,
consumer-backed finding that deserved its own ticket rather than a footnote.

## Collisions are the expected case, not an edge case — real corpus evidence

`compiler.py:270-272`'s own comment already establishes multiple populations sharing one
`spawn_region` is normal ("this must sum, not overwrite"). Confirmed against real content, not
hypothesized: every module below has exactly one region and two population refs, so **both
populations necessarily resolve to the same `spawn_region`** (no other region is in scope for
`preferred_regions` to point to without raising `ResolverError`):

| Module | Region (bounds) | Populations sharing it |
|---|---|---|
| `bandit_road_trade_pressure.yaml` | `bandit_road` `[40,40,100,60]` | `bandit_ambush_group`, `merchant_caravan` |
| `forest_warden_grove.yaml` | (single region) | `forest_warden_patrol`, `sacred_grove_guardians` |
| `sunken_swamp_border.yaml` | (single region) | `swamp_tribe_patrol`, `swamp_ambush_party` |

A plain hash-to-point-in-bounds would very likely collide on any of these three real modules. Real
per-entity de-confliction is required, not optional — confirmed via this real corpus, not asserted.

## Determinism constraint

Position must be a pure function of `world_spec` content (module composition), not the spawner's
runtime `seed` parameter — keeps `CompileProfileResolver.resolve()`'s output a pure function of
content (matches its existing docstring/architecture: resolver produces "compile-ready" static data;
spawner converts it to `EntityState`), and keeps replay stable independent of spawner-seed choice.
`spec.entities` iteration order is itself deterministic (`resolver.py:673-688`: built by insertion
order during a deterministic topological-sort-ordered merge loop), so a de-confliction pass that
claims points in that same iteration order is reproducible run-to-run for a fixed composition.
