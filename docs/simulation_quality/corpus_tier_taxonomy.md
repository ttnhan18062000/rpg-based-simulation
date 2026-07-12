---
status: active
layer: simulation
authority: P1
audience: developer
tags: [simulation-quality, world, corpus, documentation, taxonomy]
---

# SimQ Corpus Tier Taxonomy

**Ticket:** TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC
**Parent epic:** TCK-20260704-SIMQ-CORPUS-TIERS-EPIC
**Date:** 2026-07-06

---

## Why this taxonomy exists

The driving product philosophy behind the `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` initiative: world
data should eventually exercise every feature the simulation engine supports — not just the
features that already look good — across worlds of deliberately varied scale and composition, so
SimQ scoring becomes an honest diagnostic across the whole corpus, surfacing what's weak rather
than only confirming what's already strong.

Applied naively, this would mean turning every feature on in every world. That makes
troubleshooting *harder*, not easier: if every world exercises every mechanic simultaneously, a
pillar regression can no longer be attributed to a specific mechanic — it could be the mechanic
itself, or an interaction between it and everything else running at the same time.

The fix is to treat the calibration corpus like a test pyramid, mirroring the standard
unit/end-to-end/stress/regression split used for code test suites — but applied to *worlds*
instead of test functions. Each tier has a distinct job:

| Tier | Job | What "good" looks like |
|---|---|---|
| **Unit** | Isolate exactly one gated mechanic | Clean, single-variable attribution when a pillar regresses — you know immediately which mechanic caused it |
| **End-to-end** | Exercise a coherent, realistic scenario combining several systems the way they'd actually interact | Archetype-appropriate richness; interaction effects are expected and meaningful, not noise |
| **Stress** | Push scale/composition to extremes | Confidence the engine holds up outside the "comfortable middle" of entity/region/resource counts |
| **Regression / baseline** | Stay stable | A control group — if this tier's grades move, something genuinely regressed, since nothing about these worlds should be changing |

---

## Tier definitions

### Unit tier

New, small, **synthetic-content-OK** worlds. Each isolates exactly ONE compile-time-gated or
feature-flag-gated mechanic, with everything else left at its inert/default baseline. Narrative
coherence is explicitly not a goal here — these are controlled experiments, not gameplay
archetypes. Template or synthetic content is acceptable and often preferable, since it keeps the
isolation clean.

**Classification criterion:** a world belongs in this tier if it isolates exactly one
Pattern-6-style gated field (see `docs/guidelines/design_patterns.md`'s "Compile-Time Pillar
Activation Pattern") or exactly one feature flag, with every other gated mechanic left at its
existing corpus-wide default.

### End-to-end tier

Existing (or new) **archetype** worlds — the ones meant to represent a real, shippable gameplay
scenario. These get richer, bespoke, archetype-matched content rather than templated content: if a
world's description says "settlement-heavy urban politics," its FACTION/INFORMATION content should
read as urban political content, not a copy-paste of another world's values.

**Classification criterion:** a world belongs in this tier if it extends an existing archetype
world's content richness, or introduces a new world explicitly authored to represent a coherent
gameplay scenario (not an isolated mechanic test, not a scale stress test).

### Stress tier

New worlds specifically authored to fill a **named scale-diversity gap** identified by investigation
— e.g. a world combining a high distinct-faction count with a small map, or resource-node density
decoupled from map size, or gated content combined with a large-scale population. The goal is
coverage of scale/composition combinations that don't occur naturally as a byproduct of other
worlds' authoring, not narrative coherence.

**Classification criterion:** a world belongs in this tier if its primary authoring justification is
"this fills scale-diversity gap X," citing a specific gap named in an investigation document (see
§ below for the gaps currently on record).

### Regression / baseline tier

Worlds that already have committed calibration anchors (`tests/simulation_quality/fixtures/
grade_anchors.json`) and are treated as a stable control group. **This is a "do not touch" policy,
not an oversight or a placeholder waiting to be upgraded.** If a ticket needs to add content to a
regression-tier world, that content addition should be deliberate and tracked (as
`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` does for the end-to-end tier), not an incidental
side effect — and any resulting anchor drift must be re-verified and re-committed with attribution,
following the precedent `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s Step 4a established.

**Classification criterion:** a world belongs in this tier by default the moment it has at least one
committed entry in `grade_anchors.json`, unless and until a ticket deliberately promotes it into
active end-to-end-tier content work.

---

## Current tier mapping (as of 2026-07-07)

The original 10 worlds under `data/worlds/` were **Regression / baseline tier**. As of
`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`, 8 of those 10 have been deliberately promoted to
**End-to-end tier**: each received bespoke, archetype-matched `faction_tension_overrides` and (for 6
of the 8) `information_source_profiles`/`pending_information_responses` content, with calibration
anchors re-verified and updated — see `docs/simulation_quality/eval_matrix_results.md`'s
"FACTION/INFORMATION Content Expansion" section for the full per-world judgment calls and grade
tables. `urban_political` (already End-to-end by this same criterion, promoted earlier by
`TCK-20260702-SIMQ-UPLIFT2-FACTION`/`-INFORMATION`, predating this taxonomy doc) and
`simq_routing_test` (a purpose-built AGENCY calibration fixture, not a shipped-gameplay archetype)
remain **Regression/baseline tier** — neither is one of this ticket's 8 target worlds. Four new
**Unit-tier** worlds now exist (`unit_faction_tension`, `unit_information_source`,
`unit_selfmodel_pilot`, `hero_guild_routing`) — the first two added by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`, the third by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`, and the fourth by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` — see
`docs/simulation_quality/eval_matrix_results.md`'s "Unit-Tier Isolation Worlds" section for their
grade tables. Three new **Stress-tier** worlds now exist — `crowded_frontier`,
`resource_dense_basin`, and `frontier_marches`, all added by
`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` — filling named scale-diversity gaps 1-3 below; see
`docs/simulation_quality/eval_matrix_results.md`'s "Stress-Tier Worlds" section for their grade
tables and per-world justification.

| World | Tier | Notes |
|---|---|---|
| `wilderness_survival` | End-to-end | 11 entities, 4 regions — smallest world in the corpus; FACTION-only (INFORMATION documented skip, no settlement module) |
| `sandbox_world` | End-to-end | 18 entities, 3 regions; FACTION + INFORMATION (`town_notice_board`) |
| `highland_traverse` | End-to-end | 18 entities, 5 regions; FACTION + INFORMATION (`route_waystation_guide`) + SOCIAL (`ENABLE_SOCIAL_COOPERATION`, TCK-20260710-SIMQ-DEPTH-SOCIAL: SOCIAL C→S all 3 seeds, `settled_quarter` civilian/guard population satisfies `current_objective_id` gate) |
| `urban_political` | Regression/baseline | 30 entities, 3 regions — the only world with any FACTION/INFORMATION/self-model content populated before this ticket; already End-to-end by criterion, not one of this ticket's 8 target worlds |
| `dungeon_crawl` | End-to-end | 32 entities, 4 regions; FACTION-only (INFORMATION documented skip, no settlement module). SOCIAL activation rejected (TCK-20260710-SIMQ-DEPTH-SOCIAL): no settlement/civilian module → no population ever accrues `current_objective_id` → `HelpNeedEvaluator` hard gate never opens; 0 cooperation events under a live probe, SOCIAL stays C |
| `swamp_border_world` | End-to-end | 26 entities, 4 regions; FACTION + INFORMATION (`town_notice_board`) |
| `simq_routing_test` | Regression/baseline | 30 entities, 3 regions — the only world with `ENABLE_ADVENTURE_ROUTING=ON`, purpose-built as a minimal AGENCY calibration world (not a shipped gameplay archetype) |
| `frontier_living_world` | End-to-end | 46 entities, 7 regions; FACTION + INFORMATION (`town_notice_board`) + SOCIAL (`ENABLE_SOCIAL_COOPERATION`, TCK-20260710-SIMQ-DEPTH-SOCIAL: SOCIAL C→S all 3 seeds, `frontier_village_core` civilian/guard population satisfies `current_objective_id` gate) |
| `generated_frontier_3_42` | End-to-end | 44 entities, 6 regions — procedurally generated; FACTION + INFORMATION content authored; anchored at 200t (3 seeds) and 1000t (seed42) per TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS |
| `frontier_extended` | End-to-end | 56 entities, 10 regions — largest world in the corpus; FACTION + INFORMATION (`town_notice_board`) |
| `unit_faction_tension` | Unit | 18 entities, 3 regions — isolates FACTION only (TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO) |
| `unit_information_source` | Unit | 16 entities, 1 region — isolates INFORMATION only (TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO) |
| `unit_selfmodel_pilot` | Unit | 16 entities, 1 region — isolates COGNITION's self-model materialization half only (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT) |
| `hero_guild_routing` | Unit | 31 entities, 4 regions — isolates AGENCY/route-selection only via `ENABLE_ADVENTURE_ROUTING` (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY); real-archetype scale distinguishes it from calibration-minimal `simq_routing_test` |
| `crowded_frontier` | Stress | 38 entities, 4 regions — fills gap 1 (many-factions/small-map): 6 distinct populated factions in a 4-region footprint (TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS) |
| `resource_dense_basin` | Stress | 23 entities, 3 regions — fills gap 2 (resource-saturated/small-map): the corpus's new resource-node density maximum, ~2.33 nodes/region (TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS) |
| `frontier_marches` | Stress | 62 entities, 9 regions — fills gap 3 (large-scale FACTION/INFORMATION, authored-from-inception): `faction_tension_overrides` + `information_source_profiles`/`pending_information_responses` seeded from this world's first compile, at `frontier_extended`-comparable scale (TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS) |

Full per-world entity/region/resource/quest counts and module composition are documented in
`staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` §2 — this doc cites that
table as its evidentiary source rather than duplicating it, since the investigation's numbers are
the audited, evidence-backed original and should not risk drifting out of sync with a second copy.

**FACTION coverage closure (2026-07-10, `TCK-20260710-SIMQ-DEPTH-FACTION`):** the roadmap's Phase 3
FACTION-half re-verified this table's tier assignments against live `data/worlds/*/world.yaml`
content and found them accurate (no staleness) — 11/17 corpus worlds carry
`faction_tension_overrides` content; the 6 that do not (`crowded_frontier`, `resource_dense_basin`,
`simq_routing_test`, `hero_guild_routing`, `unit_information_source`, `unit_selfmodel_pilot`, all
already listed in the table above) are each FACTION-inert by deliberate tier-purity design, not by
omission. No tier reassignment resulted. See `eval_matrix_results.md`'s "FACTION Coverage Closure —
Phase 3" section for the full re-verification table.

**INFORMATION coverage closure (2026-07-12, `TCK-20260710-SIMQ-DEPTH-INFORMATION`):** the roadmap's
Phase 3 INFORMATION-half re-verified this table's tier assignments against live
`data/worlds/*/world.yaml` content and `config/simulation_quality/profiles/*.yaml` flags (two
independent, agreeing signals) and found them accurate (no staleness) — 9/17 corpus worlds carry
`information_source_profiles`/`pending_information_responses` content with
`ENABLE_BELIEF_ASSIMILATION: "ON"`; the 8 that do not (`dungeon_crawl`, `wilderness_survival`,
`crowded_frontier`, `resource_dense_basin`, `simq_routing_test`, `hero_guild_routing`,
`unit_faction_tension`, `unit_selfmodel_pilot`, all already listed in the table above) are each
INFORMATION-inert by a documented, pre-existing reason (2 structural — no population-bearing
settlement module; 2 Stress tier-purity; 1 Regression/baseline fixture; 3 Unit single-mechanic
isolation), not by omission. No tier reassignment resulted. See `eval_matrix_results.md`'s
"INFORMATION Coverage Closure — Phase 3" section for the full re-verification table.

---

## Named scale-diversity gaps (stress-tier candidates)

Per `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` §2, the following
scale/composition combinations are **not currently represented** by any world in the corpus, and are
the concrete candidates a stress-tier world should cite when justifying its authoring:

1. **Large faction count + small entity/region footprint.** No world combines a high distinct-faction
   count (6-9) with a small map — faction density and world size currently move together.
2. **High resource-node density with a small map** (or the inverse: a sprawling map with sparse
   resources). Node-per-region density is currently roughly flat (1.3-1.75) across the corpus
   regardless of overall scale.
3. **Pattern-6 gated content (FACTION/INFORMATION/self-model) combined with a large-scale
   population.** ~~The only world with any of this content populated (`urban_political`) is
   mid-scale; there's no data point for how these mechanics behave at `frontier_extended`'s scale~~
   — **stale as of `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`**: `frontier_extended` and
   `frontier_living_world` now both carry `faction_tension_overrides`/`information_source_profiles`
   content too, but as a **retrofit** applied after those worlds were already anchored, not
   authored alongside their initial composition. `frontier_marches`
   (`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`) closes the remaining, narrower version of this gap:
   the first world with this content **authored from inception** — present at first compile,
   not added after the fact — at `frontier_extended`-comparable scale (62 entities/9 regions vs.
   56/10). `wilderness_survival`'s near-zero settlement structure remains an intentional
   INFORMATION skip (no settlement-adjacent module), not a gap this ticket addresses.
4. **A routing-capable (AGENCY-active) world that is also a "real" gameplay archetype**, as opposed
   to `simq_routing_test`'s purpose-built minimal-calibration framing.
5. **Quest density decoupled from entity count.** Quest-def count currently scales almost linearly
   with entity count across the corpus; no world deliberately decouples these axes.

`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` is scoped to address a subset of these gaps — it is not
required to close all five in one ticket.

---

## Classifying a future world addition

When authoring a new world (or substantially extending an existing one), classify it using this
decision order:

1. **Does it isolate exactly one gated mechanic, with everything else at baseline, using
   template/synthetic content?** → **Unit tier.**
2. **Does it fill one of the named scale-diversity gaps above (or a newly-investigated one)?** →
   **Stress tier.**
3. **Does it extend an existing archetype world's content richness, or introduce a new world meant
   to represent a coherent, shippable gameplay scenario?** → **End-to-end tier.**
4. **Does it already have a committed `grade_anchors.json` entry, with no ticket currently
   deliberately extending its content?** → **Regression/baseline tier** — leave it alone unless a
   ticket explicitly promotes it.

A world should not straddle multiple tiers at once. If a stress-tier world happens to also exercise
a Pattern-6 mechanic (gap 3 above explicitly combines scale with gated content), classify it as
stress tier and note the mechanic it also happens to exercise — the primary tier is determined by
its *authoring justification*, not by every mechanic it happens to touch.

---

## Related documents

- `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` — full evidentiary
  source for the mechanic inventory (§1) and scale diversity tables/gap analysis (§2) this doc
  summarizes. **Path no longer resolves** — `staging_artifacts/` is gitignored and this pre-ticket
  epic-scoping doc was never migrated to `stored_artifacts/` before being lost; see
  `tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the root cause. The tables
  this doc summarizes have been independently re-verified against ground truth (`world.yaml`/
  `world_compile_report.json`, `test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`).
- `docs/guidelines/design_patterns.md` — Pattern 6, "Compile-Time Pillar Activation Pattern"
- `docs/simulation_quality/eval_matrix_results.md` — calibration grade tables and AC6/exception
  history for the regression-tier worlds
- `docs/simulation_quality/quality_scoring_contract.md` — SimQ 10-pillar scoring contract
- `docs/plans/audit_fix_plan.md`
- `tickets/todos/simq-corpus-tiers/SEQUENCE.md` — ordering rationale for this epic's 10 child
  tickets, several of which author worlds this taxonomy classifies
