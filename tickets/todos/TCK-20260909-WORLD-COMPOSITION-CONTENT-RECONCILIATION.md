---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION
phase: open
date: 2026-09-09
tags: [architecture, content]
---

# TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION

## Title
Reconcile 8 diverged world-composition content pairs (not a mechanical move), then retire `data/content/world_compositions/`

**Retitled 2026-09-12** (was "Consolidate `data/content/world_compositions/` into `data/worlds/`
per the existing ADR") — the original title read as a refactor. Real investigation (below) found
it is a content reconciliation requiring 8 separate per-world "which module set is authoritative"
decisions, with a directory cleanup only after those are made. Pulled out of the Batch-E-adjacent
consolidated PR for exactly this reason — see the 2026-09-12 findings block.

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`docs/architecture/world_repository_layout.md`'s own ADR (`ACCEPTED` status) is explicit:
*"Rather than creating separate directories for raw templates, specs, and compositions, we will
maintain the existing unified world repository root at `data/worlds/`... The root source file
inside a world folder is always `world.yaml`. The schema version within the YAML determines how
the repository indexes it"* — and names `worldcomposition.v1` as one of the accepted schema
versions indexed there. `data/content/world_compositions/*.yaml` (read by `ScenarioSetupResolver`,
default `compositions_dir`) is the anomaly this ADR already argued against, not `data/worlds/`.

**Concrete evidence the split causes real harm, found during
`TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`**: `frontier_living_world` already has two
diverged copies — `data/worlds/frontier_living_world/world.yaml` (7 modules via the richer
`module_refs` form, including `trading_company_hub`, plus `information_source_profiles`/
`pending_information_responses`) vs. `data/content/world_compositions/frontier_living_world.yaml`
(6 modules via the plain `modules:` shorthand, missing `trading_company_hub` and both
Pattern-6 fields). Two sources of truth for the same `world_id`, indexed by two different readers,
already drifted with nothing to catch it.

Also related: `TCK-20260607-STRICT-MODE-PRODUCTION` records that
`CatalogRepository("data/content").load_all(strict=True)` raises precisely because
`world_compositions/*.yaml` are non-catalog files sitting inside the catalog content directory —
the split was already a known irritant before this ticket's own finding.

**Scope note (user decision, 2026-09-09)**: `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`
deliberately does NOT do this migration — it only points `ScenarioSetupResolver`'s own
`compositions_dir` at `data/worlds/` for Campaign's own resolution (and taught
`ScenarioSetupResolver._load_composition()` to accept both the flat `<id>.yaml` and the nested
`<id>/world.yaml` layout, trying nested first). This ticket is the actual repo-wide consolidation
the ADR calls for — moving every `data/content/world_compositions/*.yaml` into `data/worlds/<id>/
world.yaml` (or confirming they already have a `data/worlds/<id>/` counterpart, per
`frontier_living_world`'s own precedent) and retiring the `data/content/world_compositions/`
directory entirely, updating every caller (not just Campaign) to use the unified layout.

**2026-09-12 pre-implementation check — this is NOT mechanical, do not treat it as a batch-sized
refactor.** Before writing any migration, ran the cheap check peer review asked for: diffed every
`data/content/world_compositions/<id>.yaml` against its `data/worlds/<id>/world.yaml` counterpart.

- **8 of 9 pairs diverge**, not just `frontier_living_world`: `dungeon_crawl`, `frontier_extended`,
  `frontier_living_world`, `highland_traverse`, `swamp_border_world`, `urban_political`,
  `wilderness_survival` (all 7 top-level `.yaml` files), plus `generated_frontier_3_42` (one of the
  two files under the `generated/` subdirectory).
- **Only `simq_scale_stress_seed42` is byte-identical.**
- **Neither side is consistently the superset.** `dungeon_crawl` example, spelled out concretely
  (the kind of divergence, not a one-off formatting difference): `data/worlds/dungeon_crawl/
  world.yaml` has 3 modules (`goblin_camp_conflict`, `old_mine_resource_loop`,
  `scalable_bandit_camp`) where `data/content/world_compositions/dungeon_crawl.yaml` has only 1
  (`scalable_bandit_camp`); the two also disagree on `danger_scale` (2 vs. 4), and `data/worlds/`
  has a `faction_tension_overrides` block the other side lacks entirely. This is the same shape as
  every one of the 8 divergent pairs — a genuine per-world "which module set/settings are
  authoritative for this world" content decision, not a rename or a formatting reconciliation. A
  rule like "prefer the richer file" does not resolve this, since richness isn't consistently on
  one side.
- **Production is unaffected either way**: `CatalogScenarioStateBuilder`'s only real (non-test)
  caller is `CampaignOrchestrator`, which unconditionally overrides `compositions_dir=Path(
  "data/worlds")` — no fallback, no conditional. Nothing in live production code ever reads the
  default `data/content/world_compositions/` path.
- **But two real tests depend on the default, and this is the part most likely to be missed**:
  `tests/integration/scenarios/test_scenario_catalog_matrix.py` and `tests/integration/scenarios/
  test_scenario_setup_resolver.py` both construct `ScenarioSetupResolver()` with no
  `compositions_dir` override, relying on the current default (`data/content/world_compositions/`).
  Redirecting that default to `data/worlds/` — the naive "just point it at the unified layout"
  fix — would silently change what these tests load (the simpler 6/7-module version today, the
  richer/diverged version after) and potentially what they assert on. Anyone picking this ticket up
  must hit this before starting the redirect, not discover it after.

**Disposition**: pulled out of the Batch E-adjacent consolidated PR (`#174`) for exactly this
reason — 8 separate content-authority decisions do not belong inside a batch refactor PR. To be
scoped as its own initiative once the batch closes. No per-world detailed diff dump was produced
beyond the `dungeon_crawl` example above (peer review confirmed the list-plus-shape is sufficient
to route later; a full dump can be regenerated cheaply when this is picked up, via the same diff
loop over `data/content/world_compositions/*.yaml` vs. `data/worlds/<id>/world.yaml`).

## Scope
- **For each of the 8 diverged pairs (list in the 2026-09-12 findings block above), decide per-
  world which content is authoritative.** Confirmed 2026-09-12: NOT a mechanical "prefer the
  richer file" rule — neither side is consistently the superset. This is a real content/design
  decision per world, likely requiring peer/user input for at least some of the 8, not something to
  resolve unilaterally during Investigate.
- Inventory every file under `data/content/world_compositions/` and check whether a
  `data/worlds/<id>/world.yaml` counterpart already exists (mostly already done, see findings
  block — `simq_scale_stress_seed42` is the one byte-identical pair; confirm no new drift since
  2026-09-12 before treating the inventory as still current).
  - If it matches: delete the `data/content/` copy, no content change needed.
  - If it diverges: apply the per-world authoritative decision above, reconcile.
  - If no `data/worlds/<id>/` counterpart exists: create one, migrating the content.
- **Before redirecting `ScenarioSetupResolver`'s default `compositions_dir`, update
  `tests/integration/scenarios/test_scenario_catalog_matrix.py` and `tests/integration/scenarios/
  test_scenario_setup_resolver.py`** (both rely on the current default, unoverridden) to account
  for whatever the reconciled content ends up being — confirmed 2026-09-12 this is the part most
  likely to be missed, not an incidental regression check.
- Update every caller of `ScenarioSetupResolver`/`CatalogScenarioStateBuilder` that currently
  relies on the default `compositions_dir` (`data/content/world_compositions/`) to use the unified
  `data/worlds/` layout instead — including reverting `CampaignOrchestrator`'s own explicit
  `compositions_dir=Path("data/worlds")` override back to the (now-unified) default, once the
  default itself points at `data/worlds/`.
- Decide whether `ScenarioSetupResolver._load_composition()`'s dual-layout fallback (nested-first,
  flat-second — added by `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` specifically to make
  the Campaign-only override safe) should be simplified back to nested-only once every caller is
  migrated, or kept as permanent back-compat.
- Retire `data/content/world_compositions/` once nothing reads from it — this step alone (given
  production already never reads the default) is the "different and much smaller task" it could
  reduce to if the 8 content decisions are instead resolved by deferring/documenting rather than
  reconciling; not pre-judged here.

## Out of Scope
- Any Campaign-specific entity-spawn logic — already implemented and closed in
  `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`.
- Consolidating the "legacy" `build_scenario_state()`/`ArenaInjector` certification path or
  `V2EngineManager`'s own manual spawn logic into this unified layout — a separate, larger
  initiative the user explicitly declined to bundle into the Campaign-mode fix; may be worth
  revisiting once this ticket lands, but not decided here.

## Acceptance Criteria
- [ ] Every world composition has exactly one authoritative source under `data/worlds/<id>/
      world.yaml`; `data/content/world_compositions/` is empty or removed.
- [ ] Every caller of `ScenarioSetupResolver` uses the unified layout, verified by a real test.
- [ ] Each of the 8 diverged pairs has a recorded, evidenced per-world authoritative-content
      decision (not a blanket "richer file wins" rule — confirmed 2026-09-12 that doesn't hold),
      with rationale for each.
- [ ] `test_scenario_catalog_matrix.py`/`test_scenario_setup_resolver.py` (the two tests relying on
      the un-overridden default) are updated to match whatever content the reconciliation settles
      on, confirmed passing.
- [ ] Full scoped regression across every consumer of `ScenarioSetupResolver`/
      `CatalogScenarioStateBuilder`/`WorldAssemblyResolver` passes.

## Related Tickets
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (found and worked around this split; this
  ticket is the real fix the ADR already called for)
- `TCK-20260607-STRICT-MODE-PRODUCTION` (documents the same split as a known irritant from a
  different angle — `CatalogRepository`'s own strict-mode content validation)

## Related Docs
- `docs/architecture/world_repository_layout.md` (the ADR this ticket implements)

## Related Stored Artifacts
None yet — created when this ticket is picked up.

## Related Code Areas
- `src/scenarios/resolver.py` (`ScenarioSetupResolver`, `_compositions_dir`)
- `src/domains/campaigns/orchestrator.py` (the Campaign-only override to revert once unified)
- `data/content/world_compositions/`, `data/worlds/`

## Assumptions / Open Questions
- ~~Whether every `data/content/world_compositions/*.yaml` file has a `data/worlds/<id>/`
  counterpart, or some are genuinely orphaned/never-migrated, is not yet known — real inventory
  work for this ticket's own Investigate phase.~~ **Resolved 2026-09-12**: every file has a
  counterpart (9/9); 8 diverge, 1 matches. See the findings block above.
- Which content is authoritative for each of the 8 diverged pairs is the real open question this
  ticket now exists to answer — deliberately not pre-judged, may need peer/user input per world
  rather than a blanket rule.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
