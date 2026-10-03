# Plan — TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE

## Scope, as confirmed with peer review
Not "count expansion plus a bundled population_id fix" — one behavior: **port
`WorldCompiler.compile()`'s classic pipeline's population-materialization logic (spawn `count`
individually-positioned, `population_id`-tagged entities per population) into the newer
catalog/archetype-native pipeline** (`CompileProfileResolver.resolve()` →
`WorldEntitySpawner.spawn_from_context()`), which currently spawns exactly one entity per
population regardless of `count`, untagged.

This is the mirror image of every other "superseded implementation" finding this audit batch made
(`BiologicalSystem`, `spawn_calamity`, `degradation.py`): those were an older implementation left
behind after a newer one landed. Here the **newer** pipeline is the incomplete one; the classic
pipeline already has this right. Remedy is to port forward, not to delete anything.

## Implementation steps
1. `src/worldassembly/models.py` — add `count: int = 1` and `spawn_positions: Tuple[Optional[Tuple[
   float, float]], ...] = Field(default_factory=tuple)` to `ResolvedEntityProfile`. Keep
   `spawn_position` unchanged (backward compatible: still means "position for individual #0",
   still the sole source of truth for hand-constructed profiles that never set the new fields).
2. `src/worldassembly/resolver.py` (`CompileProfileResolver.resolve()`) — after resolving
   `spawn_position` for individual #0 exactly as today (unchanged call, preserves existing
   determinism/tests), resolve `pop_spec.count - 1` additional deconflicted positions using
   `f"{key}#{i}"` sub-keys against the SAME shared `claimed_positions` dict (so all individuals
   across all populations still deconflict against each other). Set `count=pop_spec.count` and
   `spawn_positions=(...)` on both `ResolvedEntityProfile(...)` construction sites (archetype
   branch and the else/legacy branch).
3. `src/entities/archetype_factory.py` — add `population_id: Optional[str] = None` to
   `EntitySpawnContext`; thread it into `ArchetypeEntityFactory.build_entity()`'s `properties` dict
   (mirrors the existing `spawn_region`/`name_override`/`current_tick` pattern already there).
4. `src/worldassembly/entity_spawner.py` (`WorldEntitySpawner.spawn_from_context()`) — loop
   `range(profile.count)` per profile instead of once, incrementing `entity_id` per individual
   (not per profile); pass `population_id=_key` (the profile's own `ctx.entities` registration key,
   already `PopulationSpec.id`, matching `compiler.py`'s own `pop_key` convention exactly — no new
   field needed on the model for this identifier) on the `EntitySpawnContext`. `count=0` spawns
   zero entities from that population (a correct behavior `PopulationSpec.count`'s own `ge=0`
   schema constraint already allows, silently wrong today since 1 was always spawned regardless).
   Thread `spawn.population_id` into `_spawn_legacy_guard()`'s own manually-built `properties` dict
   too (the archetype-native path gets it automatically via step 3).
5. Real test coverage: unit tests on `WorldEntitySpawner.spawn_from_context()` for count>1 (N
   entities, N distinct positions, all tagged `population_id`) and count=0 (zero entities);
   resolver-level test confirming `ResolvedEntityProfile.count`/`spawn_positions` are populated
   correctly, including deconfliction across multiple individuals AND multiple populations sharing
   a region; an integration-level real-corpus test confirming `frontier_living_world`'s declared vs.
   spawned population counts now reconcile.
6. Regression: full existing `tests/integration/worldassembly/`, `tests/unit/worldassembly/`,
   `tests/unit/entities/`, `tests/integration/entities/` suites unchanged in outcome (existing
   count-1-implicit hand-constructed profiles must keep passing unmodified).

## Explicit non-goals (per peer review's caution)
- **Does NOT close `TCK-20260912-CONTRACT-EXPIRY-...` or `TCK-20260911-PENDING-INFORMATION-
  RESPONSES-CATALOG-ACTOR-ID-MISMATCH`.** Tagging `population_id` on catalog-spawned entities is a
  necessary prerequisite for the actor-id-mismatch ticket, not sufficient by itself:
  `WorldCompiler.compile()`'s own `target_population_id` → `actor_id` resolution
  (`compiler.py:660-664`) matches against **its own internally-compiled entity dict**, which
  Campaign mode never uses — Campaign's live roster comes from this catalog pipeline instead. Real
  end-to-end verification (resolve a real `target_population_id` in a real Campaign episode,
  confirm the returned `actor_id` names the intended entity) is that ticket's own remaining scope,
  not something this fix alone can close. If time permits, will attempt that verification as a
  bonus check and report the result honestly either way — but will not claim that ticket done on
  the strength of tagging alone.
- Does not touch `region_declared_population`/`_seed_population_cohorts()` — per the ticket's own
  Out of Scope, since the demographic apportionment math itself isn't what's being questioned here,
  only whether `WorldEntitySpawner` should have expanded `count` (it should, and now will).
- Does not touch `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s own already-landed
  single-position-per-population deconfliction design — this reuses that exact mechanism
  (`_resolve_spawn_position`, `_DECONFLICT_PROBE_OFFSETS`, the shared `claimed_positions` dict) for
  additional individuals rather than replacing or duplicating it.
