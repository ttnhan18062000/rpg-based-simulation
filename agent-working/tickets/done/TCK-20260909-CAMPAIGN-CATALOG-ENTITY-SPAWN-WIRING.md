---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING
phase: done
date: 2026-09-09
tags: [world, content, architecture]
---

# TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING

## Title
Wire the catalog-native scenario pipeline (CatalogScenarioStateBuilder) into CampaignOrchestrator so Campaign-mode episodes actually spawn entities

## Status
DONE

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
- [x] `CampaignOrchestrator._build_initial_state()`'s "no alive carry-forwards" branch spawns real
      entities via `CatalogScenarioStateBuilder`, for `campaign_life_arc`'s own real scenario shape
      (`frontier_living_world`/`hero_guild_perspective`), confirmed via a real test
      (`test_episode_zero_spawns_real_entities_matching_the_world_composition`).
- [x] `regions`/`places` (from the existing `WorldCompiler.compile()` call) are still populated
      alongside the new entities — no regression to `TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`'s
      own fix (same test).
- [x] The survivor-reconstruction branch (episode N>0, real carry-forwards) is confirmed unaffected
      — the pre-existing `test_build_initial_state_survivor_branch_also_carries_compiled_regions_and_places`
      never touches the new catalog-spawn code path and continues to pass unchanged.
- [x] The all-entities-at-origin gap is fixed for Campaign's own episodes (interim, explicitly
      labeled scatter workaround — real position resolution deferred, with a recorded rationale,
      to `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`), verified via
      `test_episode_zero_entities_are_scattered_not_co_located` and the zero-occupancy-violation
      assertion in `test_real_campaign_episode_event_stream_is_plausible_not_degenerate`.
- [x] A real `campaign_life_arc` episode run (via `CampaignOrchestrator.run_episode()`, the real
      production path) runs to something close to its configured `tick_limit` rather than stalling
      at ~52 — verified via `test_real_campaign_episode_does_not_stall_early`. (Per-tick
      `kernel._current_tick_event_count` non-zero-ness itself is verified via the real
      `ScenarioRuntimeService` construction `run_episode()` uses internally, in
      `test_real_campaign_episode_event_stream_is_plausible_not_degenerate` — `run_episode()`'s own
      `event_recorder` parameter, confirmed during Investigate, only ever surfaces 2 scenario-level
      bookkeeping event types, never the kernel-generated stream needed for this check.)
- [x] No `STALL_THRESHOLD` change anywhere in the diff.
- [x] Full scoped regression: `tests/unit/domains/campaigns/ tests/integration/campaigns/
      tests/integration/scenarios/ tests/integration/worldassembly/ tests/unit/certification/
      tests/integration/certification/ tests/unit/engine/ tests/unit/api/test_read_model_cache.py
      -m "not slow and not extra_slow"` passes with no regressions — 587 passed, 2 skipped, 44
      deselected, 0 failed.

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
- `TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION` (new; the repo-wide directory migration
  this ticket's own ADR citation calls for but deliberately does not do)
- `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` (new; real per-entity spatial placement,
  removing this ticket's own interim `_scatter_catalog_entities()` workaround)
- `TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED` (new; a sibling Pattern-6
  field-threading gap found while checking reachability at peer review's request)
- `TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY` (new; `event_recorder` only ever
  receives 3 scenario-bookkeeping event types, never the kernel-generated stream — found while
  writing this ticket's own real test coverage; open question whether Campaign SimQ scoring
  depends on the stream it isn't getting)
- `TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE` (new; the second recorded
  occurrence of this ticket's own post-push CI re-pin — the line-keyed pinning mechanism itself is
  brittle and its legitimate-maintenance failure mode is diff-indistinguishable from a prohibited
  gate-weakening edit, per peer review)

## Related Docs
- `docs/architecture/world_repository_layout.md` (the ADR governing the `compositions_dir`
  decision above)
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

**Repository lifetime (decision 2 from plan.md), resolved with evidence**: both
`CatalogRepository` and `WorldModuleRepository` confirmed genuinely immutable after `load_all()` —
grepped every method in both classes; only `load_all()`/`_load_module_file()` write instance
state, every `get_*`/`list_*` is a pure read, and no downstream consumer
(`WorldAssemblyResolver`/`ArchetypeEntityFactory`/`WorldEntitySpawner`) mutates the repository
objects it's given. Built once in `CampaignOrchestrator.__init__()`, reused across all episodes —
no state-leak risk to episode isolation.

**Scatter (decision 1 from plan.md), implemented and empirically verified**: added
`CampaignOrchestrator._scatter_catalog_entities()`, an explicitly-labeled INTERIM WORKAROUND
(deterministic, seeded from `episode_seed` via `DeterministicRNG`, same mechanism
`RaidService.spawn_raid()` already uses) — deployed after `CatalogScenarioStateBuilder.build()`
produces its co-located entities, before they're threaded into the returned `AuthoritativeState`.
Re-ran the same real 70-tick episode used to find the original problem:
- 15 distinct positions, zero tile collisions.
- **Zero `LAW-OCCUPANCY-COLLISION` violations** anywhere in the run (was 41).
- Event mix now varied and plausible: 15 separate `combat_initiated` events across the run (was 1
  isolated fight), `cooperation_event` down to 67 from 935 (no longer 79% of all activity), real
  economic activity (`gold_sink_fired`, `contract_offer_created`), 2 real deaths from distributed
  combat (13/15 alive at end). `stall_counter` touches 1 occasionally but never sustains — nowhere
  near `STALL_THRESHOLD=50`.

**Directory divergence (found while investigating the peer-flagged "duplication" concern for the
first `unit_faction_tension.yaml` content mirror) — resolved, per direct user decision, citing
`docs/architecture/world_repository_layout.md`'s own ADR**: `data/worlds/<world_id>/world.yaml`
(read by `WorldRepository`, used for `regions`/`places`) and
`data/content/world_compositions/<world_id>.yaml` (originally read by `ScenarioSetupResolver`)
were confirmed to have already diverged for `frontier_living_world` (the real `campaign_life_arc`
world) — 7 modules via the richer `module_refs` form (including `trading_company_hub`) plus
`information_source_profiles`/`pending_information_responses` in `data/worlds/`, vs. 6 modules
and neither field in `data/content/`. The ADR is explicit that `data/worlds/` is the single unified
root for every `world.yaml`-shaped source, `worldcomposition.v1` included — `data/content/
world_compositions/` is the anomaly. **Fix**: `CampaignOrchestrator.__init__()` now passes
`compositions_dir=Path("data/worlds")` to `CatalogScenarioStateBuilder`, and
`ScenarioSetupResolver._load_composition()` was taught to accept both the nested `<id>/world.yaml`
layout (tried first) and the flat `<id>.yaml` layout (fallback) — nested-first is safe for every
other existing caller, since `data/content/world_compositions/<id>/` never exists there, so the
check falls through to the pre-existing flat-file behavior unchanged. Re-ran the same real 70-tick
episode after switching (now 16 entities instead of 15, `trading_company_hub`'s own entity now
spawns): still **zero `LAW-OCCUPANCY-COLLISION` violations**, still a varied, plausible event mix
(14 distinct `combat_initiated` events, `cooperation_event` at 75/579 ≈ 13%, real economic/
progression/region-trauma activity, 11/16 alive at end from real distributed combat) — confirmed
directly, not assumed to carry over from the pre-switch result. The now-redundant
`data/content/world_compositions/unit_faction_tension.yaml` mirror (created before this directory
decision) was deleted; `unit_faction_tension` now resolves via its existing
`data/worlds/unit_faction_tension/world.yaml` directly, through the same nested-path lookup.

**Deliberate, justified exception to this ticket's own "Campaign-only" scope, called out
explicitly per peer review**: the `_load_composition()` fallback change lives in
`src/scenarios/resolver.py` — shared code, not `CampaignOrchestrator`-local. This is real, and
noted here rather than left to read as Campaign-only when it isn't: it is additive-only
(`data/content/world_compositions/<id>/` never exists for any current caller, so every other
caller's own lookup falls through to the pre-existing flat-file behavior unchanged, verified by
the full regression suite below), and was the only way to make the Campaign-only `compositions_dir`
override actually resolve real files given `data/worlds/`'s per-world-directory layout differs
structurally from the flat `data/content/world_compositions/` layout the resolver was originally
written against.

**Repo-wide consolidation explicitly deferred, per user decision**: this ticket does NOT retire
`data/content/world_compositions/` or migrate every other caller — scoped to Campaign's own
resolution only. Filed `TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION` for the real,
repo-wide migration the ADR still calls for, citing this ticket's own concrete divergence evidence.

**Test assertions (10 originally-failing tests) — read individually, not just patched to pass, per
peer review's explicit instruction**: all 10 use `MagicMock` scenario specs that previously never
needed real `id`/`perspective` values (since `_build_initial_state()` never actually called
`ScenarioSetupResolver.resolve()` for the episode-0 branch before this ticket). 9 of the 10 mock
out `ScenarioRuntimeService` entirely and assert only orchestrator-level bookkeeping (episode
history, `run_id`, `event_recorder` wiring) — the real entities this ticket now spawns are never
read by any of their own assertions, so setting real `id`/`perspective` string values on the shared
`_make_manifest()`/`_real_episode_spec()` test helpers is a non-vacuous, purely mechanical fix.
**One test's own assertion was genuinely, deliberately wrong for the new behavior**:
`test_build_initial_state_episode_zero_carries_compiled_regions_and_places` asserted
`state.entities == {}` as an intentional invariant — true for the pre-fix code, but describing the
exact defect this ticket exists to close, not a real design contract. Updated to assert real,
non-empty, correctly-`id`-keyed entities instead of relaxing the assertion or deleting the
coverage — the docstring explains why the old assertion existed and why it changed.

**`information_source_profiles`/`pending_information_responses` reachability — checked per peer
review, found NOT reaching consumers, filed rather than chased inline**: confirmed
`src/engine/pipeline.py:199`'s `information_belief` phase reads `state.information_source_profiles`
directly every tick, and `src/engine/apply.py:500` genuinely carries it forward — but neither
`_build_initial_state()` branch threads `information_source_profiles=`/
`pending_information_responses=` from the `WorldCompiler.compile()` result into the constructed
`AuthoritativeState` (only `regions=`/`places=` are threaded). `frontier_living_world` declares a
real, non-trivial `information_source_profiles` entry, so this is a genuine "declared but never
delivered" gap, not a moot one. Filed
`TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED` rather than fixing it here —
independently-scoped, unrelated to entity spawning.

**New real test file**: `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`, 4 tests,
all real (no mocking of `_build_initial_state()`/`CampaignOrchestrator`/`ScenarioRuntimeService`
internals):
- `test_episode_zero_spawns_real_entities_matching_the_world_composition` — real entities present,
  matching `frontier_living_world`'s own resolved archetype kinds.
- `test_episode_zero_entities_are_scattered_not_co_located` — every entity on a distinct tile.
- `test_real_campaign_episode_does_not_stall_early` — via `CampaignOrchestrator.run_episode()`
  itself (the real production entrypoint), confirms no ~52-tick stall regression.
- `test_real_campaign_episode_event_stream_is_plausible_not_degenerate` — via the same real
  `ScenarioRuntimeService` construction `run_episode()` uses internally, with a
  `kernel._event_listeners` hook attached (the only way to see the full per-tick event stream —
  confirmed `event_recorder=` only ever receives 2 scenario-bookkeeping event types, never the
  kernel-generated combat/cooperation/hard-law events this needs); asserts zero
  `InvariantViolation`, real distributed combat (≥3 `combat_initiated`), and `cooperation_event`
  under 50% of total activity (was ~79% pre-scatter).

Full scoped regression, final state: `pytest tests/unit/domains/campaigns/
tests/integration/campaigns/ tests/integration/scenarios/ tests/integration/worldassembly/
tests/unit/certification/ tests/integration/certification/ tests/unit/engine/
tests/unit/api/test_read_model_cache.py -m "not slow and not extra_slow"` (via
`/home/u24desktop/Working/venv/bin/python3`) → **587 passed, 2 skipped, 44 deselected, 0 failed**
(this count predates the new test file, which is itself `@pytest.mark.slow` and therefore excluded
from that scoped run by design — run directly instead: 4 passed, 0 failed).

## Files Changed
- `src/domains/campaigns/orchestrator.py` — `CampaignOrchestrator.__init__()` builds
  `CatalogRepository`/`WorldModuleRepository`/`CatalogScenarioStateBuilder` once (pointed at
  `data/worlds/` per the ADR); `_build_initial_state()`'s empty-carry-forwards branch spawns and
  scatters entities; `_scatter_catalog_entities()` new static method (explicitly-labeled interim
  workaround, see its own docstring and `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`).
- `src/scenarios/resolver.py` — `ScenarioSetupResolver._load_composition()` now tries the nested
  `<compositions_dir>/<id>/world.yaml` layout before the flat `<compositions_dir>/<id>.yaml`
  layout; backward-compatible for every existing caller (default `compositions_dir` never has the
  nested shape, so the check falls through unchanged).
- `tests/architecture/test_phase18_import_boundaries.py` — post-push CI caught a real, mechanical
  regression this ticket's own edit caused (not a new architectural violation): the
  `__init__()`/`_build_initial_state()` additions shifted `orchestrator.py`'s existing, already-
  reviewed `from src.observability.events import SimulationEvent` import from line 447 to 487.
  `_DOMAINS_OBSERVABILITY_PINNED`'s line-keyed exception no longer matched. Re-pinned to 487,
  following the exact precedent already documented in this same dict's own comment for an earlier
  ticket's identical collateral line-shift (`TCK-20260905-FAME-DERIVER-LEGEND-FACT`). Verified via
  `pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor -m "not slow
  and not extra_slow"` — 237 passed (was 236 passed, 1 failed). **This is now the second recorded
  occurrence of the same collateral drift** — per peer review, the line-keyed pinning mechanism
  itself is brittle, and its failure mode (a legitimate re-pin) is diff-indistinguishable from the
  prohibited gate-weakening edit the Gate Integrity rule exists to catch, costing real reviewer
  scrutiny each time. Filed `TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE` (P3) to
  make the pinning key stable instead — not fixed here.
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` — `_make_manifest()`/
  `_real_episode_spec()` helpers set real `id`/`perspective`/`initial_conditions`;
  `test_build_initial_state_episode_zero_carries_compiled_regions_and_places` updated to assert
  real, non-empty entities instead of the old (defect-describing) empty-entities invariant.
- `tests/integration/campaigns/test_progression_planner_three_episode.py` — `_make_manifest()`
  helper set to real `id`/`perspective`/`initial_conditions`, same reason.
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` — new, 4 real tests (see Test
  Summary).
- New tickets filed, not implemented: `TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION`,
  `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`,
  `TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED`,
  `TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY`,
  `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (filed earlier, now unblocked).

No change to `V2EngineManager`'s spawn path, the certification/arena `build_scenario_state()`/
`ArenaInjector` path, or `STALL_THRESHOLD` — all explicitly out of scope, per user decision.

## Completion Summary
Wired `CampaignOrchestrator._build_initial_state()`'s empty-carry-forwards branch to spawn real
entities via the existing but previously completely unwired `CatalogScenarioStateBuilder` pipeline
— fixing `campaign_life_arc`'s zero-entity root cause
(`TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`). Verified end-to-end with a real
70-tick `CampaignOrchestrator.run_episode()` run: the stall never triggers, events are non-zero
every tick, real distributed combat happens with real deaths. Along the way, verified rather than
assumed two real risks flagged during peer review — co-located spawn genuinely triggers a sustained
engine-level hard-law violation (fixed with an explicitly-labeled interim scatter workaround, not
silently accepted), and the entity-spawn path was reading a different, poorer world-composition
source than the regions/places path (fixed by pointing Campaign's own resolution at the ADR-correct
`data/worlds/` directory, scoped to Campaign only). Four real, evidence-backed follow-up tickets
filed rather than scope-crept into this one: repo-wide directory consolidation, real per-entity
position resolution (removing the interim scatter), a Pattern-6 field-threading gap found while
checking reachability, and grief/nemesis reachability re-verification now that entities exist.
Test assertions for all 10 originally-failing tests were read individually rather than
mechanically patched — one genuinely needed its own behavior-describing assertion updated, not
just its mock inputs fixed.

**Addendum (2026-09-11):** `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` landed real
per-entity spatial placement in `WorldEntitySpawner` itself (authored `spawn_region` + region
bounds, with deterministic de-confliction). `_scatter_catalog_entities()` — this ticket's own
explicitly-labeled interim workaround — has been deleted, and `_build_initial_state()` now uses
`WorldEntitySpawner`'s real positions directly. The "NOT valid for any spatial, proximity, or
distance-dependent measurement" caveat recorded throughout this ticket's own body (e.g. lines
56-58, 397) no longer applies — re-verified via the same real 70-tick `run_episode()` evidence
this ticket originally used: zero `LAW-OCCUPANCY-COLLISION` violations and a plausible event mix
(`combat_initiated >= 3`, `cooperation_event` share `< 50%`), now achieved via real authored
placement rather than the arbitrary grid-scatter.
