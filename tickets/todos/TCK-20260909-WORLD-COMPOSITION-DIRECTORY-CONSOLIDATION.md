---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION
phase: open
date: 2026-09-09
tags: [architecture, content]
---

# TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION

## Title
Consolidate `data/content/world_compositions/` into `data/worlds/` per the existing ADR

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

## Scope
- Inventory every file under `data/content/world_compositions/` and check whether a
  `data/worlds/<id>/world.yaml` counterpart already exists.
  - If it exists and matches: delete the `data/content/` copy, no content change needed.
  - If it exists and diverges (like `frontier_living_world`): decide which version is
    authoritative (the richer `data/worlds/` one, per this ticket's own precedent finding) and
    reconcile.
  - If no `data/worlds/<id>/` counterpart exists: create one, migrating the content.
- Update every caller of `ScenarioSetupResolver`/`CatalogScenarioStateBuilder` that currently
  relies on the default `compositions_dir` (`data/content/world_compositions/`) to use the unified
  `data/worlds/` layout instead — including reverting `CampaignOrchestrator`'s own explicit
  `compositions_dir=Path("data/worlds")` override back to the (now-unified) default, once the
  default itself points at `data/worlds/`.
- Decide whether `ScenarioSetupResolver._load_composition()`'s dual-layout fallback (nested-first,
  flat-second — added by `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` specifically to make
  the Campaign-only override safe) should be simplified back to nested-only once every caller is
  migrated, or kept as permanent back-compat.
- Retire `data/content/world_compositions/` once nothing reads from it.

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
- [ ] `frontier_living_world`'s own divergence is resolved with the richer version as the
      authoritative one (confirmed no content regression for existing consumers of the simpler
      version, if any exist beyond Campaign).
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
- Whether every `data/content/world_compositions/*.yaml` file has a `data/worlds/<id>/`
  counterpart, or some are genuinely orphaned/never-migrated, is not yet known — real inventory
  work for this ticket's own Investigate phase.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
