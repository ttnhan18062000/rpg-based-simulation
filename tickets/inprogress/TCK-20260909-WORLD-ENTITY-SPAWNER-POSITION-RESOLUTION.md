---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION
phase: open
date: 2026-09-09
tags: [world, content, architecture]
---

# TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION

## Title
`WorldEntitySpawner.spawn_from_context()` has no per-entity spatial placement — fix the spawner, not just Campaign's own workaround

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`: `WorldEntitySpawner.
spawn_from_context()` (`src/worldassembly/entity_spawner.py:27-67`) places **every** entity it
spawns at the identical `default_position` — a single function-level parameter
(`Tuple[float, float] = (0.0, 0.0)`), applied unconditionally inside its own
`for _key, profile in ctx.entities.items()` loop. No caller anywhere in the codebase has ever
overridden it (`grep -rn "spawn_from_context(" src/ tests/` — every call site, including the
pipeline's own dedicated test file, uses the default). `ResolvedEntityProfile`
(`src/worldassembly/models.py:8-28`, the per-entity resolved data `ctx.entities` carries) has no
position/region/spawn-zone field for a caller to even use if it wanted per-entity placement — the
data this would need doesn't exist yet in this pipeline's own model.

**This is not a Campaign-specific problem** — it is a latent defect in a shared pipeline that
stayed invisible because every prior consumer of `WorldEntitySpawner` was test-only, and tests
never needed spatial realism. `CampaignOrchestrator` (`TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`)
is the first live consumer, and confirmed the real consequence empirically: spawning every entity
onto the same tile trips `LAW-OCCUPANCY-COLLISION`
(`src/observability/hard_law_monitor.py`) repeatedly (41 sustained ERROR-severity violations over
a real 70-tick run) and inflates proximity-gated systems (`cooperation_event`,
`contract_offer_created`) into the dominant share of all simulation activity.

**Interim workaround already shipped, explicitly labeled temporary**:
`CampaignOrchestrator._scatter_catalog_entities()` (`src/domains/campaigns/orchestrator.py`)
applies a small, seeded, deterministic grid-scatter to Campaign's own spawned entities after
`CatalogScenarioStateBuilder.build()` returns — Campaign-local, does not touch
`WorldEntitySpawner` itself, does not reflect authored `world_composition` placement (arbitrary
offsets, not correct ones). **Delete that method once this ticket lands** — its own docstring
already says so.

## Scope
- Design real per-entity position resolution for `WorldEntitySpawner.spawn_from_context()` — likely
  requires a new field on `ResolvedEntityProfile` (or an equivalent side-channel) carrying a
  spawn-zone/region anchor per entity, threaded through from each entity's originating
  `WorldModuleSpec`/`ModuleRefSpec` (so a `frontier_village_core` entity spawns near the village,
  a `goblin_camp_conflict` entity near the camp, etc. — reflecting the authored `world_composition`,
  which the current co-located spawn does not).
- Update every live/test consumer of `WorldEntitySpawner.spawn_from_context()` if the function
  signature changes (check `tests/integration/worldassembly/test_world_entity_spawner.py` and any
  other caller for compatibility).
- Delete `CampaignOrchestrator._scatter_catalog_entities()` and its call site once real placement
  lands; re-run `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own real-episode test
  evidence (zero `LAW-OCCUPANCY-COLLISION`, plausible event mix) to confirm real placement achieves
  the same clean result the scatter workaround did, without the "arbitrary, not correct" caveat.
- Remove the "NOT valid for any spatial, proximity, or distance-dependent measurement" caveat from
  `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own record once this lands — that caveat
  is this ticket's own reason to exist.

## Out of Scope
- Any other gap this pipeline may have beyond position resolution (not surveyed here).
- Campaign-mode's own entity-spawn wiring — already implemented and closed; this ticket only
  removes its interim workaround once the real fix is ready.
- Consolidating the "legacy" spawn paths (`V2EngineManager`'s manual spawn,
  `build_scenario_state()`/`ArenaInjector`) — a separate, larger initiative the user explicitly
  declined to bundle into this work.

## Acceptance Criteria
- [ ] `ResolvedEntityProfile` (or equivalent) carries real per-entity spatial data derived from
      its originating module.
- [ ] `WorldEntitySpawner.spawn_from_context()` places entities at distinct, module-appropriate
      positions instead of a single shared `default_position`.
- [ ] A real Campaign episode re-run (same shape as
      `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own verification) shows zero
      `LAW-OCCUPANCY-COLLISION` violations and a plausible event mix, achieved via real placement
      rather than the scatter workaround.
- [ ] `CampaignOrchestrator._scatter_catalog_entities()` is deleted.
- [ ] No regression in `tests/integration/worldassembly/`, `tests/unit/certification/`,
      `tests/integration/certification/`, or `tests/unit/domains/campaigns/`/
      `tests/integration/campaigns/`.

## Related Tickets
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (origin of this finding; ships the interim
  workaround this ticket removes)
- `TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION` (sibling follow-up from the same
  investigation, unrelated scope — directory layout, not spatial placement)

## Related Docs
- `docs/world/assembly_contract.md` (Entity Spawner Contract section — needs updating once this
  lands, since it currently documents the single-`default_position` contract as-is)

## Related Stored Artifacts
None yet — created when this ticket is picked up.

## Related Code Areas
- `src/worldassembly/entity_spawner.py` (`WorldEntitySpawner.spawn_from_context()`)
- `src/worldassembly/models.py` (`ResolvedEntityProfile`)
- `src/worldassembly/resolver.py` (`WorldAssemblyResolver`, where module-level spawn-zone data
  would need to be threaded through)
- `src/domains/campaigns/orchestrator.py` (`_scatter_catalog_entities()`, to be deleted)

## Assumptions / Open Questions
- Whether spawn-zone data should be authored per-module (declarative, in each
  `WorldModuleSpec`'s own YAML) or derived procedurally (e.g. from each module's own region bounds,
  already computed by `WorldCompiler.compile()`) is the central design question — not decided here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
