---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY
artifact_type: test_plan
tags: [simulation-quality, agency, adventure, corpus, calibration]
---

# Test Plan — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY

## Regression Surface

**Unit / harness:**
- `tests/simulation_quality/test_evaluate_harness.py` — 17 tests exercising `_within_band`/
  `_compare`/`_parse_run_key`; unaffected by adding a new world, but must stay green (confirms the
  generalized-mechanism migration in `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE` is not
  disturbed).
- `tests/simulation_quality/test_grade_regression.py` — parametrized over `FAST_ANCHOR_KEYS`
  (currently 52 keys across ~17 worlds, including `simq_routing_test_seed{42,123,456}_500t`'s own 3
  anchors). All existing entries must still pass `test_grade_anchor_file_exists_and_valid` and
  `test_grade_within_anchor_band` after this ticket's 3 new keys are added.
- `tests/unit/worldassembly/test_corpus_diversity.py` — `test_entity_count_band` and
  `test_distinct_populated_factions` are parametrized over fixed dicts that do **not** currently
  include `hero_guild_routing`; adding this world must not require touching
  `ANCHORED_WORLD_BANDS`/`EXPECTED_DISTINCT_POPULATED_FACTIONS` (those are explicitly scoped to the
  5-world Regression-tier band set per the file's own header comment) — only
  `POPULATION_STABILITY_WORLDS` gets the new entry, mirroring how `unit_faction_tension`/
  `unit_information_source`/`unit_selfmodel_pilot` were added there without touching the other two
  dicts.
- `tests/unit/strategic/test_opportunities.py` — includes
  `test_resource_opportunities_hometown_wood_node`/`test_resource_opportunities_hometown_herb_patch`
  (from `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`) — must stay passing; this world's
  `frontier_village_core` module depends on that same global catalog fix.

**Integration / world-assembly:**
- `tests/integration/worldassembly/test_real_content_world_modules.py`,
  `tests/integration/worldassembly/test_real_content_world_compositions.py`,
  `tests/unit/worldbuilding/test_world_compiler.py`, `tests/unit/worldassembly/test_resolver.py` —
  the SELFMODEL-PILOT precedent ran exactly this set (50 passed) after authoring a new world; same
  scope applies here since this ticket also adds a new `data/worlds/<id>/` composition.
- `tests/integration/domains/test_fused_loop.py` — not directly touched, but confirms the broader
  domain-phase fixture set stays stable; cheap to include in the same scoped run.

**Arena-combat:** none directly in scope — `AdventureDecisionPhase` interacts with combat only
indirectly (route selection may lead a hero toward a `COMBAT_RETREAT`/engagement project), and this
ticket does not modify combat logic. No arena-combat test file is listed in Related Code Areas.

## New Tests Required

- **Name**: `test_population_stability[hero_guild_routing]` (parametrized case added by extending
  `POPULATION_STABILITY_WORLDS` in `tests/unit/worldassembly/test_corpus_diversity.py`)
  **Category**: integration / architecture guard (marked `@pytest.mark.slow`)
  **Verifies**: >=60% starting `entity_count` stays alive at every 50-tick checkpoint through 300
  ticks (Acceptance Criterion: "population-stable (>=60% alive floor) through 200-500 ticks").
  **Caveat carried from investigation.md OQ-1**: this mechanism does not currently apply a world's
  profile `feature_flags:` — it runs with `ENABLE_ADVENTURE_ROUTING` at default OFF. The
  plan/implementer must decide whether that is acceptable as the AC's stability check (with the
  3-seed calibration matrix below serving as the actual flag-ON stability evidence) or whether the
  harness needs a small generalization first. Do not silently treat the OFF-flag pytest pass as
  proof of ON-flag stability without documenting which claim it actually supports.
  **Where**: `tests/unit/worldassembly/test_corpus_diversity.py` (add `"hero_guild_routing"` to the
  existing `POPULATION_STABILITY_WORLDS` list, no new test function needed).

- **Name**: 3-seed calibration matrix entries — `hero_guild_routing_seed42_{N}t`,
  `hero_guild_routing_seed123_{N}t`, `hero_guild_routing_seed456_{N}t` (N = 500 per UQ-1's default,
  unless the plan changes it).
  **Category**: unit (fixture-data) / regression anchor
  **Verifies**: `test_grade_regression.py::test_grade_within_anchor_band` and
  `test_grade_anchor_file_exists_and_valid` for the 3 new keys, once added to both
  `grade_anchors.json` and `FAST_ANCHOR_KEYS`. Each entry must record the actual measured grade for
  all 10 pillars (not just AGENCY) — mirror the 10-key-per-entry shape already used by every other
  world in `grade_anchors.json` (see `unit_faction_tension_seed42_200t` as the structural template:
  `{"COGNITION": ..., "AGENCY": ..., "COMBAT": ..., "FACTION": ..., "ECONOMY": ..., "PROGRESSION":
  ..., "SOCIAL": ..., "INFORMATION": ..., "WORLD": ..., "NARRATIVE": ...}`).
  **Where**: `tests/simulation_quality/fixtures/grade_anchors.json` (data),
  `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` list entries).

- **Name**: `test_production_catalog_wood_and_herb_cover_hometown`-style spot-check (only if OQ-2 from
  investigation.md surfaces a real gap) — e.g. a targeted opportunity-availability check for
  `mountain_pass`/`ruins_mystery_quest`/`goblin_camp_conflict` regions, mirroring
  `test_resource_opportunities_hometown_wood_node`'s pattern.
  **Category**: unit
  **Verifies**: every region this world's heroes can occupy has at least one resource node (or other
  route-eligible opportunity) tagged for it, preventing a repeat of the `hometown` stasis-collapse
  class of bug in a new region.
  **Where**: `tests/unit/strategic/test_opportunities.py` (additive, only if the plan's Scope-4/5
  investigation finds an actual gap — do not add a synthetic test for a gap that turns out not to
  exist; document a clean-pass finding instead, per the SELFMODEL-PILOT precedent's "honest result"
  norm).

- **Name**: `eval_matrix_results.md` `### hero_guild_routing` subsection (documentation, not a pytest
  test, but an Acceptance Criterion deliverable)
  **Category**: n/a (doc)
  **Verifies**: the actual measured AGENCY grade (and all 9 other pillars) is recorded honestly,
  framed as a second routing-capable archetype distinct from `simq_routing_test`'s calibration-only
  purpose, per AC.
  **Where**: `docs/simulation_quality/eval_matrix_results.md`, directly after the existing
  `simq_routing_test` section (mirroring where `unit_selfmodel_pilot`'s section was inserted after
  `unit_information_source`'s).

- **Name**: `docs/simulation_quality/corpus_tier_taxonomy.md` Unit-tier table row update
  (documentation deliverable, cross-checked by no automated test today — flag as a manual-diff
  check in the Scoped Commands below).
  **Where**: `docs/simulation_quality/corpus_tier_taxonomy.md`.

## Scoped Pytest / Tool Commands

```
# Existing-corpus regression check before any change (baseline)
.venv/bin/python3 tools/evaluate_simq.py --dry-run

# After authoring the world (already done) — architecture/compile sanity
pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldassembly/test_resolver.py \
       tests/integration/worldassembly/test_real_content_world_modules.py \
       tests/integration/worldassembly/test_real_content_world_compositions.py -q

# Population-stability guard (slow marker; run explicitly, not swept up by "not slow")
pytest tests/unit/worldassembly/test_corpus_diversity.py -k hero_guild_routing -q

# Resource-opportunity spot check (existing hometown regression + any new region-coverage additions)
pytest tests/unit/strategic/test_opportunities.py -q

# 3-seed calibration matrix (profile feature_flags drive ENABLE_ADVENTURE_ROUTING=ON automatically —
# do not export the env var manually; that would bypass the generalized mechanism this ticket
# depends on and defeat its own Scope item 1 verification)
.venv/bin/python3 tools/calibrate_simq.py --name hero_guild_routing --seed 42   --ticks 500
.venv/bin/python3 tools/calibrate_simq.py --name hero_guild_routing --seed 123  --ticks 500
.venv/bin/python3 tools/calibrate_simq.py --name hero_guild_routing --seed 456  --ticks 500

# Grade-anchor + regression harness after adding entries
pytest tests/simulation_quality/test_grade_regression.py -q
.venv/bin/python3 tools/evaluate_simq.py --dry-run    # or: make evaluate

# Full scoped sweep matching the SELFMODEL-PILOT precedent's own combined run
pytest tests/unit/worldassembly/test_corpus_diversity.py \
       tests/simulation_quality/test_grade_regression.py \
       -m "not slow" -q

# Docs/index refresh (only if docs/ files changed, per project workflow rule)
make knowledge-index-update
```

Never run `pytest tests/` unscoped. All commands above are scoped to
`simulation_quality`/`worldassembly`/`strategic` domains directly implicated by this ticket.

## Anti-Drift Test Guards

- **9-non-routing-worlds grade-stability guard**: after adding `hero_guild_routing`'s anchors, re-run
  `tools/evaluate_simq.py --dry-run` (or `make evaluate`) across the **full** existing corpus (not
  just the new world) and confirm 0 regressions — this is the direct check for "None of the 9
  existing non-routing worlds' AGENCY grades change" (AC). A regression anywhere outside
  `hero_guild_routing_*` keys means the profile YAML or a shared catalog file leaked scope.
- **Profile-leakage grep guard**: `grep -rl ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/`
  must return exactly `simq_routing_test.yaml` and `hero_guild_routing.yaml` — nothing else. Run this
  before declaring the ticket done, mirroring the exact verification step
  `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE` performed for its own migration.
- **AGENCY Cross-World Design Note additive-only guard**: diff
  `docs/simulation_quality/eval_matrix_results.md` before/after and confirm the existing "9
  non-routing worlds stay C" and `simq_routing_test` calibration-harness paragraphs are byte-identical
  — only new content should be appended (new subsection + one new paragraph in the Cross-World Design
  Note), matching how `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` appended rather than
  rewrote.
- **Anchor-count sanity guard**: `grade_anchors.json` should go from 52 total keys to 55 (49 world
  entries + 3 metadata keys → 52 world entries + 3 metadata keys), and `FAST_ANCHOR_KEYS` should gain
  exactly 3 new entries — a mismatch (e.g. 6 new keys, suggesting a duplicate seed or wrong tick
  count) should block before commit.
- **Isolation guard**: confirm no `faction_tension_overrides`, `information_source_profiles`,
  `pending_information_responses`, or `pending_self_model_information_events` blocks were added to
  `hero_guild_routing/world.yaml` — this world's Out-of-Scope explicitly excludes seeding
  FACTION/INFORMATION/self-model content; a diff review of the final `world.yaml` should show only
  AGENCY/routing-relevant content.
