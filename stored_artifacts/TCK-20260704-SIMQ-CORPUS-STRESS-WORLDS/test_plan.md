---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS
artifact_type: test_plan
tags: [simulation-quality, world, corpus, calibration]
---

# Test Plan — TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS

## Regression Surface

Existing tests that must keep passing (none of these should change behavior for any of the 9
existing corpus worlds — only gain new parametrized cases for the 3 new worlds):

**Unit — corpus diversity / world assembly**
- `tests/unit/worldassembly/test_corpus_diversity.py` — `test_entity_count_band`,
  `test_distinct_populated_factions`, `test_population_stability` (`@pytest.mark.slow`),
  `test_hazard_kind_completeness`, `test_module_family_anchored`. Existing parametrizations
  (`ANCHORED_WORLD_BANDS`, `EXPECTED_DISTINCT_POPULATED_FACTIONS`, `POPULATION_STABILITY_WORLDS`)
  must be extended additively — no existing dict/list entry changes value.
- `tests/unit/worldassembly/test_assembly.py` — region/faction/population merge-collision guards
  (`test_faction_tension_overrides_applied_after_merge`, `test_faction_tension_overrides_unknown_faction_raises`,
  etc.) — must still pass unmodified; directly relevant since the resolver's collision-raising
  behavior (`ValueError` on duplicate region id) is load-bearing for which modules this ticket can
  safely compose (see investigation.md's Anti-Drift Hazards).
- `tests/unit/worldbuilding/test_world_compiler.py` — `distinct_populated_factions` computation and
  general compile-report shape must be unaffected by new world content.
- `tests/unit/strategic/test_opportunities.py` — resource-opportunity provider tests; relevant if
  the resource-saturated/small-map world (gap b) introduces any new region/resource-node combination
  not already covered by `source_region_tags` (mirrors the `hero_guild_routing` precedent's Step 2
  finding).
- `tests/integration/worldassembly/test_real_content_world_modules.py` — `MODULE_MATRIX` catalog
  coverage; confirm no existing entry is broken by reuse of existing modules in new compositions.

**Simulation-quality — grade regression**
- `tests/simulation_quality/test_grade_regression.py` — `test_grade_anchor_file_exists_and_valid`,
  `test_grade_within_anchor_band`. `FAST_ANCHOR_KEYS` gains entries for the 3 new worlds; no existing
  key's anchor value changes.
- `tests/simulation_quality/test_quality_hub_integration.py`, `tests/simulation_quality/test_agency_scorer.py`,
  `tests/simulation_quality/test_information_scorer.py` — scorer-level tests; must be unaffected
  since this ticket adds no new scoring/emission logic.

**Content catalog / semantics (only if gap (b) touches resource-node region-tag coverage, or if
`FAC-012`/`INFRA-256` parity text is extended)**
- `tests/unit/content/test_catalog.py`, `tests/unit/content_semantics/test_semantics.py` —
  `hazard_immunities`/catalog round-trip guards, unaffected but cheap to run given this ticket
  touches faction/hazard-adjacent content.
- `tests/unit/faction/test_diplomacy.py` — `test_urban_political_seeded_tension_fires_tense_transition`
  and neighboring tests, if gap (c)'s world extends `FAC-012`'s evidence.

## New Tests Required

Per Acceptance Criteria (exact test additions depend on the planner's final world compositions and
world IDs — placeholders below use `<world_a>`/`<world_b>`/`<world_c>` for the many-factions,
resource-density, and large-scale-FACTION/INFORMATION worlds respectively):

1. **`test_entity_count_band[<world_a>]` / `[<world_b>]` / `[<world_c>]`**
   Category: unit (parametrized regression guard).
   Verifies: each new world's `world_compile_report.json::entity_count` falls within the band it
   was authored to fill (small for `<world_a>`/`<world_b>`, `frontier_extended`-comparable for
   `<world_c>`).
   Location: `tests/unit/worldassembly/test_corpus_diversity.py` — extend `ANCHORED_WORLD_BANDS`
   with 3 new entries (additive only).

2. **`test_distinct_populated_factions[<world_a>]`** (and, for completeness, `[<world_b>]`/`[<world_c>]`)
   Category: unit (numeric gap-closure proof — this is the AC's explicit "confirm numerically, not
   by eyeballing" requirement for world (a), Scope item 3).
   Verifies: `world_compile_report.json::distinct_populated_factions` equals the expected count
   (6-9 for `<world_a>`, whatever `<world_b>`/`<world_c>` actually measure) — must be filled in with
   the *actual measured* value after compile, not an assumed target.
   Location: `tests/unit/worldassembly/test_corpus_diversity.py` — extend
   `EXPECTED_DISTINCT_POPULATED_FACTIONS` (additive only).

3. **`test_population_stability[<world_a>]` / `[<world_b>]` / `[<world_c>]`** (`@pytest.mark.slow`)
   Category: unit / architecture guard (durable-state survival regression).
   Verifies: `>=60%` starting-entity-count alive floor at every 50-tick checkpoint through 300 ticks
   (or through the world's calibrated tick length if longer, per AC's "200-300 ticks" wording).
   Location: `tests/unit/worldassembly/test_corpus_diversity.py` — extend
   `POPULATION_STABILITY_WORLDS` (additive only; do **not** add to
   `tickets/todos/TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP.md`'s backfill list — these
   are new worlds, a distinct and smaller ask per investigation.md's Open Question).

4. **`test_hazard_kind_completeness[<world_a>]` / `[<world_b>]` / `[<world_c>]`**
   Category: unit (architecture guard — every `hazard_level > 0` region must declare `hazard_kind`
   or rely on a documented, already-immune native faction).
   Verifies: no region in the new world's resolved spec has `hazard_level > 0` without a
   `hazard_kind` (guards against Finding-3-class population collapse). Given investigation.md's
   module screening, this should pass cleanly if `undead_battlefield` (not `ruins_mystery_quest`)
   is the chosen `haunted_battlefield` variant, and no gap-(a)/(b) composition introduces an
   unscreened hazardous region.
   Location: `tests/unit/worldassembly/test_corpus_diversity.py` — extend `ANCHORED_WORLD_BANDS`'
   parametrization set (same list drives this test).

5. **Resource-node source-region-tag coverage spot-check (gap b only, contingent on findings)**
   Category: unit (targeted regression, mirrors `test_resource_opportunities_hometown_wood_node`).
   Verifies: every new region introduced by the resource-density world has at least one resource
   kind whose `source_region_tags` in `data/content/world/resources.yaml` actually covers it — only
   add this test if the investigation phase (or a Step-2-style check during implementation) finds a
   real gap; do not add a synthetic test for a gap that doesn't exist (per the `hero_guild_routing`
   precedent's "honest result" norm).
   Location: `tests/unit/strategic/test_opportunities.py`.

6. **Module-family / anchored-corpus sanity (no new test needed unless a genuinely new module is
   authored)**
   If UQ-1 resolves to "existing catalog content is sufficient" (investigation.md's finding
   supports this for all 3 gaps), `test_module_family_anchored`'s `NEWLY_ANCHORED_MODULES`/
   `STILL_UNANCHORED_MODULE` do not need changes — reused modules are already in that test's
   tracked set or irrelevant to it. If the planner instead authors a genuinely new module (only
   plausible for gap (a) if the entity-count-vs-region-count tension in investigation.md's Open
   Question resolves toward "author new, deliberately small population recipes"), add that module
   to `NEWLY_ANCHORED_MODULES` and verify `test_module_family_anchored` still passes.

## Scoped Pytest Commands

```bash
# Corpus-diversity regression guard (fast tests only first)
pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow" -q

# The @pytest.mark.slow population-stability cases, explicit (not swept by -m "not slow")
pytest tests/unit/worldassembly/test_corpus_diversity.py -k "<world_a> or <world_b> or <world_c>" -q

# Assembly/merge-collision guards (relevant to the region-id-collision Anti-Drift Hazard)
pytest tests/unit/worldassembly/test_assembly.py -q

# World-compiler and content-catalog round-trip
pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/content/test_catalog.py \
       tests/unit/content_semantics/test_semantics.py -q

# Resource-opportunity provider (only if gap (b) needs the spot-check test)
pytest tests/unit/strategic/test_opportunities.py -q

# Grade-anchor regression (fast keys; run the full suite including slow keys before final gate)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
pytest tests/simulation_quality/test_grade_regression.py -q   # full, before declaring done

# Faction-tension parity spot-check (only if FAC-012 extended for gap c)
pytest tests/unit/faction/test_diplomacy.py -q

# Full-corpus dry-run regression gate (AC's explicit requirement)
python3 tools/evaluate_simq.py --dry-run   # or: make evaluate --dry-run
```

Never run `pytest tests/` in full — scope to the domains above, matching this repo's Testing Rule.

## Anti-Drift Test Guards

- **`ANCHORED_WORLD_BANDS`/`EXPECTED_DISTINCT_POPULATED_FACTIONS`/`POPULATION_STABILITY_WORLDS` must
  gain exactly 3 new keys each (one per new world)** — a different delta (e.g. the 9 existing worlds'
  values silently changing, or more than 3 new keys appearing) indicates either an unintended edit to
  an existing world's entry or a duplicate/typo'd world id, and must be caught before merge. This
  directly guards the "do not touch existing worlds" Out-of-Scope item.
- **`test_distinct_populated_factions[<world_a>]` must assert the *measured* compiled value, not the
  6-9 target restated as fact** — if the chosen module composition actually yields, say, 5 or 10
  distinct populated factions instead of 6-9, that is a real AC failure to catch, not something to
  paper over by writing the test to match whatever the world happens to produce.
- **Grade-anchor key-count sanity check** (mirrors the `hero_guild_routing` precedent): before this
  ticket, `tests/simulation_quality/fixtures/grade_anchors.json` has 55 total keys (52 world-run
  entries + 3 metadata keys). After adding 3 new worlds × 3 seeds (assuming a single tick-count per
  world, matching the `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` 200t-default precedent unless a
  world-specific reason to deviate is documented), the file should gain exactly 9 new entries (64
  total) — a different delta signals a duplicate seed/tick-count or a miscounted world.
- **`make evaluate --dry-run` / `tools/evaluate_simq.py --dry-run` must show 0 regressions across the
  full existing 9-world (10 including `simq_routing_test`, 11 including `generated_frontier_3_42`)
  corpus, not just the 3 new worlds** — this is the direct check for the ticket's own AC "0
  regressions" wording and for the Out-of-Scope guarantee that no existing world's AGENCY/other
  pillar grade moves.
- **Region-id-collision guard**: if implementation attempts to compose
  `bandit_road_trade_pressure` + `scalable_bandit_camp`, or `wolf_den_near_forest` + `nomadic_herd`,
  `WorldAssemblyResolver.assemble()` raising `ValueError` at compile time is the correct, expected
  behavior (per investigation.md) — this must not be "fixed" by renaming a region id in a shared
  module file (`data/content/world_modules/*.yaml` is shared catalog content used by other worlds);
  the correct fix is choosing a non-colliding module pair.
- **Do not silently expand `moon_cult`/`dwarven_mine_clan` into "populated" status** — if any new
  world's composition uses `moon_cult_ruins`/`old_mine_resource_loop`, the test asserting
  `distinct_populated_factions` must reflect that these two declared-but-unpopulated factions do
  **not** count, catching an easy authoring mistake (assuming a module's `factions:` list equals its
  populated-faction contribution).
- **Tier-purity guard (manual, not automatable)**: if gap (a)/(b)'s stress-tier worlds gain any
  `faction_tension_overrides`/`information_source_profiles` content, `docs/simulation_quality/
  corpus_tier_taxonomy.md`'s Stress-tier classification criterion should be re-read before merging —
  this test plan does not add an automated guard for tier-purity since it's a documentation/judgment
  concern, not a state-correctness one, but reviewers should treat unexplained Pattern-6 content on
  a stress-tier world as a flag, not accept it silently.
