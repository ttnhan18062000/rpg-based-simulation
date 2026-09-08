---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING
phase: open
date: 2026-09-09
tags: [world, content, architecture]
---

# TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING

## Title
Wire the catalog-native scenario pipeline (CatalogScenarioStateBuilder) into CampaignOrchestrator so Campaign-mode episodes actually spawn entities

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION` confirmed the root cause of
`campaign_life_arc`'s event-silence: `CampaignOrchestrator._build_initial_state()` never spawns any
entities for a fresh episode (or any episode with no surviving carry-forwards, which cascades to
every episode in a fresh manifest) — it only compiles `regions`/`places` via
`WorldCompiler.compile()`. A real, tested, but completely unwired scenario-construction pipeline
already exists: `CatalogScenarioStateBuilder` (`src/scenarios/catalog_state_builder.py`) composes
`ScenarioSetupResolver` (world_composition + perspective → `ResolvedWorldBundle`) and
`WorldEntitySpawner` (`CompileContext` → real `EntityState` objects via `ArchetypeEntityFactory`)
into a working `AuthoritativeState(entities=...)` builder — but it has zero live consumers anywhere
in the codebase (only 3 test files reference it).

**User decision (2026-09-09, via peer review `rpg-feature-planning`, confirmed directly by the
user)**: wire `CatalogScenarioStateBuilder` into `CampaignOrchestrator` specifically — **not**
option (b) (a minimal Campaign-specific hero+goblin spawn mirroring `V2EngineManager`'s own manual
approach, rejected because it would make the stall symptom disappear without Campaign profiles
ever reflecting their own authored `world_composition` — "a fix that looks complete and isn't,"
the exact failure mode this batch of tickets has been closing), and **not** option (c) (touching
`V2EngineManager`'s own live API spawn path or the legacy `build_scenario_state()`/`ArenaInjector`
certification path — consolidating all three scenario-construction paths is a real, separate,
larger initiative, not a rider on this ticket).

**A real, empirical probe already surfaced a genuine gap in the catalog pipeline itself** (per the
user's own explicit scope guard: "treat 'it's tested' as necessary but not sufficient... expect to
find gaps and file them rather than patching around them") — see Investigate section below:
`WorldEntitySpawner.spawn_from_context()` spawns **every** entity at the exact same
`default_position` (literally `(0.0, 0.0)` unless overridden, and it is never overridden anywhere
in the codebase, including the pipeline's own tests) — there is no per-entity spatial placement
anywhere in this pipeline. This is real scope this ticket's own Plan must explicitly decide on
(accept co-located spawn for this ticket's own acceptance criteria, which do not require spatial
realism — or scope real position resolution as part of this fix), not silently absorb or ignore.

## Scope
- Wire `CampaignOrchestrator._build_initial_state()`'s "no alive carry-forwards" branch (episode 0,
  and any episode where nothing survived) to spawn entities via `CatalogScenarioStateBuilder` (or
  its constituent pieces directly), reading the episode's own `spec.world_composition`/
  `spec.perspective`, in addition to (not instead of) the existing `WorldCompiler.compile()` call
  for `regions`/`places` — both are needed; `CatalogScenarioStateBuilder.build()`'s own state
  object does not carry `regions`/`places`.
- Campaign-only. Do not modify `V2EngineManager`'s spawn path or the certification/arena
  `build_scenario_state()`/`ArenaInjector` path.
- Address (or explicitly, evidence-backed, defer with rationale) the all-entities-at-origin gap
  found in `WorldEntitySpawner.spawn_from_context()` — a real design decision, not a silent
  omission either way.
- Confirm the survivor-reconstruction branch (episode N>0 with real carry-forwards) is unaffected —
  it already builds `EntityState` objects from `EntityCarryForward` snapshots and must keep doing
  so; only the "nobody survived" branch changes.
- **Acceptance must include a real `campaign_life_arc` episode producing non-zero
  `_current_tick_event_count` past tick 2, running to something close to its configured length
  rather than stalling at ~52** (per the user's own explicit AC). Do not close any part of this by
  touching `STALL_THRESHOLD` — the standing prohibition from
  `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION` applies here too.

## Out of Scope
- `V2EngineManager`'s own live spawn path (`EntityGenerator`-based hero+goblin construction) —
  explicitly not touched, per user decision.
- The legacy `build_scenario_state()`/`ArenaInjector` certification path — explicitly not touched.
- Consolidating all 3 scenario-construction paths into one — a real, separate, larger initiative
  per the user's own framing, not this ticket's scope.
- `TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION`'s own question (why the
  governor enters `DEGRADED` at tick 1) — independent of whether entities exist; not reopened here.
- Re-verifying grief/nemesis reachability in a real, now-populated campaign run — that is
  `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`'s own scope (filed separately, blocked on
  this ticket), not duplicated here.
- Changing `STALL_THRESHOLD` or any other stall-detector logic — see Scope above.

## Acceptance Criteria
- [ ] `CampaignOrchestrator._build_initial_state()`'s "no alive carry-forwards" branch spawns real
      entities via `CatalogScenarioStateBuilder` (or equivalent), for `campaign_life_arc`'s own
      real scenario shape (`frontier_living_world`/`hero_guild_perspective`), confirmed via a real
      (not synthetic-only) test.
- [ ] `regions`/`places` (from the existing `WorldCompiler.compile()` call) are still populated
      alongside the new entities — no regression to `TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`'s
      own fix.
- [ ] The survivor-reconstruction branch (episode N>0, real carry-forwards) is confirmed unaffected
      by a real test.
- [ ] The all-entities-at-origin gap is either fixed (with test evidence of real spatial
      distribution) or explicitly deferred with a recorded rationale (e.g. filed as its own
      follow-up ticket) — not silently left unaddressed without a decision.
- [ ] A real `campaign_life_arc` episode run (via `CampaignOrchestrator.run_episode()`, the real
      production path — not a lower-level unit call) produces non-zero
      `kernel._current_tick_event_count` past tick 2, and runs to something close to its
      configured `tick_limit` rather than stalling at ~52 — verified with a real test.
- [ ] No `STALL_THRESHOLD` change anywhere in the diff.
- [ ] Full scoped regression: `tests/unit/domains/campaigns/ tests/integration/campaigns/
      tests/integration/scenarios/ tests/integration/worldassembly/ tests/unit/certification/
      tests/integration/certification/ -m "not slow and not extra_slow"` passes with no
      regressions.

## Related Tickets
- `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION` (origin; root cause this ticket fixes)
- `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` (found the same "real, tested, but
  completely unwired" pattern for `BiologicalSystem.update()` — same class of gap, different
  subsystem)
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (new, filed alongside this ticket, blocked
  on it — re-verifies `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`'s own reachability claim now that
  entities will actually exist)
- `TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION` (independent finding from
  the same investigation, not reopened by this ticket)

## Related Docs
- `docs/world/assembly_contract.md` (Entity Spawner Contract section — the pipeline's own
  documented contract, including its `default_position` parameter)

## Related Stored Artifacts
`staging_artifacts/TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING/` (investigation.md, plan.md,
test_plan.md — created as part of this ticket's own Scope/Investigate/Plan phases, per peer review
request to bring the plan back before implementing).

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (`CampaignOrchestrator._build_initial_state()`, the
  integration point)
- `src/scenarios/catalog_state_builder.py` (`CatalogScenarioStateBuilder`)
- `src/scenarios/resolver.py` (`ScenarioSetupResolver`)
- `src/worldassembly/entity_spawner.py` (`WorldEntitySpawner.spawn_from_context()`, the
  all-entities-at-origin gap)
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`, the existing regions/places call to
  preserve alongside the new entity spawn)

## Assumptions / Open Questions
- Whether the all-entities-at-origin gap should be fixed as part of this ticket or deferred is the
  central open design question — not decided here, to be resolved during this ticket's own
  Investigate/Plan write-up and reviewed by peer before implementation.

## Implementation Notes

**Investigate (2026-09-09) — real, empirical probe, not reasoning from tests alone.**

Confirmed `CatalogScenarioStateBuilder.build()` genuinely works for `campaign_life_arc`'s own real
scenario shape. Real construction pattern (`CatalogRepository("data/content")` + `.load_all()`,
`WorldModuleRepository()` + `.load_all()` — my first attempt used default-constructed, un-loaded
repositories and hit a `ValueError: Referenced module 'frontier_village_core' not found`; fixed by
matching the exact construction pattern `tests/integration/scenarios/test_scenario_setup_resolver.py`
already uses for this identical `frontier_living_world`/`hero_guild_perspective` combo):

```
scenario = SimulationScenarioDefinition(
    id="campaign_life_arc_ep0", world_composition="frontier_living_world",
    perspective="hero_guild_perspective", victory_conditions=[{"kind": "tick_limit", "value": 200}],
)
catalog = CatalogRepository("data/content"); catalog.load_all()
module_repo = WorldModuleRepository(); module_repo.load_all()
result = CatalogScenarioStateBuilder(catalog, module_repo).build(scenario, seed=42)
```

Produced **15 real entities**: 7 human (factions 1-3, matching `frontier_village_core`'s NPCs/hero),
4 goblin (`goblin_camp_conflict`), 1 spider, 1 undead (`undead_battlefield`), 2 wolf
(`wolf_den_near_forest`) — genuinely resolving every module in the composition's module list, not a
subset. This confirms the catalog pipeline is real and functional for exactly this scenario, not
merely "passes its own narrow unit tests."

**Real gap found, per the user's own explicit instruction to expect and file gaps rather than
patch around them**: every one of the 15 entities has `position=(0.0, 0.0)` — identical, stacked
at the origin. Traced to `WorldEntitySpawner.spawn_from_context()`
(`src/worldassembly/entity_spawner.py:27-67`): `EntitySpawnContext(position=default_position, ...)`
is constructed identically inside the `for _key, profile in ctx.entities.items()` loop — there is
no per-entity position resolution anywhere in this function, and `default_position` (a single
`Tuple[float, float]`, default `(0.0, 0.0)`) is never overridden by any caller anywhere in the
codebase (`grep -rn "spawn_from_context(" src/ tests/` — every call site, including the function's
own dedicated test file, uses the default). `ResolvedEntityProfile`
(`src/worldassembly/models.py:8-28`, the per-entity data `ctx.entities` carries) has no
position/region/spawn-zone field at all — this isn't a caller-side oversight, the data needed to
place entities per-module doesn't exist yet in this pipeline's own model. This is a real,
structural gap in the pipeline's own design, not something `CampaignOrchestrator` can trivially
work around by passing a different `default_position` (that would just move the single shared
point, not distribute entities).

**Scope decision needed from peer/user before implementation, not decided here**: whether to (a)
accept co-located spawn for this ticket (the Acceptance Criteria only need real, non-zero
`_current_tick_event_count` — entities stacked at the same position could still interact/fight,
which would if anything *help* produce events, not block them) and file the position-resolution
gap as its own follow-up ticket, or (b) scope real per-entity position resolution (e.g. deriving a
spawn point per entity from its originating module, using `WorldCompiler.compile()`'s own already-
computed region bounds as an anchor) as part of this ticket's own work. Recommending (a) — the
narrower option, consistent with the user's own explicit acceptance criteria and the "smallest
change that reflects the world's authored content" framing already used to reject option (b)'s
hero+goblin spawn — but flagging both for peer review before locking in, per this ticket's own
"bring the plan back before implementing" instruction.

## Test Summary
_(pending — Investigate/Plan phases only so far; no implementation, per explicit instruction to
bring the plan to peer review first)_

## Files Changed
_(pending — no `src/` files changed yet)_

## Completion Summary
_(pending)_
