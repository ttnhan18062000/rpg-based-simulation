---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, world, corpus, calibration]
---

# TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS

## Title
Author new stress-tier worlds filling the corpus's identified scale-diversity gaps

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 found that scale
diversity across the existing 10 worlds is incidental (a byproduct of module composition for other
reasons), not deliberate, and named specific combinations "NOT currently represented":
- Large faction count (6-9) combined with a small entity/region footprint (today, faction density
  and world size move together — the 6-9-faction worlds are also the largest)
- High resource-node density with a small map (today's densest world, `frontier_extended`, is also
  the largest by region count — nothing tests a small map saturated with resources, or the inverse)
- FACTION/INFORMATION/self-model content combined with a large-scale population (the only world
  with any Pattern-6 content, `urban_political`, is mid-scale — 30 entities/3 regions — there is no
  data point at `frontier_extended`'s scale, 56 entities/10 regions)

This ticket authors new stress-tier worlds filling these gaps, per the taxonomy
`TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` defines.

## Scope
1. Author **at minimum** the following, per the task's explicit minimum:
   (a) **A many-factions/small-map world**: comparable in entity/region footprint to the smallest
       existing worlds (`wilderness_survival` 11/4, `sandbox_world` 18/3) but with 6-9 distinct
       populated factions (matching the density of `frontier_living_world`/`generated_frontier_3_42`/
       `frontier_extended`) crammed into that small footprint.
   (b) **A sparse-resources/large-map world, OR a resource-saturated/small-map world** — whichever
       this ticket's own investigation phase judges more valuable given available catalog content
       (both fill the same identified gap from opposite directions; pick one and justify the choice
       in Implementation Notes).
   (c) **A world combining FACTION/INFORMATION content with a large-scale population** — comparable
       to `frontier_extended`'s scale (56 entities/10 regions), with `faction_tension_overrides`
       and `information_source_profiles`/`pending_information_responses` seeded (bespoke to this
       world's archetype, following the same per-world judgment discipline as
       `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`) — the first data point for how these
       mechanics behave at large scale.
2. For each new world: compile, verify 0 warnings, verify population stability (>=60% alive floor)
   through 200-300 ticks, run a 3-seed calibration matrix, add grade-anchor entries.
3. Use the `distinct_populated_factions` metric from `TCK-20260704-SIMQ-CORPUS-SCALE-METRIC` (if
   landed) to numerically confirm world (a) actually achieves 6-9 populated factions in a small
   footprint — do not rely on eyeballing the world.yaml content.
4. Update `docs/simulation_quality/eval_matrix_results.md` with the new worlds' grade tables, tagged
   as stress-tier.
5. Run `make evaluate --dry-run` (0 regressions on pre-existing corpus) and
   `make knowledge-index-update` if docs changed.

## Out of Scope
- Any changes to the 9 existing non-routing worlds' AGENCY grade — stress-tier worlds this ticket
  authors are new worlds, not modifications reversing the AGENCY-DA ruling
- Quest-density-vs-entity-count decoupling (investigation.md §2's fourth named gap) — this ticket's
  minimum scope is the 3 gaps explicitly listed in Scope item 1; the quest-density gap may be picked
  up in a future ticket if judged valuable, but is not required here
- Fixing any pillar scoring/emission bug discovered while authoring these worlds — file a follow-up
  ticket

## Acceptance Criteria
- [x] A many-factions/small-map world exists: entity/region footprint comparable to
      `wilderness_survival`/`sandbox_world`, with 6-9 distinct populated factions confirmed
      (numerically, via the scale metric if available)
- [x] Either a sparse-resources/large-map world or a resource-saturated/small-map world exists, with
      the choice justified in Implementation Notes
- [x] A large-scale (comparable to `frontier_extended`) world exists with bespoke
      `faction_tension_overrides` and `information_source_profiles`/`pending_information_responses`
      content
- [x] All 3 new worlds compile with 0 warnings and are verified population-stable (>=60% alive
      floor) through 200-300 ticks
- [x] All 3 new worlds have 3-seed grade-anchor entries
- [x] `docs/simulation_quality/eval_matrix_results.md` updated with stress-tier grade tables
- [x] `make evaluate --dry-run` exits 0 with 0 regressions

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — defines stress-tier criteria these worlds must meet
- TCK-20260704-SIMQ-CORPUS-SCALE-METRIC — used to numerically verify the many-factions/small-map
  world's faction density
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — sibling content-authoring discipline (per-world
  judgment, not copy-paste) that the large-scale FACTION/INFORMATION world in this ticket should
  follow
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — precedent for compile/verify/anchor workflow

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 ("Combinations NOT
  currently represented" — all 4 named gaps, 3 of which this ticket addresses)
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/guides/content_authoring.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — compile/verify/anchor workflow
  reference

## Related Code Areas
- `data/worlds/` — 3 new world directories
- `data/content/world_modules/` — existing modules to compose from (prefer reuse over new module
  authoring where possible, per investigation.md §3's low-risk framing for content-only changes)
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- UQ-1: Should these 3 worlds be built primarily from existing catalog modules
  (`data/content/world_modules/`), or does filling the "many-factions/small-map" gap specifically
  require new module content (since no existing module combination currently produces that
  shape, per investigation.md §2)? Investigate available existing modules first; only author new
  module content if no existing combination can achieve the target shape.
- UQ-2: For gap (b) (sparse-resources/large-map vs. resource-saturated/small-map) — this ticket
  explicitly defers the choice to the implementer's investigation phase, per the task's own framing
  ("whichever the implementer's investigation phase judges more valuable"). Document the reasoning
  for whichever is chosen.

## Implementation Notes

All 3 worlds built entirely from existing `data/content/world_modules/` catalog content (UQ-1: no
new module authored). All measured compile-report numbers matched the plan's pre-computed table
exactly (0 warnings, entity/region/faction counts all as predicted), so no target had to be
re-derived from ground truth.

**crowded_frontier (gap a — many-factions/small-map, seed 601):** `frontier_village_core` +
`hero_adventurers` + `bandit_road_trade_pressure` + `goblin_camp_conflict` + `orc_clan_territory`.
Compiled: 38 entities, 4 regions, 6 distinct populated factions, 0 warnings. UQ-1 resolution (region
count, not raw entity count, is the axis satisfied): 4 regions matches `wilderness_survival`
exactly; 38 entities is the necessary cost since no catalog faction-populating module besides
`hero_adventurers` contributes under 5 entities. No `faction_tension_overrides`/
`information_source_profiles` added (tier-purity rule). 3-seed/200t calibration: identical grades
across all 3 seeds, all C/B baseline except NARRATIVE=A — no anomaly.

**resource_dense_basin (gap b — resource-saturated/small-map, seed 602):** `frontier_village_core`
+ `old_mine_resource_loop` + `orc_clan_territory`. Compiled: 23 entities, 3 regions, 4 distinct
populated factions, 0 warnings. UQ-2 resolved toward resource-saturated/small-map (lower
authoring/verification risk than the sparse/large-map alternative, which would need ~7-8 modules).
**Correction to the plan's own resource-density arithmetic:** the plan's investigation phase
estimated "~37 nodes / ~12.3 per region" by summing each resource definition's `count:`/charge
field, but the compile report's authoritative `resource_node_count` metric (the same one used
throughout `eval_matrix_results.md`'s scale-summary table) counts distinct resource-node
*definitions*, not charges — the real measured value is 7 nodes / 3 regions (~2.33/region). This is
still the corpus's new density maximum (surpassing `swamp_border_world`'s prior 1.75/region), so the
gap-2 justification still holds; only the specific number was wrong and has been corrected in
`eval_matrix_results.md`. Step 7's resource-tag spot-check found a **mixed** result, not a uniform
clean pass: `old_mine` is covered (`iron_vein`'s legacy_id fallback in
`src/core/registries.py:435-436` infers `source_region_tags=("old_mine",)`), but `orc_stronghold`
has a genuine, pre-existing gap — neither `iron_vein` nor `wood_node` (the two resource kinds
`orc_clan_territory` places there) carries an `orc_stronghold` `source_region_tags` entry in
`data/content/world/resources.yaml`. This gap pre-dates this ticket (`orc_clan_territory` is already
composed by `frontier_extended`/`frontier_living_world`/`generated_frontier_3_42`); it is
deliberately left unfixed (shared catalog file, out of this ticket's scope) and documented as a
follow-up recommendation, mirroring the `hero_guild_routing`/`mountain_pass_zone` precedent exactly.
Two targeted spot-check tests added to `tests/unit/strategic/test_opportunities.py` confirming both
findings. 3-seed/200t calibration: identical grades across all 3 seeds; ECONOMY=C is stable and not
anomalous (matches the corpus's typical ECONOMY=C baseline) despite the elevated resource density —
no scoring-formula concern found on inspection.

**frontier_marches (gap c — large-scale FACTION/INFORMATION, authored-from-inception, seed 603):**
`frontier_village_core` + `hero_adventurers` + `wolf_den_near_forest` + `goblin_camp_conflict` +
`bandit_road_trade_pressure` + `orc_clan_territory` + `undead_battlefield` + `sunken_swamp_border` +
`old_mine_resource_loop`. Compiled: 62 entities, 9 regions, 9 distinct populated factions, 0
warnings. Gap-c reframed (not dropped) per the plan: `frontier_extended`/`frontier_living_world`
already gained this content via the sibling E2E-CONTENT-EXPANSION ticket as a **retrofit**;
`frontier_marches` is the first world with this content **authored from inception** at comparable
scale, sharing 6 of `frontier_extended`'s 8 modules but swapping `forest_warden_grove` for
`hero_adventurers`+`sunken_swamp_border` (not a near-duplicate composition). Bespoke content: a
`bandit_company`/`orc_clan` tension pair (no other world declares this pair together) and a
`bandit_road_conditions`/`bandit_road`/`0.72` information response (deliberately distinct subject/
region/certainty from both sibling worlds). `docs/parity_ledger/faction.yaml::FAC-012` and
`docs/parity_ledger/infrastructure.yaml::INFRA-256` both extended additively (one clause each, no
existing text reworded), closing the prior inconsistency where INFRA-256 had been extended twice for
the E2E ticket's work but FAC-012 had not been touched at all.

**Deviation from the plan, traced and resolved (not silently worked around):** the plan did not
call for a new calibration profile file, but the first `frontier_marches` calibration pass measured
`INFORMATION=C`/`event_count=0` despite `AuthoritativeState.pending_information_responses` compiling
correctly (1 well-formed entry, verified directly via a Python compile check — `actor_id=9`, subject
`bandit_road_conditions` present). Traced (per the "honest-grade, trace before assuming a bug"
discipline) to `ENABLE_BELIEF_ASSIMILATION` defaulting OFF (`src/domains/optimization/feature_flags.py:18`)
with no matching `config/simulation_quality/profiles/frontier_marches.yaml` to turn it ON — every
other world with `information_source_profiles` content (`frontier_extended`, `frontier_living_world`,
`sandbox_world`, `highland_traverse`, `swamp_border_world`, `urban_political`,
`generated_frontier_3_42`, `unit_information_source`) has exactly such a profile file, and
`frontier_marches` was missing the equivalent. Added
`config/simulation_quality/profiles/frontier_marches.yaml` (`feature_flags:
{ENABLE_BELIEF_ASSIMILATION: "ON"}`, mirroring `frontier_extended.yaml` byte-for-byte) and
recalibrated all 3 seeds — INFORMATION moved to B/event_count=1 in all 3, matching the established
C→B pattern. Recorded as a Deviation in `staging_artifacts/.../plan.md`.

3-seed/200t calibration (post-fix): identical grades across all 3 seeds — FACTION=S (genuine signal
from the seeded tension pair) and INFORMATION=B (genuine signal from Branch A, 1
`belief_assimilated`/`belief_updated` hit/run) both confirm the bespoke content is live and
measurable at this scale.

**Consolidation (Step 11):** `docs/simulation_quality/eval_matrix_results.md` gained 3 rows in the
"Corpus World-Scale Summary" table (with a note correcting the resource-node-count metric
conflation) plus a new "Stress-Tier Worlds" section with one subsection per world.
`docs/simulation_quality/corpus_tier_taxonomy.md`'s stale "no stress-tier world exists yet" sentence
and gap-3's stale "no data point" text were both corrected in place (not left standing unqualified
next to the new evidence), and 3 new tier-mapping rows were added.

**Full-corpus regression sweep (Step 12):** `test_corpus_diversity.py` (fast + all 3 new worlds'
slow population-stability tests), `test_assembly.py`, `test_world_compiler.py`/`test_catalog.py`/
`test_semantics.py`, `test_opportunities.py`, `test_grade_regression.py` (fast + full), and
`test_diplomacy.py` all pass with 0 failures. `python3 tools/evaluate_simq.py --dry-run` (used
directly per the plan's guard against the documented `make evaluate --dry-run` double-flag no-op
trap) reports 430 pillars checked, 0 regressions, 0 missing across the full corpus.
`grade_anchors.json` gained exactly 9 keys (55→64); `ANCHORED_WORLD_BANDS` and
`EXPECTED_DISTINCT_POPULATED_FACTIONS` each gained exactly 3 keys (5→8, 10→13) with no existing
key's value touched. None of the 3 worlds enable `ENABLE_ADVENTURE_ROUTING` (confirmed via grep),
so `INFRA-237`/`SIMQ-CALIBRATED-001` were correctly left untouched. `make knowledge-index-update`
and `graphify update .` both run since `docs/` and `tests/` files changed.

## Citation Correction (2026-07-08, TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING)

This ticket's citations above to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
(later renamed to `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`) point to a
pre-ticket epic-scoping investigation that was never migrated to `stored_artifacts/` and is now
unrecoverable: `staging_artifacts/` is gitignored by repo policy, and full git history confirms no commit
ever added a file at either path. This is a citation/traceability gap only -- every specific fact this
ticket drew from that doc has been independently cross-validated against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) by this ticket and/or
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` / `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`. See
`tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the full root-cause writeup.

## Test Summary
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -k "crowded_frontier or resource_dense_basin or frontier_marches"` — 12 passed (entity-band, distinct-factions, hazard-kind, population-stability x3 worlds)
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow"` — 30 passed (full fast corpus regression, no existing-world regression)
- `pytest tests/unit/strategic/test_opportunities.py` — 9 passed (7 existing + 2 new: `test_resource_opportunities_old_mine_iron_vein` clean-pass, `test_resource_opportunities_orc_stronghold_tag_gap` documented-gap)
- `pytest tests/simulation_quality/test_grade_regression.py -k "crowded_frontier or resource_dense_basin or frontier_marches"` — 9 passed (3 worlds x 3 seeds)
- `pytest tests/unit/worldassembly/test_assembly.py` — 30 passed
- `pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/content/test_catalog.py tests/unit/content_semantics/test_semantics.py` — 46 passed
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` — 36 passed, 15 skipped (pre-existing, missing local calibration data for unrelated worlds)
- `pytest tests/simulation_quality/test_grade_regression.py` (full) — 44 passed, 18 skipped
- `pytest tests/unit/faction/test_diplomacy.py` — 27 passed
- `python3 tools/evaluate_simq.py --dry-run` — 430 pillars checked, 0 regressions, 0 missing

## Files Changed
- `data/worlds/crowded_frontier/world.yaml` (new)
- `data/worlds/crowded_frontier/world_compile_report.json` (generated)
- `data/worlds/crowded_frontier/resolved/*` (generated)
- `data/worlds/resource_dense_basin/world.yaml` (new)
- `data/worlds/resource_dense_basin/world_compile_report.json` (generated)
- `data/worlds/resource_dense_basin/resolved/*` (generated)
- `data/worlds/frontier_marches/world.yaml` (new)
- `data/worlds/frontier_marches/world_compile_report.json` (generated)
- `data/worlds/frontier_marches/resolved/*` (generated)
- `data/worlds/world_index.json` (3 new entries registered)
- `config/simulation_quality/profiles/frontier_marches.yaml` (new — deviation, see Implementation Notes)
- `tests/unit/worldassembly/test_corpus_diversity.py` (`ANCHORED_WORLD_BANDS` +3, `EXPECTED_DISTINCT_POPULATED_FACTIONS` +3)
- `tests/unit/strategic/test_opportunities.py` (+2 new tests)
- `tests/simulation_quality/fixtures/grade_anchors.json` (+9 keys)
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` +9)
- `docs/parity_ledger/faction.yaml` (`FAC-012` additive clause)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-256` additive clause)
- `docs/simulation_quality/eval_matrix_results.md` (3 new scale-summary rows + new "Stress-Tier Worlds" section)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (stale stress-tier/gap-3 text corrected, 3 new tier-mapping rows)
- `staging_artifacts/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS/plan.md` (Deviations section added)

## Completion Summary
All 3 stress-tier worlds authored from existing catalog content, compiled with 0 warnings, verified
population-stable through 300 ticks, 3-seed/200t calibrated and anchored, and documented. Full
corpus (`make evaluate`: 430 pillars) shows 0 regressions. All 7 Acceptance Criteria met.

**One real, deliberately out-of-scope gap found during Step 7's spot-check, tracked, not left
unstated:** `resource_dense_basin`'s `orc_stronghold` region has no resource kind covering it in
`data/content/world/resources.yaml` — the same root mechanism (and exact same region name) already
tracked corpus-wide by `tickets/todos/TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT.md`.
Added `resource_dense_basin` as a new row to that ticket's existing uncovered-region table rather
than filing a duplicate ticket. A regression test documenting current behavior was added to
`tests/unit/strategic/test_opportunities.py`; the shared catalog file was deliberately left unfixed
here, per that audit ticket's own scope (it owns the fix-or-decide call across all affected worlds).
