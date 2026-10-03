---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION
phase: done
date: 2026-09-09
tags: [world, content, architecture]
---

# TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION

## Title
`WorldEntitySpawner.spawn_from_context()` has no per-entity spatial placement — fix the spawner, not just Campaign's own workaround

## Status
DONE

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
- [x] `ResolvedEntityProfile` (or equivalent) carries real per-entity spatial data derived from
      its originating module. — New `spawn_position: Optional[Tuple[float, float]]` field, resolved
      in `CompileProfileResolver.resolve()` from the population's own authored `spawn_region` +
      that region's real `bounds` (both already threaded through module assembly — no new schema).
- [x] `WorldEntitySpawner.spawn_from_context()` places entities at distinct, module-appropriate
      positions instead of a single shared `default_position`. — One-line change: reads
      `profile.spawn_position` when set, falls back to `default_position` only when `None`.
      Deterministic de-confliction added (peer review: collisions are the normal case, not an edge
      case, given `compiler.py:270-272`'s own "multiple populations may share one spawn_region"
      comment — confirmed against real corpus content, see investigation.md).
- [x] A real Campaign episode re-run (same shape as
      `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own verification) shows zero
      `LAW-OCCUPANCY-COLLISION` violations and a plausible event mix, achieved via real placement
      rather than the scatter workaround. — Re-ran
      `test_real_campaign_episode_event_stream_is_plausible_not_degenerate` unmodified: 0
      `InvariantViolation`, `combat_initiated >= 3`, `cooperation_event` share `< 50%` — all pass,
      now achieved via real authored placement.
- [x] `CampaignOrchestrator._scatter_catalog_entities()` is deleted. — Method and its call site
      removed; `_build_initial_state()` uses `catalog_result.state.entities` directly.
- [x] No regression in `tests/integration/worldassembly/`, `tests/unit/certification/`,
      `tests/integration/certification/`, or `tests/unit/domains/campaigns/`/
      `tests/integration/campaigns/`. — 354 passed, 0 failed (scoped run, `-m "not slow and not
      extra_slow"`); plus the 4 `@pytest.mark.slow` real-episode tests in
      `test_catalog_entity_spawn_wiring.py` run separately, all passing.

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
- ~~Whether spawn-zone data should be authored per-module (declarative...) or derived
  procedurally...~~ **Resolved during Investigate**: it's both, and both already existed —
  `PopulationSpec.spawn_region` (declarative, authored) anchors into `RegionSpec.bounds`
  (procedural geometry, already computed during module assembly). No new authoring format was
  needed; see investigation.md.
- `EntitySpawnContext.spawn_region` (a *different*, pre-existing field on the spawn context, unlike
  the new `ResolvedEntityProfile.spawn_position`) was checked before adding a new field, per peer
  review — confirmed genuinely dead (never set to a real value, and nothing reads it even if it
  were). Recorded as an 8th instance in `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` rather
  than fixed here.
- Population `count` still does not expand into multiple individually-spawned entities (a
  pre-existing, separate gap, not this ticket's scope) — filed as
  `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` since it has real, live
  consumers (`RegionState.population_cohorts` feeds demographics migration/camp/reproduction logic
  and diverges from actual spawned entity count whenever `count != 1`).

## Implementation Notes
Full investigation, plan, and test plan recorded in
`staging_artifacts/TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION/`. Approach reviewed and
approved by `rpg-feature-planning` before implementation, with two required additions folded in:
deterministic de-confliction, and filing (not just flagging) the count-vs-declared-population
divergence.

1. **`src/worldassembly/models.py`** — added `spawn_position: Optional[Tuple[float, float]] = None`
   to `ResolvedEntityProfile`. Default `None` keeps every existing profile (test-constructed or
   from the legacy path) backward compatible.
2. **`src/worldassembly/resolver.py`** — two new pure module-level helpers,
   `_hash_point_in_bounds()` (deterministic candidate point from a key + region bounds, no RNG) and
   `_resolve_spawn_position()` (candidate + deterministic de-confliction via a fixed probe-offset
   sequence, falling back to the claimed candidate only for a genuinely degenerate region too small
   to de-conflict). `CompileProfileResolver.resolve()` now builds a `region_bounds` map from
   `spec.regions` (extending its existing town-ownership loop) and a `claimed_positions` dict local
   to that one `resolve()` call (never module/instance state, keeping position resolution a pure
   function of that call's `spec`), and passes `spawn_position=_resolve_spawn_position(...)` into
   both `ResolvedEntityProfile` construction branches.
   - Caught and fixed a real bug in my own first draft during manual verification: the initial
     `_hash_point_in_bounds` formula used `width = max(max_x - min_x, 1)` combined with
     `% (width + 1)`, which for a degenerate single-point region (`min_x == max_x`) could produce a
     candidate one unit past `max_x`/`max_y`. Fixed to `num_positions = max_x - min_x + 1` (always
     `>= 1`, since `RegionSpec.validate_bounds` already guarantees `min_x <= max_x`), with a
     regression test (`test_degenerate_single_point_region_never_exceeds_bounds`) added so it can't
     regress silently.
   - **Peer review, pre-merge:** the exhausted-probe fallback (when de-confliction genuinely can't
     find a free tile) silently reintroduced the exact `LAW-OCCUPANCY-COLLISION` condition this
     ticket exists to eliminate — a real, unobservable degradation path, not acceptable given this
     entire batch has been about conditions that were real, harmful, and unobservable. Added a
     `logger.warning` naming the region, the key, and the collision, with a regression test
     (`test_exhausted_probe_sequence_logs_a_warning`) confirming it fires. Also corrected the
     fallback's own comment, which claimed exhaustion only happens in a "degenerate region too
     small" — false: the probe set is 12 fixed offsets covering only a +/-2 box (13 candidates), so
     exhaustion is also reachable in a large region whose local neighborhood around one hash point
     is saturated, with thousands of free tiles elsewhere in the same region.
3. **`src/worldassembly/entity_spawner.py`** — one-line change in `spawn_from_context()`'s loop:
   `position = profile.spawn_position if profile.spawn_position is not None else default_position`.
   No signature change.
4. **`src/domains/campaigns/orchestrator.py`** — deleted `_scatter_catalog_entities()` (the
   explicitly-labeled interim workaround) and its call site; `_build_initial_state()`'s
   no-alive-carry-forwards branch now uses `catalog_result.state.entities` directly.
5. **`docs/world/assembly_contract.md`** — added a "Spatial placement" subsection to the Entity
   Spawner Contract describing the new `spawn_position`-from-`spawn_region` resolution and
   de-confliction, replacing the previously-undocumented single-`default_position` behavior.
6. **`tickets/done/TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING.md`** — added a dated addendum
   (matching this repo's own established correction-paragraph precedent for closed tickets) noting
   its "NOT valid for any spatial measurement" caveat no longer applies, re-verified via the same
   real 70-tick evidence that ticket originally used.
7. **Sibling findings, filed rather than silently fixed or silently dropped**, both per peer review:
   `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` (new standard-tier ticket)
   and an 8th instance recorded on `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`
   (`EntitySpawnContext.spawn_region`).

## Test Summary
- New unit tests, `tests/unit/worldassembly/test_resolver.py` (`TestHashPointInBounds`,
  `TestResolveSpawnPosition`, 12 new tests): determinism, in-bounds guarantee, the degenerate
  single-point regression case, unknown/empty `spawn_region` → `None`, real de-confliction (forced
  collision via monkeypatch, and a genuinely degenerate 1x1 region exhausting the probe sequence
  without raising), confirming the pure-function-per-call contract (no state leaks across separate
  `resolve()`-equivalent calls), and (post-review) confirming the exhausted-probe fallback logs a
  `logger.warning` naming the region and key.
- New integration tests, `tests/integration/worldassembly/test_world_entity_spawner.py` (3 new):
  `spawn_position` used when set, `default_position` fallback when unset, and a **real-corpus**
  regression (`bandit_road_trade_pressure.yaml`, which has exactly one region and two population
  refs, so both necessarily resolve to the same `spawn_region` today) confirming de-confliction
  actually engages on real content, not only a synthetic test case.
- Real Campaign episode re-verification: all 4 tests in
  `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` (3 `@pytest.mark.slow`) re-run
  unmodified except docstring updates removing the now-deleted `_scatter_catalog_entities()`
  reference — all pass, including the zero-`LAW-OCCUPANCY-COLLISION` and plausible-event-mix checks
  the ticket's own AC requires, now achieved via real placement.
- Scoped regression: `pytest tests/integration/worldassembly/ tests/unit/certification/
  tests/integration/certification/ tests/unit/domains/campaigns/ tests/integration/campaigns/
  tests/unit/worldassembly/ -m "not slow and not extra_slow"` — 354 passed, 0 failed.
- Sanity check (not required by this ticket's own scope, run anyway since `region_bounds`
  construction touches the same `spec.regions` loop demographics indirectly depends on via
  `RegionState`): `tests/unit/world/test_demographics.py tests/integration/scenarios/
  test_demographics.py` — 61 passed, 0 failed.
- `tools/validate_frontmatter.py` clean on this ticket and the amended
  `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING.md`.
- `make knowledge-index-update` run after the `docs/` change.

## Files Changed
- `src/worldassembly/models.py` — new `spawn_position` field
- `src/worldassembly/resolver.py` — `_hash_point_in_bounds()`, `_resolve_spawn_position()`,
  `region_bounds`/`claimed_positions` construction and wiring in `CompileProfileResolver.resolve()`
- `src/worldassembly/entity_spawner.py` — `spawn_from_context()` position fallback
- `src/domains/campaigns/orchestrator.py` — `_scatter_catalog_entities()` and its call site deleted
- `docs/world/assembly_contract.md` — new "Spatial placement" subsection
- `tests/unit/worldassembly/test_resolver.py` — 11 new unit tests
- `tests/integration/worldassembly/test_world_entity_spawner.py` — 3 new integration tests
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` — 1 docstring update (stale
  `_scatter_catalog_entities()` reference removed), no assertion changes
- `tickets/done/TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING.md` — dated addendum
- `tickets/todos/TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT.md` — 8th instance recorded
- `tickets/todos/TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE.md` — new ticket
- `staging_artifacts/TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION/` — investigation.md,
  plan.md, test_plan.md

## Completion Summary
Real per-entity spatial placement now lands in `WorldEntitySpawner` itself, not a Campaign-local
workaround. The ticket's own "central design question" turned out to already be answered by
existing data: `PopulationSpec.spawn_region` (declarative, already authored per-module and already
threaded through assembly) anchors into `RegionSpec.bounds` (real per-module geometry, already
computed) — no new authoring schema was needed. Two required additions came out of peer review
before implementation began: deterministic de-confliction (multiple populations sharing one
`spawn_region` is the documented normal case, confirmed against real corpus modules where it's
unavoidable — a plain hash-to-point would have shipped a latent collision bug), and filing rather
than merely flagging a real, consumer-backed divergence between declared and spawned population
counts. `CampaignOrchestrator._scatter_catalog_entities()` is deleted; the real Campaign episode
re-verification (same shape as `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own evidence)
confirms zero `LAW-OCCUPANCY-COLLISION` and a plausible event mix via real placement. One real bug
was found and fixed in my own first implementation draft (a degenerate-region off-by-one in the
hash formula) via direct manual verification before it reached a committed test — caught early
enough to add a permanent regression test rather than ship it.

**Addendum (2026-09-11):** this ticket fixed real placement for the episode-0 catalog-spawn path
only. `CampaignOrchestrator._build_initial_state()`'s OTHER branch — survivor-reconstruction for
episode N>0 — never touches `WorldEntitySpawner` at all and still places every reconstructed
survivor at the identical `(0.0, 0.0)` default, confirmed at real scale (13 of 16 survivors
colliding, tripping a real `LAW-SPAWN-OCCUPANCY` violation) during
`TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`'s own real multi-episode investigation. Never
exercisable before now — Campaign mode had zero entities, so zero survivors, until this ticket's
own sibling (`TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`) and this ticket landed. Filed as
`TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`, the other half of this same
underlying gap.
