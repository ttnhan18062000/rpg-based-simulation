---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING
artifact_type: plan
tags: [world, content, architecture]
---

# Plan — TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING

**Not yet implemented.** Per peer review's own request ("bring me the plan before implementing —
this one touches a pipeline with no production track record"), this plan is submitted for review
before any `src/` change is made.

## Two open decisions, flagged for peer review before implementation

1. **Position-resolution scope** (see `investigation.md`'s own "Real gap found" section):
   recommend accepting co-located (all-at-origin) spawn for this ticket, deferring real per-entity
   spatial placement to a separate follow-up ticket. This ticket's own AC (non-zero event count,
   episode runs to length) does not require spatial realism, and fixing it properly is a
   pipeline-wide change (new field needed on `ResolvedEntityProfile`), not Campaign-specific scope.
2. **`CatalogRepository`/`WorldModuleRepository` construction lifetime**: two options —
   (a) construct once in `CampaignOrchestrator.__init__()`, reused across all episodes in a
   campaign (avoids repeated `load_all()` filesystem I/O per episode; matches how a real multi-
   episode campaign would want this to behave) — or (b) construct fresh inside
   `_build_initial_state()` per call (simpler, matches this method's own existing per-call
   `WorldRepository("data/worlds")` construction pattern for regions/places, but repeats
   `load_all()` I/O on every episode). **Recommend (a)** — `load_all()` walks a directory tree and
   parses YAML on every call; for a 3-episode campaign that's 3x redundant I/O for content that
   never changes mid-campaign. Flagging both since this is a real design choice with a real,
   measurable cost difference, not a style preference.

## Steps (once the above are confirmed)

1. **Add `CatalogRepository`/`WorldModuleRepository`/`CatalogScenarioStateBuilder` construction**
   to `CampaignOrchestrator.__init__()` (per decision 2 above), alongside the existing
   `self._manifest`/`self._event_recorder`/`self._state` fields. Uses `CatalogRepository("data/content")`
   and `WorldModuleRepository()` (default `modules_dir`, matching
   `tests/integration/scenarios/test_scenario_setup_resolver.py`'s own real construction pattern),
   both with `.load_all()` called once.
2. **In `_build_initial_state()`'s "no alive carry-forwards" branch**
   (`orchestrator.py:655-663`): call `self._catalog_builder.build(spec, seed=episode_seed)`,
   producing `catalog_result`. Thread `entities=catalog_result.state.entities` into the branch's
   returned `AuthoritativeState`, alongside the existing `regions=compiled_regions,
   places=compiled_places`.
3. **Error handling**: if `ScenarioSetupResolver.resolve()` raises (e.g. an unknown
   `world_composition`, or a `perspective` not in the composition's own `default_perspectives` —
   both real `ValueError`s the resolver already raises), let it propagate — this is the same
   failure behavior `WorldCompiler.compile()` already has for a bad `world_composition` on the very
   next line, no new error-handling pattern needed.
4. **Do not touch** the survivor-reconstruction branch, `V2EngineManager`, or
   `src/certification/scenarios.py`'s `build_scenario_state()`/`ArenaInjector`.
5. **Tests** (see `test_plan.md`): a new real, end-to-end test via
   `CampaignOrchestrator.run_episode()` (the actual production path) confirming non-zero
   `kernel._current_tick_event_count` past tick 2 and the episode running well past the old ~52-tick
   stall point; a unit-level test confirming `_build_initial_state()`'s empty branch now populates
   `entities`; a regression test confirming the survivor branch is unaffected.
6. **If the position-resolution gap is deferred (recommended)**: file the follow-up ticket as part
   of this ticket's own Finalize phase, cross-referenced, not left as a bare comment.

## Explicitly not in this plan
- Any change to `V2EngineManager`, `src/certification/scenarios.py`, or `STALL_THRESHOLD`.
- Real per-entity spatial placement (pending the decision above).
- Re-verifying grief/nemesis reachability — that is
  `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`'s own scope, filed separately and blocked on
  this ticket's own closure.

## Resolution (post-implementation, both decisions confirmed with real evidence)

- **Decision 2 (repository lifetime)**: (a) confirmed correct with evidence, not preference — both
  `CatalogRepository` and `WorldModuleRepository` verified genuinely immutable after `load_all()`
  (every `get_*`/`list_*` method is a pure read; no downstream consumer mutates them). Built once
  in `__init__()`.
- **Decision 1 (position-resolution scope)**: recommendation (defer) was correct, but "accept
  co-located spawn as-is" was NOT — verified empirically per peer review's explicit instruction,
  and co-location genuinely trips a sustained `LAW-OCCUPANCY-COLLISION` hard-law violation (41
  occurrences over a real 70-tick run) and inflates `cooperation_event` to ~79% of all activity.
  Added an explicitly-labeled interim scatter workaround
  (`CampaignOrchestrator._scatter_catalog_entities()`) rather than shipping the degenerate result;
  real position resolution still deferred to
  `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`, which removes the workaround once it
  lands.
- **New decision, not anticipated in this plan's own original two**: `ScenarioSetupResolver`'s
  default `compositions_dir` (`data/content/world_compositions/`) was found to have already
  diverged from `data/worlds/<id>/world.yaml` for `frontier_living_world` (the real
  `campaign_life_arc` world) — a real, distinct source-of-truth question, not anticipated when this
  plan was written. Resolved per direct user decision, citing
  `docs/architecture/world_repository_layout.md`'s own ADR: `CatalogScenarioStateBuilder` is now
  constructed with `compositions_dir=Path("data/worlds")`, Campaign-only, with
  `ScenarioSetupResolver._load_composition()` taught to accept both the nested and flat layouts.
  Repo-wide consolidation filed separately (`TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION`).
