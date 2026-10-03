---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP
artifact_type: plan
tags: [strategy, simulation-quality]
---

# Plan: TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP

Per investigation.md: 1 genuine new tag-gap (`river_ford`), 2 zero-content regions extending an
already-reviewed disposition class (`deep_forest`, `survivor_outpost`), plus a role-scope gap in
the existing regression test now that `GuildAction` is a live, role-agnostic consumer.

## Steps

1. `data/content/world/resources.yaml`: additively extend `herb_patch`'s
   `metadata.source_region_tags` with `"river_ford"`.
2. `tests/unit/strategic/test_opportunities.py`: new positive-coverage test for `river_ford`
   (mirroring the `swamp_border_territory` test template); new zero-opportunity test for
   `deep_forest`/`survivor_outpost` (mirroring the `bandit_road`/`wolf_den` test template).
3. `tests/integration/content/test_resource_region_coverage_corpus.py`: add
   `_ACCEPTED_ZERO_CONTENT_REGIONS` frozenset (extending the existing 3-region accepted-gap list
   with `deep_forest`/`survivor_outpost`); add a new all-roles corpus-wide regression test
   (`test_no_entity_of_any_role_spawns_in_an_unresolved_region_corpus_wide`), keeping the existing
   hero-only test unchanged (still valid for its own AdventureDecisionPhase-specific purpose).
4. Docs: `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-244` update note),
   `docs/parity_ledger/town_resource.yaml` (new `TOWN-191` entry), `docs/guidelines/
   intentional_divergences.md` (§2.29 update note extending the accepted-gap list; new §2.32 for
   the `river_ford` tag-gap fix itself, following §2.28's exact precedent format).
5. Real-kernel-adjacent verification: manually compute `GuildAction.visit()`'s scarcity formula
   for an entity in `river_ford` before/after the fix, confirming the practical impact
   (0.0 → 0.8).
6. Run scoped tests (`tests/unit/strategic/`, `tests/unit/core/test_registry_bridge.py`,
   `tests/architecture/test_guild_action_dormancy.py`, `tests/unit/world/`, `tests/unit/quest/`,
   `tests/integration/content/`), doc-staleness check, Verify static precheck, Finalize.

## Acceptance criteria map

| Original AC | Disposition |
|---|---|
| investigation.md confirms exact regions/catalog entries and real practical impact | Done — river_ford (a), deep_forest/survivor_outpost (c); scarcity 0.0→0.8 confirmed |
| Catalog fix applied (or reasoned decision documented) | Done — river_ford fixed; deep_forest/survivor_outpost documented as extending the existing accepted-gap disposition, not needing a fix |
| strategic_cognition.yaml (STRAT-244) and town_resource.yaml updated | Done — STRAT-244 update note, new TOWN-191 |
| Scoped pytest passes | Done |
