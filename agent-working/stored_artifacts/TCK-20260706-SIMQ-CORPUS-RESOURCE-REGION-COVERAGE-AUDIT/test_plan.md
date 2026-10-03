---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT
artifact_type: test_plan
tags: [simulation-quality, world, resource-registry, corpus]
---

# Test Plan — TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT

## Regression Surface

Existing tests that must keep passing after any option (a) catalog changes (additive
`metadata.source_region_tags` edits to `data/content/world/resources.yaml`) and any option (c)
doc-only dispositions:

**Unit — resource opportunity gating (direct):**
- `tests/unit/strategic/test_opportunities.py` — all tests, especially:
  - `test_resource_opportunities_basic`, `test_resource_opportunities_with_blocker` (near_forest/
    old_mine baseline, unaffected by additive changes)
  - `test_resource_opportunities_hometown_wood_node`, `_herb_patch` (already-fixed hometown pair,
    must stay green)
  - `test_resource_opportunities_mountain_pass_zone_iron_vein`, `_frost_shard_cluster` (already-fixed
    pair, the exact pattern any new fix's positive-coverage test should follow)
  - `test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes` (tests
    zero-opportunities behavior when `mock_state.resource_nodes` is empty — unaffected by catalog
    tag changes, this is a live-state-shape test not a catalog test)
  - `test_resource_opportunities_old_mine_iron_vein` (legacy_id-fallback baseline)
  - `test_resource_opportunities_orc_stronghold_tag_gap` (currently asserts ZERO — **must be
    rewritten**, not merely "kept passing," if `orc_stronghold` gets an option (a) fix; see New Tests
    Required)

**Unit — registry/catalog parity (subset-style, tolerant of additive changes):**
- `tests/unit/core/test_registry_bridge.py` — asserts `"near_forest" in res_wood.source_region_tags`,
  `"old_mine" in res_iron.source_region_tags`, `"hometown" in res_wood.source_region_tags`, etc.
  (`in`-checks, not equality) — additive tags do not break these.
- `tests/unit/core/test_registry_parity.py::test_production_catalog_parity` — asserts
  `leg_tags_set.issubset(cat_tags_set)` (legacy heuristic tags must remain a subset of catalog tags) —
  additive catalog tags only grow the superset side, subset relation is preserved.
  `test_catalog_registry_projection_parity` — presence-only check, unaffected.
- `tests/unit/content/test_adapter_heuristic_reporting.py` — synthetic fixtures, does not read the
  real catalog file, unaffected.
- `tests/integration/content/test_registry_projection_parity.py` — synthetic fixtures, unaffected.

**Integration — world compilation / e2e smoke (node-count assertions, not tag-content):**
- `tests/integration/worldassembly/test_e2e_smoke.py::test_smoke_urban_political_compiles_to_authoritative_state`
  — asserts `resource_node_count >= 3`; unaffected by tag-only changes but should be re-run since it
  touches the same content family (`urban_political`/`trading_company_hub`).
- `tests/unit/worldassembly/test_corpus_diversity.py` (`test_population_stability[*]`) — generic
  OFF-flag population-floor guard across the corpus; unaffected by resource-tag changes but should be
  re-run given this ticket touches every world's audited region set.
- `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py` — ON-flag population
  floor for the one other routing-capable world; unaffected but in the blast radius of "every world
  audited."

**Quest generation (the latent `GuildAction` consumer, STRAT-244):**
- `tests/unit/quest/test_quest_generation.py::test_quest_generation_favors_hunt_under_high_trauma`,
  `::test_quest_generation_favors_gather_under_high_scarcity` — should stay green; this ticket does
  not touch `GuildAction.visit()` or `QuestGenerator`, only the catalog file it reads from at
  call-time. No expected impact, but the scarcity computation is a "read the real catalog at runtime"
  path, so worth a pass/fail check.

**Guild pipeline (unwired but directly-tested consumer):**
- `tests/unit/world/test_guild_pipeline.py::test_guild_visit_leads`,
  `::test_guild_visit_quests` — unaffected (uses `iron`/synthetic node kinds, not the regions this
  ticket touches), but in the same file family as the `GuildAction` finding above.

**Perf budget (P0, must not regress):**
- `tests/perf/test_phase3_adventure_decision_budget.py::test_phase3_adventure_decision_perf_budget`
  (STRAT-225, P0) — `AdventureDecisionPhase` calling `get_opportunities()` per hero per tick; additive
  tag growth on `wood_node`/`iron_vein`/etc. could marginally increase the opportunity list size for
  entities already covered, but the function caps output at 5 (`resources.py:97`) and this ticket's
  recommended fix path never touches `resources.py`/`registries.py` source — expected unaffected, but
  P0 status means this must be explicitly re-run, not assumed.

## New Tests Required

Per acceptance criteria — one entry per required new/modified test:

1. **`test_resource_opportunities_orc_stronghold_tag_gap` rewrite (IF `orc_stronghold` gets an option
   (a) fix)**
   - Category: unit (regression rewrite, not new)
   - Verifies: a hero (or any entity) standing in `orc_stronghold` with an `iron_vein`/`wood_node`
     node present now DOES receive a `gather_resource` opportunity (mirrors the exact
     `test_resource_opportunities_mountain_pass_zone_iron_vein` pattern already in the file for the
     already-fixed precedent)
   - Location: `tests/unit/strategic/test_opportunities.py` (same file, same function name — do not
     leave the old "expects zero" assertion in place per its own docstring's explicit instruction)

2. **New positive-coverage tests for each region receiving an option (a) fix** (e.g.
   `sacred_grove`/`healing_flower_patch`+`spirit_wisp`, `swamp_border_territory`/`wood_node`+
   `herb_patch`, `haunted_battlefield`/`spirit_wisp`, `trading_hometown`/`iron_vein` — exact set
   depends on which the Plan phase decides to fix)
   - Category: unit
   - Verifies: entity standing in the newly-covered region with the relevant node present receives a
     non-empty `gather_resource` opportunity list; existing coverage for that same kind's other
     regions (e.g. `wood_node`'s `near_forest`/`hometown`) is unaffected (assert both old and new tags
     present via `in`-checks, not equality, matching `test_registry_bridge.py`'s style)
   - Location: `tests/unit/strategic/test_opportunities.py`

3. **Explicit-zero regression guards for each region receiving an option (c) accepted-gap
   disposition** (e.g. `bandit_road`, `goblin_camp`, `wolf_den` if confirmed intentional)
   - Category: unit (anti-drift guard)
   - Verifies: entity standing in the region continues to receive zero `gather_resource`
     opportunities — codifies the "this absence is intentional, not a bug" contract so a future
     catalog edit that accidentally starts covering it is caught and forces a conscious doc update
     (mirrors the existing `test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes`
     pattern, but keyed on the *disposition decision*, not merely "no node present in mock state")
   - Location: `tests/unit/strategic/test_opportunities.py`

4. **Corpus-wide region-coverage audit test (architecture guard, new)**
   - Category: architecture guard / integration
   - Verifies: programmatically re-derives this ticket's live audit table (glob
     `data/worlds/*/resolved/world.resolved.yaml`, build the real `ResourceRegistry` projection,
     diff spawn regions against covered tags) and asserts the **hero-role** uncovered set is empty
     corpus-wide — turning this ticket's most safety-critical live finding ("zero hero-role gaps
     today") into a durable regression guard rather than a one-time investigation fact. Optionally
     also assert the **all-role** uncovered set exactly equals the documented/accepted set (fails
     loudly if a new world is added with a region nobody has dispositioned yet — the exact "corpus
     grew silently" drift this investigation found relative to the parent ticket's stale table)
   - Location: new test, e.g. `tests/integration/content/test_resource_region_coverage_corpus.py` or
     alongside `tests/unit/worldassembly/test_corpus_diversity.py` (match existing corpus-wide-guard
     file placement convention)

5. **`GuildAction` dormancy guard (optional but recommended, anti-drift)**
   - Category: architecture guard
   - Verifies: `GuildAction.visit()` (or its `visit` symbol) is not referenced by any dispatcher/
     pipeline-phase module under `src/engine/` or `src/domains/` — if this ever starts failing (i.e.
     `GuildAction` gets wired into a live phase), it's a signal that the dormant scarcity-computation
     risk identified in §4 of the investigation has gone live and needs its own coverage-gap
     evaluation, not silently inheriting this ticket's "currently dormant, no live impact" conclusion
   - Location: `tests/architecture/` (match existing architecture-guard placement, e.g. alongside any
     existing dispatcher-wiring guards) — lower priority than items 1-4, include only if Plan
     confirms this is worth codifying vs. just documenting

## Scoped Pytest Commands

```bash
# Core resource-opportunity gating tests (primary regression surface)
.venv/bin/python3 -m pytest tests/unit/strategic/test_opportunities.py -v

# Registry/catalog parity (must remain subset-tolerant after additive tag changes)
.venv/bin/python3 -m pytest tests/unit/core/test_registry_bridge.py tests/unit/core/test_registry_parity.py -v

# Quest generation (latent GuildAction consumer, STRAT-244)
.venv/bin/python3 -m pytest tests/unit/quest/test_quest_generation.py tests/unit/world/test_guild_pipeline.py -v

# World compilation / corpus population-floor smoke (touches every audited world)
.venv/bin/python3 -m pytest tests/integration/worldassembly/test_e2e_smoke.py tests/unit/worldassembly/test_corpus_diversity.py tests/unit/worldassembly/test_hero_guild_routing_population_stability.py -v

# P0 perf budget guard (STRAT-225) -- must not regress
.venv/bin/python3 -m pytest tests/perf/test_phase3_adventure_decision_budget.py -v

# New corpus-wide coverage guard (once authored)
.venv/bin/python3 -m pytest tests/integration/content/test_resource_region_coverage_corpus.py -v

# Corpus-wide dry-run diff against grade anchors -- required by AC5, run after any catalog/content change
make evaluate
```

Never run the full `pytest tests/` suite — all commands above are scoped to the world/resource/quest
domains this ticket touches.

## Anti-Drift Test Guards

- **`test_resource_opportunities_orc_stronghold_tag_gap`'s current "expects zero" assertion is itself
  an anti-drift guard for the *pre-fix* state** — if it starts failing without a corresponding
  deliberate rewrite, that means the catalog changed unexpectedly (e.g. a `preferred_biomes` promotion
  script or an unrelated ticket's edit) rather than through this ticket's planned decision. Any
  implementation must rewrite it deliberately, not let it fail silently.
- **The subset-style assertions in `test_registry_parity.py`/`test_registry_bridge.py` are the guard
  against a non-additive mistake** — if a future edit ever *replaces* rather than *extends* a
  `source_region_tags` tuple, `leg_tags_set.issubset(cat_tags_set)` would fail immediately, catching
  regressions in `near_forest`/`old_mine`/`hometown`/`mountain_pass_zone` coverage that a
  region-scoped test alone might miss.
- **New corpus-wide coverage test (New Tests Required item 4) is the key guard against the exact drift
  this investigation found** — the parent ticket's table went stale as 6 new worlds were added without
  anyone re-running the audit; a programmatic, live-glob-based test (not a hardcoded world list)
  prevents that from recurring silently.
- **`GuildAction` dormancy guard (item 5)** — protects against silently promoting a dead-code
  consumer to live without anyone re-evaluating whether its region gaps still matter once it's
  reachable.
- **Do not accidentally assert exact-equality on any `source_region_tags` tuple** in a new or modified
  test (e.g. `res_wood.source_region_tags == (...)`) — every precedent test uses `in`-membership
  checks specifically so future additive fixes for *other* regions don't retroactively break tests
  written for *this* ticket's regions. Any new test written under this ticket must follow the same
  convention.
