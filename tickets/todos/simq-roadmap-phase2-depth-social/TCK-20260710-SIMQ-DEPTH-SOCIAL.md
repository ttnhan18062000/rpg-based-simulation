---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-SOCIAL
phase: open
date: 2026-07-10
tags: [simulation-quality, social, world, corpus, calibration, feature-flags]
---

# TCK-20260710-SIMQ-DEPTH-SOCIAL

## Title
Extend SOCIAL pillar activation (ENABLE_SOCIAL_COOPERATION) to 2-3 more corpus worlds — Phase 2 Depth Wave 1

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This is `docs/plans/simq_development_roadmap.md` Phase 2 ("Depth Wave 1: SOCIAL"). SOCIAL is
currently active (grade S) in exactly one corpus world, `urban_political`, via
`TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`, which enabled `ENABLE_SOCIAL_COOPERATION` in that world's
calibration profile and fixed two engine bugs blocking it: (1) `apply_generation()` silently
dropping `feature_flags` across ticks, and (2) `CooperationPhase` storing a non-serializable
`CooperationDecisionResult` object in `property_updates`, breaking canonical state hashing. Both
fixes are already in `src/engine/apply.py` and `src/domains/cooperation/phase.py` — this ticket
does not need to re-find them, only build on them.

Per `TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT`'s finding (re-verified below, not just cited), SOCIAL
is pure feature-flag gating with **no `WorldCompiler` durable-state construction gap** — unlike
FACTION/INFORMATION, which needed compiler-level fixes (`FactionState`/`InformationSourceProfile`
construction) before content authoring could matter. `CooperationPhase` bootstraps its own first
records from **live** per-tick conditions (active strategic objective, combat risk/HP, faction-mate
proximity, default trust=0.5/familiarity=0.0 when no prior social history exists) rather than
requiring pre-seeded state. This makes SOCIAL the cheapest of the three flag/compiler-gated pillars
to expand — the playbook this Phase 2 wave is meant to prove before Phase 3 (FACTION+INFORMATION,
`tickets/todos/simq-roadmap-phase3-depth-faction-information/`) spends a larger budget on the two
pillars that do carry a compiler-level gap.

**Staleness check (explicitly required by this ticket's filing instructions, since the sibling
FACTION ticket found its own roadmap premise stale): re-verified directly against current repo
state, not trusted from the roadmap doc.** `grep -rn "ENABLE_SOCIAL_COOPERATION" config/simulation_
quality/profiles/*.yaml` returns exactly one hit: `urban_political.yaml`. All 13 other profile
files (`default`, `dungeon_crawl`, `frontier_extended`, `frontier_living_world`,
`frontier_marches`, `generated_frontier_3_42`, `hero_guild_routing`, `highland_traverse`,
`sandbox_world`, `simq_routing_test`, `swamp_border_world`, `unit_information_source`,
`unit_selfmodel_pilot`) have no `feature_flags:` entry for it. Independently confirmed via
`docs/simulation_quality/eval_matrix_results.md`: the 8-world FACTION/INFORMATION content
expansion (`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`) explicitly states "COMBAT/ECONOMY/
SOCIAL/WORLD/NARRATIVE/PROGRESSION/AGENCY held at their pre-expansion grades in every touched
anchor" — SOCIAL was untouched as a side effect of that unrelated work. **Conclusion: unlike
FACTION, SOCIAL's single-world-coverage premise is NOT stale.** It remains a genuine, unclaimed
expansion opportunity, exactly as the roadmap assumes.

## Scope
1. **Investigate phase (required first step, before any profile/content changes):** re-confirm the
   candidate short-list below against live `data/worlds/*/world.yaml` and
   `config/simulation_quality/profiles/*.yaml` (both may have drifted further by pickup time —
   do not trust this ticket's own snapshot without a spot-check, mirroring the sibling FACTION
   ticket's UQ-3 discipline). Read `src/domains/cooperation/phase.py`,
   `src/domains/cooperation/evaluators.py` (`HelpNeedEvaluator`), and
   `src/domains/cooperation/providers.py` (`PartnerCandidateProvider`) to confirm each candidate
   world's population actually satisfies `CooperationPhase`'s live-trigger conditions: entities
   need an active `strategic.current_objective_id` (set by normal adventuring/quest gameplay, e.g.
   via the `hero_adventurers` world-composition module) and at least 2 same-faction entities within
   `spatial_radius=15.0` (or `trust_history > 0.7`) for `PartnerCandidateProvider` to surface
   candidates. No FACTION/INFORMATION-style schema field (`initial_tension_level`,
   `information_source_profiles`) is required — this is a materially different content-authoring
   shape than the FACTION sibling ticket's, and the eventual Plan phase should not assume symmetric
   effort.
2. **Candidate worlds (identified by this ticket, to be re-verified not re-derived by Investigate):**
   - `dungeon_crawl` (32 entities, 4 regions, End-to-end tier) — party-based dungeon-crawl
     archetype; `hero_adventurers` module confirmed present
     (`grep hero_guild\|hero_adventurers data/worlds/dungeon_crawl/world.yaml`). Combat-risk-heavy
     framing lines up directly with `HelpNeedEvaluator`'s `combat_support_needed`/`healer_needed`
     triggers — plausibly the highest-yield candidate.
   - `frontier_living_world` (46 entities, 7 regions, End-to-end tier) — `bandit_road_trade_pressure`
     module gives a `bandit_company`/`merchant_league` tension backdrop; traders/guards banding
     together under bandit threat is a natural cooperation fit; `hero_adventurers`-derived
     population confirmed present.
   - `highland_traverse` (18 entities, 5 regions, End-to-end tier) — `settled_quarter` module
     (`town_council`/`merchant_league`, governance-vs-trade) gives a guild/service-hub framing;
     smallest of the three, useful as a lower-population data point.
   - Considered and set aside pending Investigate: `swamp_border_world` (similar
     governance/border-tension shape to `highland_traverse`, redundant as a third pick unless
     Investigate finds `highland_traverse` unsuitable); `frontier_extended` (largest world, no
     independent reason yet to prefer it over `frontier_living_world` for this wave); Unit/Stress/
     Regression-baseline tier worlds excluded by default per `corpus_tier_taxonomy.md`'s tier-purity
     discipline (mirrors the FACTION sibling ticket's Out-of-Scope reasoning) unless Investigate
     finds an explicit justification.
3. For each selected world (2-3 of the above, final count decided by Investigate): add
   `feature_flags: ENABLE_SOCIAL_COOPERATION: "ON"` to its
   `config/simulation_quality/profiles/<world>.yaml`, following `urban_political.yaml`'s existing
   block as the template.
4. Confirm (not necessarily author, per point 1 above) that each selected world's population
   satisfies the live-trigger conditions; if a world's entities never accrue an active objective or
   never cluster same-faction within radius, that is new information requiring a candidate swap or
   minimal population/composition adjustment — not a reason to force activation through unrelated
   means.
5. Recalibrate each selected world (3-seed matrix, following the corpus's existing calibration
   pattern) and add/update grade-anchor entries in `tests/simulation_quality/fixtures/
   grade_anchors.json` (+ `FAST_ANCHOR_KEYS` in `tests/simulation_quality/test_grade_regression.py`
   if applicable).
6. Run a corpus-wide regression sweep (`make evaluate` / `make evaluate-full` as appropriate) —
   per Pattern 6 activation history (the COGNITION-alongside-INFORMATION dual-emission drift
   documented in `eval_matrix_results.md`), a flag-gated pillar's activation can shift an adjacent
   pillar as a side effect even when the target pillar's own mechanism is flag-only; do not assume
   SOCIAL-only impact without running the full sweep.
7. Update `docs/simulation_quality/eval_matrix_results.md` and `corpus_tier_taxonomy.md` with the
   newly-activated worlds' grade tables/tier notes.
8. Extend `docs/parity_ledger/social_narrative.yaml`'s `SOC-007` entry ("Party/group cooperation is
   purpose-driven, not just proximity clustering," already `status: verified`) with `v2_evidence`
   covering the newly selected worlds, mirroring how the FACTION sibling ticket extends `FAC-012`
   rather than creating a new entry — unless Investigate finds a reason a new entry is warranted.
9. Track any newly-discovered engine bug as its own ticket rather than folding it into this
   ticket's scope (mirrors the FACTION sibling ticket's instruction and the INFORMATION-side
   precedent where 3 causally-linked kernel bugs surfaced during `urban_political`'s own
   activation).

## Out of Scope
- The FACTION/INFORMATION Phase 3 wave — filed as a sibling pair of tickets in
  `tickets/todos/simq-roadmap-phase3-depth-faction-information/`; different content-authoring
  shape (compiler-level gap vs. pure flag gating here), can run independently.
- Any `WorldCompiler`/schema/resolver engine work — this ticket's own investigation (re-verifying
  `TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT`) confirms none is needed; if Investigate finds
  otherwise for a specific candidate world, that is new information requiring a plan revision, not
  in-scope engineering to push through.
- Changing SOCIAL scoring weights/thresholds in `quality_scoring_contract.md` §5.
- Re-fixing the two engine bugs `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO` already closed
  (`apply_generation` feature-flag propagation, `CooperationPhase` serialization) — confirmed both
  fixes are already present in `src/engine/apply.py` and `src/domains/cooperation/phase.py`; this
  ticket only needs to consume them, not re-verify their internals line-by-line.
- Authoring any new Unit-tier SOCIAL-isolation world (no such world exists yet and none is
  requested by the roadmap for this phase).
- Adding SOCIAL content to Stress tier (`crowded_frontier`, `resource_dense_basin`), Unit tier, or
  `simq_routing_test`/regression-baseline worlds, absent an explicit tier-purity-exception
  justification from Investigate.
- Deciding the final 2-vs-3 world count or the exact candidate set — left to this ticket's own
  Investigate/Plan phases per the pre-filing instruction that world selection is deferred.

## Acceptance Criteria
- [ ] Investigate phase re-verifies the candidate short-list against live `data/worlds/` and
      `config/simulation_quality/profiles/` state (not this ticket's snapshot) and confirms each
      selected world's population satisfies `CooperationPhase`'s live-trigger conditions before any
      profile change is made
- [ ] 2-3 selected worlds each have `feature_flags: ENABLE_SOCIAL_COOPERATION: "ON"` added to their
      `config/simulation_quality/profiles/<world>.yaml`
- [ ] Each selected world compiles with 0 new warnings and holds its existing population-alive floor
      (per `corpus_tier_taxonomy.md`'s baseline expectations for its tier) through its calibration
      run length
- [ ] Each selected world's SOCIAL grade moves measurably off `C` (calibration_hits > 0 for
      `cooperation_event` or another SOCIAL-scored event type) across a 3-seed calibration matrix,
      with grade-anchor entries added to `grade_anchors.json` (+ `FAST_ANCHOR_KEYS` if applicable)
- [ ] `make evaluate` (full corpus sweep, not just `--dry-run`) exits 0 with 0 unattributed
      regressions (any cross-pillar drift, e.g. a COGNITION/other-pillar side effect, is identified
      and attributed, not silently accepted)
- [ ] `docs/parity_ledger/social_narrative.yaml`'s `SOC-007` extended (or a justified new entry
      added) with `v2_evidence` covering the newly selected worlds
- [ ] `eval_matrix_results.md` and `corpus_tier_taxonomy.md` updated with the newly-activated
      worlds' grade tables/tier notes
- [ ] Any newly-discovered engine bug is filed as its own ticket, not silently folded into this
      one's scope

## Related Tickets
- `docs/plans/simq_development_roadmap.md` Phase 2 — parent roadmap phase (source of this ticket)
- `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO` (done) — original SOCIAL activation in `urban_political`;
  this ticket extends the same `ENABLE_SOCIAL_COOPERATION` mechanism to more worlds and must not
  re-fix the two engine bugs it already closed
- `TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT` (done) — established SOCIAL has no compiler-level
  construction gap (unlike FACTION/INFORMATION); this ticket's Request Summary re-verifies that
  finding still holds rather than trusting the citation blindly
- `TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION` (done) — added `SocialScorer` emitters this ticket's
  calibration runs depend on
- `docs/plans/simq_development_roadmap.md` Phase 3 (FACTION + INFORMATION, filed as
  `tickets/todos/simq-roadmap-phase3-depth-faction-information/TCK-20260710-SIMQ-DEPTH-FACTION.md`
  and its INFORMATION sibling) — this ticket's actual cost should sanity-check that wave's larger
  effort budget once this one closes, per the FACTION ticket's own cross-reference

## Related Docs
- `docs/plans/simq_development_roadmap.md` — Phase 2 section (source of this ticket)
- `docs/simulation_quality/quality_scoring_contract.md` §5 SOCIAL — pillar definition, 11 scored
  event types (`cooperation_event`, `group_joined`, `group_expelled`, `contract_offer_created`,
  `contract_offer_accepted`, `contract_milestone_completed`, `contract_completed`,
  `contract_lapsed`, `contract_expired_offer`, `reputation_delta`, `social_memory_created`),
  scoring deltas table, `cooperation_dormant`/`social_structure_static`/`reputation_flat` dormancy
  penalties, and traceability path (flag check → proximity/personality conditions → contract
  offer timeline)
- `docs/guides/feature_flags.md` — `ENABLE_SOCIAL_COOPERATION` flag mechanism (default OFF,
  profile YAML `feature_flags:` block read by `tools/calibrate_simq.py::_load_profile_feature_
  flags()`)
- `docs/simulation_quality/corpus_tier_taxonomy.md` — 17-world tier structure; candidate worlds
  selected from End-to-end tier per its classification criteria
- `docs/simulation_quality/eval_matrix_results.md` — confirms SOCIAL held flat across the 8-world
  FACTION/INFORMATION content expansion (staleness-check evidence) and documents `urban_political`'s
  SOCIAL=S activation in detail
- `docs/guidelines/design_patterns.md` — Pattern 6 context (for contrast: SOCIAL does not use this
  pattern, it is pure flag gating, not compile-time field seeding)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO/` — `investigation.md`, `plan.md`,
  `test_plan.md`: original SOCIAL root-cause diagnosis and fix methodology (the two engine bugs,
  the profile-YAML flag-injection mechanism) this ticket's approach directly reuses
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT/investigation.md` — the no-compiler-
  gap finding for SOCIAL this ticket's Request Summary re-verifies

## Related Code Areas
- `src/domains/cooperation/phase.py` — `CooperationPhase.execute()`; flag check at line 40
  (`state.social_cooperation_enabled`), main per-tick evaluation loop
- `src/domains/cooperation/evaluators.py` — `HelpNeedEvaluator` (requires
  `entity.strategic.current_objective_id`; triggers: combat risk/near-death, HP < 30%/40%, unknown
  route, gold > 1000), `PartnerFitEvaluator`
- `src/domains/cooperation/providers.py` — `PartnerCandidateProvider.get_candidates()`
  (`spatial_radius=15.0`, same-faction filter, trust/familiarity defaults of 0.5/0.0 when no prior
  history exists — confirms no pre-seeded content is required)
- `src/domains/cooperation/services.py` — `CooperationDecisionService`, `CooperationIntentBridge`,
  `PartyObjectiveAlignmentService`, `PartyCohesionService`, `CooperationLearningService`
- `src/domains/optimization/feature_flags.py` — `ENABLE_SOCIAL_COOPERATION` default `FeatureMode.OFF`
- `src/engine/pipeline.py:158` — `run_phase("cooperation", ..., "ENABLE_SOCIAL_COOPERATION")` wiring
- `tools/calibrate_simq.py` — `_load_profile_feature_flags()` (profile YAML → engine state flag
  injection)
- `config/simulation_quality/profiles/{dungeon_crawl,frontier_living_world,highland_traverse}.yaml`
  — files to be edited (final set TBD by Investigate)
- `data/worlds/{dungeon_crawl,frontier_living_world,highland_traverse}/world.yaml` — candidate
  worlds' composition (`hero_adventurers` module presence confirmed via grep for this ticket's
  filing; population/faction-clustering details to be re-verified by Investigate)
- `tests/simulation_quality/fixtures/grade_anchors.json`,
  `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`)
- `docs/parity_ledger/social_narrative.yaml` — `SOC-007` entry to extend

## Assumptions / Open Questions
- **AQ-1:** This ticket assumes `CooperationPhase`'s live-trigger conditions (active strategic
  objective + same-faction proximity + default trust/familiarity) are already satisfied by normal
  adventuring gameplay in the three candidate worlds, requiring zero bespoke content authoring —
  a materially cheaper shape than FACTION/INFORMATION's schema-field seeding. This is inferred from
  reading the evaluator/provider code and from `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`'s own
  `urban_political` fix (which added no SOCIAL-specific world content, only the flag). If Investigate
  finds a candidate world's entities never accrue an active objective in practice (e.g. because a
  module wires objectives differently than assumed), that invalidates the "flag-only" cost estimate
  for that world and the candidate should be swapped, not forced.
- **AQ-2:** If fewer than 2 of the 3 candidates pan out, should this ticket's target count drop
  below "2-3," or should `swamp_border_world`/`frontier_extended` be promoted from the considered-
  and-set-aside list? Left to Investigate/Plan — default assumption if unresolved is to proceed
  with however many legitimate candidates exist rather than force a weak fourth pick.
- **AQ-3:** `docs/simulation_quality/corpus_tier_taxonomy.md`'s "as of 2026-07-07" tier mapping and
  `eval_matrix_results.md` may have further updates by the time this ticket is picked up —
  Investigate must spot-check both against live `data/worlds/*/world.yaml` and
  `config/simulation_quality/profiles/*.yaml`, not trust either doc as current without verification
  (mirrors the FACTION sibling ticket's UQ-3 and this ticket's own staleness re-check above).
- **AQ-4:** `layer: world` was chosen (matching the FACTION sibling ticket's own reasoning) because
  this ticket's actual mechanism is primarily per-world calibration-profile editing
  (`config/simulation_quality/profiles/`) plus confirmation of existing `data/worlds/` content, not
  engine-level schema/compiler/resolver work — that plumbing does not exist for SOCIAL and is
  confirmed unnecessary. `layer: simulation` was considered (matching
  `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`'s own choice, which did touch engine code) but rejected
  since this ticket's scope, unlike that one, is not expected to require engine changes.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
