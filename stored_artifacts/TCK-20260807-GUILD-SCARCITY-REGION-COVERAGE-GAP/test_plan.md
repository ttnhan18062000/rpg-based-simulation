---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP
artifact_type: test_plan
tags: [strategy, simulation-quality]
---

# Test Plan: TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP

## New/updated tests

**`tests/unit/strategic/test_opportunities.py`**

| Test | Behavior verified |
|---|---|
| `test_resource_opportunities_river_ford_herb_patch` | An entity in `river_ford` with a `herb_patch` node in mock state gets a real `gather_resource` opportunity (positive coverage) |
| `test_resource_opportunities_deep_forest_and_survivor_outpost_no_resource_nodes` | An entity in `deep_forest` or `survivor_outpost` with no nodes in mock state correctly gets zero opportunities (accepted zero-content gap, not a false negative) |

**`tests/integration/content/test_resource_region_coverage_corpus.py`**

| Test | Behavior verified |
|---|---|
| `test_no_entity_of_any_role_spawns_in_an_unresolved_region_corpus_wide` (new) | Every entity of every role, corpus-wide, spawns only in a region with either real `source_region_tags` coverage or an explicit `_ACCEPTED_ZERO_CONTENT_REGIONS` entry — no unresolved disposition gaps remain |
| `test_no_hero_role_entity_spawns_in_an_uncovered_region_corpus_wide` (pre-existing, unchanged) | Still passes — hero-only scope preserved for its own `AdventureDecisionPhase`-specific purpose |

## Regression coverage
- `tests/unit/strategic/` (full suite, 8 files) — scorer-level and opportunity-provider tests.
- `tests/unit/core/test_registry_bridge.py` — `CatalogToResourceRegistryAdapter` precedence tests.
- `tests/architecture/test_guild_action_dormancy.py` — confirms the dispatch-site guard from the
  sibling ticket is unaffected by this content-only change.
- `tests/unit/world/` (full suite) — `GuildAction`/guild-pipeline/guild-intel tests.
- `tests/unit/quest/` (full suite) — `QuestGenerator`/pressure-weighting tests, since scarcity
  feeds `QuestPressureProfile`.
- `tests/integration/content/` (full directory).

## Real-kernel-adjacent verification
Directly computed `GuildAction.visit()`'s scarcity formula for an entity in `river_ford` with a
`herb_patch` node at `remaining_charges=2, max_charges=10`: before this fix, `scarcity=0.0`
(node's kind not in `river_ford`'s coverage, so `ratios` stayed empty); after, `scarcity=0.8`
(correctly reflects the real charge ratio).

## Results
`tests/unit/strategic/` + `tests/unit/core/test_registry_bridge.py` +
`tests/architecture/test_guild_action_dormancy.py` + `tests/unit/world/` + `tests/unit/quest/` +
`tests/integration/content/`: 633/633 pass. No pre-existing or new failures.

## Out of scope for this test plan
- `bandit_road`/`goblin_camp`/`wolf_den`'s own existing accepted-gap tests — unchanged, already
  covered by the original audit's own test suite.
- Any change to `ResourceOpportunityProvider`, `GuildAction.visit()`'s own computation logic, or
  `ResourceNodeState` — per this ticket's own Scope, only the catalog content and test coverage
  were touched, no engine code.
