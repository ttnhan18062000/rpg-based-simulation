---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-TIERS-EPIC
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, world, feature-flags, corpus]
---

# TCK-20260704-SIMQ-CORPUS-TIERS-EPIC

## Title
SimQ Corpus Tier Expansion: full-feature world coverage across Unit/End-to-End/Stress tiers

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` (2026-07-04, pre-ticket
epic-scoping pass, no code changed) found that four compile-time-gated mechanics — FACTION tension
seeding, INFORMATION source profiles, self-model/Branch B seed events, and AGENCY/adventure
routing — are populated in only 1 of 10 worlds (`urban_political`, and `simq_routing_test` for
AGENCY only), and that the corpus's scale diversity (entity/region/resource/faction counts) is
incidental (a byproduct of which modules were composed for other reasons) rather than deliberate.

The driving product philosophy: world data should eventually exercise every feature the engine
supports — not just what already looks good — across worlds of deliberately varied scale/
composition, so SimQ scoring becomes an honest diagnostic across the whole corpus. Turning
everything on in every world at once would make troubleshooting harder (a regression could not be
attributed to a specific mechanic), so the corpus is organized into test-pyramid-style tiers:

- **Unit tier** — new, small, synthetic-content-OK worlds, each isolating exactly ONE gated
  mechanic with everything else at baseline. Template/synthetic content is acceptable here;
  narrative coherence does not matter — it is a controlled experiment.
- **End-to-end tier** — the 9 existing archetype worlds (`urban_political`, `dungeon_crawl`,
  `sandbox_world`, `wilderness_survival`, `highland_traverse`, `swamp_border_world`,
  `frontier_living_world`, `frontier_extended`, `generated_frontier_3_42`) get richer, bespoke,
  archetype-matched content (not templated) — the direct answer to "why does only
  `urban_political` have FACTION/INFORMATION content."
- **Stress tier** — new worlds specifically filling the scale-diversity gaps the investigation
  found (investigation.md §2 "Combinations NOT currently represented": many-factions/small-map,
  sparse-resources/large-map, feature-content-at-large-scale, etc.).
- **Regression/baseline tier** — today's already-calibration-anchored worlds, left alone as a
  stable control group. **No ticket in this epic touches this tier — it is a "do not touch"
  policy**, not an oversight.

Three decisions were already made by the user (via `AskUserQuestion`) during the investigation and
are binding on every child ticket:
1. **AGENCY**: author 1-2 NEW routing-capable worlds (unit tier). Do NOT reverse
   `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for any existing world — the 9 non-routing worlds stay
   AGENCY=C as archetype-correct, permanently.
2. **Branch B (self-model)**: pilot via one dedicated unit-tier world, built specifically to also
   serve as the real-load evidence-gathering step the investigation found was missing (this doubles
   as the informal pre-approval step — no separate pre-approval ticket is created).
3. **Content authoring approach**: hybrid by tier — template/synthetic content for new unit-tier
   worlds, bespoke archetype-matched content for existing end-to-end-tier worlds.

Per CLAUDE.md's Tier Routing rules, this epic ticket is **scope-only** — it tracks the 10 child
tickets below and does not implement anything directly.

## Scope
Track and sequence the following 10 child tickets, all created under
`tickets/todos/simq-corpus-tiers/` (see `SEQUENCE.md` in that folder for full ordering rationale):

1. **TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC** — Document the Unit/End-to-End/Stress/Regression
   corpus tier taxonomy, including which existing worlds map to which tier today and criteria for
   classifying future world additions.
2. **TCK-20260704-SIMQ-CORPUS-SCALE-METRIC** — Add "distinct populated factions" as an explicitly
   tracked scale metric alongside existing entity/region/resource-node counts.
3. **TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE** — Generalize `ENABLE_ADVENTURE_ROUTING`
   activation from `tools/evaluate_simq.py`'s hardcoded `simq_routing_test_*` scenario-name special
   case into the same per-world `feature_flags:` profile YAML mechanism already used for
   `ENABLE_BELIEF_ASSIMILATION`. Prerequisite for ticket 6. Does NOT change any existing world's
   AGENCY grade.
4. **TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO** — Author 2 new small unit-tier worlds
   (template/synthetic content): one isolating FACTION tension seeding, one isolating INFORMATION
   source-profile seeding, everything else at baseline.
5. **TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT** — Author 1 new unit-tier world piloting
   Branch B (self-model) activation with a real multi-entity, multi-tick calibration run — the
   first live-load evidence for this mechanic, with other flags kept at baseline to isolate the
   test.
6. **TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY** — Author 1 new unit-tier/archetype world with
   `ENABLE_ADVENTURE_ROUTING` ON by design from inception, at a "real" scale/archetype (not a
   minimal calibration-only world). Depends on ticket 3. Does NOT reverse the AGENCY-DA ruling for
   any existing world.
7. **TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION** — Author bespoke, archetype-matched FACTION
   tension and INFORMATION source-profile content into the 8 existing end-to-end-tier worlds beyond
   `urban_political`. Requires drift-check-and-update discipline against existing calibration
   anchors.
8. **TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS** — Author new stress-tier worlds filling the identified
   scale gaps: many-factions/small-map, sparse-resources-or-saturated-resources at contrasting map
   sizes, and FACTION/INFORMATION content combined with a large-scale population.
9. **TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS** — Folds in `docs/plans/audit_fix_plan.md`
   P2-D. Expand `data/content/social/faction_relationships.yaml` from 34 entries / 20-of-120 pairs
   (16.7%) toward the original 50%+ coverage target.
10. **TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL** — Folds in `docs/plans/audit_fix_plan.md`
    P2-E. Add a test asserting expected feature-flag states per scenario/world profile, covering the
    expanded flag surface tickets 3-9 introduce. Lands last by design.

## Out of Scope
- Any direct implementation (this is an epic ticket — implementation happens in the 10 child
  tickets)
- Reversing `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for any existing world
- Touching the regression/baseline tier (today's already-anchored worlds not named in tickets 7-8)
- Deciding the exact stress-tier world count/composition beyond the 3 gap categories named in
  ticket 8 (left to that ticket's own investigation phase)
- Resolving the `ResourceRegistry: STONE` gap discovered by `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`
  (tracked separately, `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`)

## Acceptance Criteria
- [x] All 10 child tickets exist under `tickets/todos/simq-corpus-tiers/` with correct frontmatter
      and cross-references to this epic
- [x] `tickets/todos/simq-corpus-tiers/SEQUENCE.md` documents ordering rationale and dependencies
- [x] Each child ticket's Related Tickets section references this epic ID
- [x] Ticket 6 explicitly references ticket 3 as a hard dependency
- [x] No child ticket proposes reversing the AGENCY-DA ruling for any of the 9 existing non-routing
      worlds
- [x] As child tickets complete, this epic's status is updated to reflect closed-out children (epic
      itself has no direct completion criteria beyond all 10 children reaching `tickets/done/`) —
      all 10 confirmed present in `tickets/done/` before this epic was closed

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC (child, order 1)
- TCK-20260704-SIMQ-CORPUS-SCALE-METRIC (child, order 2)
- TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE (child, order 3)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO (child, order 4)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT (child, order 5)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY (child, order 6)
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION (child, order 7)
- TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS (child, order 8)
- TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS (child, order 9)
- TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL (child, order 10)
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA — ruling this epic explicitly does NOT reverse
- TCK-20260702-SIMQ-UPLIFT2-FACTION — prior single-world FACTION activation this epic generalizes
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — prior corpus-diversification ticket; established the
  hazard-kind fix, population-stability verification pattern, and drift-check discipline this
  epic's children reuse
- TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP — separate, pre-existing gap; explicitly out of
  scope here

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` — full evidence base
  for this epic (file paths, line numbers, per-world content status, scale tables, blast-radius
  analysis); every child ticket must cite this file
- `docs/plans/audit_fix_plan.md` — P2-D (folded into ticket 9), P2-E (folded into ticket 10)
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/guidelines/design_patterns.md` — Pattern 6 (world-content compile-time-gated fields)

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — investigation for this epic
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — prior corpus-diversification
  precedent (hazard-kind fix, anchor drift-check pattern)
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG/` — DA documentation template

## Related Code Areas
- `src/worldbuilding/schema.py` — `WorldSpec` (FACTION/INFORMATION/self-model fields)
- `src/worldassembly/schema.py` — `WorldCompositionSpec`, `NormalizedWorldComposition`
- `src/domains/optimization/feature_flags.py` — `ENABLE_ADVENTURE_ROUTING`,
  `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_SELF_MODEL_COGNITION`
- `tools/evaluate_simq.py`, `tools/calibrate_simq.py` — calibration harness, profile YAML loading
- `config/simulation_quality/profiles/` — per-world `feature_flags:` blocks
- `data/worlds/` — the 10 compiled worlds
- `data/content/social/faction_relationships.yaml`

## Assumptions / Open Questions
- Epic assumes all 10 child tickets are independently implementable per `tickets/inprogress`
  workflow; no additional epic-level pre-approval step is required beyond the 3 user decisions
  already recorded in the investigation.
- Whether stress-tier world count settles at exactly 3 (per ticket 8's 3 named gap categories) or
  more is deferred to ticket 8's own investigation phase.

## Implementation Notes
Per this epic's own Tier Routing (scope-only, no direct implementation), all work happened in the
10 child tickets, each following the full Scope→Investigate→Plan→Review→Implement→Test→Verify→
Finalize pipeline independently. This epic ticket's own role was tracking, sequencing, and — for
several children — resolving genuine cross-ticket forks the child tickets' own investigations
surfaced but correctly deferred rather than deciding unilaterally (e.g. the COGNITION/INFORMATION
framing tension in ticket 5, the AC6-vs-scope-boundary tradeoff surfaced during the earlier
AGENCY-STASIS-COLLAPSE work this epic builds on).

Execution spanned two sessions/environments sharing this same working directory: tickets 1-5 were
implemented and verified in one continuous session; tickets 6-9 (`UNIT-WORLD-AGENCY`,
`E2E-CONTENT-EXPANSION`, `STRESS-WORLDS`, `FACTION-RELATIONSHIPS`) landed via a parallel session
running concurrently, discovered via git log when this session resumed; ticket 10
(`SCENARIO-FLAG-GUARDRAIL`) was implemented and verified last, closing the epic.

## Test Summary
Each child ticket ran and independently re-verified its own test suite; ticket 10's guardrail test
(55 passing cases across 7 test functions) is itself the corpus-wide regression test for this
epic's entire flag/content surface going forward. While finalizing ticket 10, a `make evaluate` run
surfaced 26 apparent FACTION-pillar regressions — investigated directly and confirmed to be
entirely a stale local `data/calibration/` cache artifact (fresh recalibration of an affected world
reproduced the committed anchor exactly), not a real regression. Refreshed via `make evaluate-full`
(61 scenarios); `make evaluate` now shows **0 regressions across 610 pillars** — the true,
corpus-wide state of the epic's output.

## Files Changed
See each child ticket's own Files Changed section for full detail. At a corpus level, this epic
took `data/worlds/` from 10 worlds to 17 (4 new unit-tier: `unit_faction_tension`,
`unit_information_source`, `unit_selfmodel_pilot`, `hero_guild_routing`; 3 new stress-tier:
`crowded_frontier`, `resource_dense_basin`, `frontier_marches`), promoted 8 of the original 10
worlds to End-to-end tier with bespoke FACTION/INFORMATION content, expanded
`data/content/social/faction_relationships.yaml`'s coverage, generalized `ENABLE_ADVENTURE_ROUTING`
activation onto the same profile-YAML mechanism every other flag uses, added a
`distinct_populated_factions` scale metric, documented the whole tier taxonomy, and added a
corpus-wide flag/content guardrail test — all without reversing the `AGENCY-DA` ruling for any of
the 9 originally-non-routing worlds.

## Completion Summary
All 10 child tickets landed in `tickets/done/`, closing this epic. The corpus now genuinely
exercises every Pattern-6-gated mechanic (FACTION, INFORMATION, self-model, AGENCY) across
deliberately varied scale/composition, organized into a test-pyramid-style tier structure
(Unit/End-to-end/Stress/Regression) specifically so a future pillar regression can be attributed to
a mechanic rather than lost in an undifferentiated "everything on everywhere" corpus — the
product-philosophy problem this epic was scoped to solve. All three of the user's binding decisions
(AGENCY via new dedicated worlds only, Branch B via one isolated pilot, hybrid content authoring by
tier) were honored by every child ticket, verified independently at each ticket's own Review phase
and again here at epic close. `make evaluate` confirms 0 regressions across the full,
freshly-recalibrated 610-pillar corpus.
