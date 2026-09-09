---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING
artifact_type: investigation
tags: [world, content, architecture]
---

# Investigation — TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING

## Current state of `CampaignOrchestrator._build_initial_state()`

Two branches (`src/domains/campaigns/orchestrator.py:604-863`), both starting from the same
`WorldCompiler.compile()` call for `regions`/`places`:

- **No alive carry-forwards** (episode 0, or any episode after a full-party wipe) — lines 655-663:
  `return AuthoritativeState(tick=0, seed=episode_seed, regions=compiled_regions,
  places=compiled_places)`. **No `entities=` — defaults to `{}`.** This is the entire bug.
- **Survivors exist** (episode N>0, real carry-forwards) — lines 665-863: reconstructs `EntityState`
  objects from `EntityCarryForward` snapshots, applies social-memory/grief/nemesis/progression-plan
  imports, and returns `AuthoritativeState(tick=0, seed=episode_seed, entities=entities,
  regions=compiled_regions, places=compiled_places, region_loyalty_pressure=..., ...)`. Rich,
  correct, not touched by this ticket.

## Real, empirical confirmation that the catalog pipeline works for `campaign_life_arc`'s own scenario

Ran (not reasoned from tests alone) `CatalogScenarioStateBuilder.build()` against
`SimulationScenarioDefinition(world_composition="frontier_living_world",
perspective="hero_guild_perspective", ...)` — the exact real shape `campaign_life_arc.yaml`'s own
episodes use (`config/simulation_quality/profiles/campaign_life_arc.yaml` + the manifest
construction in `tools/calibrate_simq.py`'s `_run_campaign_engine()`).

Real construction requirements (my first attempt used default-constructed, unloaded repositories
and failed with `ValueError: Referenced module 'frontier_village_core' not found in repository`):

```python
catalog = CatalogRepository("data/content"); catalog.load_all()
module_repo = WorldModuleRepository(); module_repo.load_all()
builder = CatalogScenarioStateBuilder(catalog, module_repo)
result = builder.build(scenario, seed=42)
```

Result: **15 real entities** — 7 human (factions 1-3: hero + village NPCs from
`frontier_village_core`), 4 goblin (`goblin_camp_conflict`), 1 spider, 1 undead
(`undead_battlefield`), 2 wolf (`wolf_den_near_forest`) — every module in
`frontier_living_world.yaml`'s module list resolved into real entities, not a partial/synthetic
subset. `result.setup.perspective_id == "hero_guild_perspective"` confirmed correctly threaded.
This is strong evidence the pipeline is functionally correct for this exact use case, not merely
passing its own narrow test fixtures.

## Real gap found: no per-entity spatial placement anywhere in the pipeline

Every one of the 15 entities spawned with `position=(0.0, 0.0)` — identical, all stacked at the
origin. Traced to `WorldEntitySpawner.spawn_from_context()`
(`src/worldassembly/entity_spawner.py:27-67`):

```python
for _key, profile in ctx.entities.items():
    spawn = EntitySpawnContext(position=default_position, spawn_region=None, ...)
    ...
```

`default_position: Tuple[float, float] = (0.0, 0.0)` is a single function-level parameter, applied
identically to every entity in the loop — there is no per-entity position logic at all.
`grep -rn "spawn_from_context(" src/ tests/` shows every call site (the pipeline's own dedicated
test file included) uses the default; `default_position` has never been overridden by anyone,
anywhere. `ResolvedEntityProfile` (`src/worldassembly/models.py:8-28`, the per-entity resolved data
`ctx.entities` holds) has no position/region/spawn-zone field — the data needed for per-entity
placement doesn't exist yet in this pipeline's own model, so this is not a simple caller-side
parameter-passing fix.

**This is real, structural, pre-existing scope in the pipeline itself** — not introduced or
discovered as a consequence of wiring it into Campaign; any future live consumer of this pipeline
would hit the same gap. Consistent with the user's own explicit instruction: "expect to find gaps
and file them rather than patching around them."

## Scope decision: accept co-located spawn for this ticket, defer position resolution

Recommended, not yet locked in — see `plan.md` for the peer-review checkpoint.

This ticket's own Acceptance Criteria (per the user's explicit decision) require only real,
non-zero `kernel._current_tick_event_count` past tick 2 and the episode running to something close
to its configured length — not spatial realism. Entities co-located at the same position may, if
anything, *increase* early interaction/event generation (proximity-based combat/interaction
triggers would fire immediately rather than requiring entities to path toward each other first) —
plausibly helpful for this ticket's own AC, not a blocker. Real per-entity spatial placement (e.g.
deriving a spawn point per entity from its originating module, anchored to
`WorldCompiler.compile()`'s own already-computed region bounds) is a materially larger change
(needs a new field on `ResolvedEntityProfile` or an equivalent side-channel, threaded through
`WorldAssemblyResolver`/`ArchetypeEntityFactory`) that would affect every future consumer of this
pipeline, not just Campaign — out of proportion to what this ticket needs to fix. Recommend: accept
co-located spawn here, file a separate follow-up ticket for real position resolution (benefits the
whole pipeline, not Campaign-specific — a good candidate for whoever eventually consolidates the
3 scenario-construction paths, per the user's own framing of that as separate, future work).

## What the wiring change itself looks like

Confined to `_build_initial_state()`'s "no alive carry-forwards" branch
(`orchestrator.py:655-663`). Add a `CatalogScenarioStateBuilder` call (constructed once, reusing
the orchestrator's own catalog/module-repo instances — needs a real decision on whether those are
built once per `CampaignOrchestrator` instance in `__init__` or once per call in
`_build_initial_state()`; the former avoids repeated `load_all()` I/O across episodes in the same
campaign, the latter is simpler and matches this method's own existing per-call `WorldRepository`
construction pattern — see `plan.md`) using `spec.world_composition`/`spec.perspective` (already
available as `spec` is this method's own second parameter), and thread the resulting
`entities=result.state.entities` into the branch's existing `AuthoritativeState(...)` return
alongside the already-present `regions=compiled_regions, places=compiled_places`.

The survivor-reconstruction branch is untouched — confirmed it never calls the empty-branch's own
entity construction, so no risk of double-spawning or interference.
