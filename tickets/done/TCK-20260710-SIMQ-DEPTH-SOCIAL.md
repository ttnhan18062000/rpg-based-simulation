---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-SOCIAL
phase: done
date: 2026-07-10
tags: [simulation-quality, social, world, corpus, calibration, feature-flags]
---

# TCK-20260710-SIMQ-DEPTH-SOCIAL

## Title
Extend SOCIAL pillar activation (ENABLE_SOCIAL_COOPERATION) to 2-3 more corpus worlds — Phase 2 Depth Wave 1

## Status
DONE

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

Followed `staging_artifacts/TCK-20260710-SIMQ-DEPTH-SOCIAL/plan.md`'s 6 steps exactly, with two
deviations (both required by the actual data, recorded here and in the plan's own Deviations
section):

1. **Flag activation.** Added `ENABLE_SOCIAL_COOPERATION: "ON"` to
   `config/simulation_quality/profiles/frontier_living_world.yaml` and
   `config/simulation_quality/profiles/highland_traverse.yaml`, matching `urban_political.yaml`'s
   existing pattern. `dungeon_crawl.yaml` (rejected candidate, confirmed by Investigate: no
   settlement/civilian module means no population ever accrues `current_objective_id`, so
   `HelpNeedEvaluator`'s hard gate never opens — 0 cooperation events under a live probe) and
   `urban_political.yaml` (existing control) both show zero diff.

2. **Recalibration (3 seeds x 2 worlds, against the committed profile YAML, not an env-var
   probe).** Results:
   - `frontier_living_world`: SOCIAL C → S all 3 seeds (545 / 903 / 625 `cooperation_event`s at
     seed 42/123/456).
   - `highland_traverse`: SOCIAL C → S all 3 seeds (1496 / 1667 / 715 events).
   - **Deviation from plan.md's stated expectation** ("Every other pillar field... must remain
     byte-identical"): `frontier_living_world_seed123_200t`'s NARRATIVE moved B → A, and
     `frontier_living_world_seed456_200t`'s PROGRESSION moved B → C. Both are within the grade
     regression suite's ±1 letter band tolerance. Attribution: `CooperationPhase` is a genuine
     per-tick decision phase (assigns objectives, forms partner candidates, can affect entity
     routing) unlike the purely additive scorers activated by prior pillar work — once active it
     deterministically perturbs each seed's downstream entity trajectory, which can cascade into
     other pillars' event counts. This is expected engine behavior for a real phase activation,
     not a bug, and per the parent task's own instruction ("Update the SOCIAL field (and any other
     pillar fields that shift)"), both fields were updated to the real observed values rather than
     left stale. `highland_traverse` showed no such cascade in any of its 3 seeds — the effect is
     population/composition dependent.
   - All 6 touched `grade_anchors.json` entries updated in place (no new keys minted, all already
     in `FAST_ANCHOR_KEYS`).

3. **Corpus-wide regression sweep** (`python3 tools/evaluate_simq.py`, the full non-`--dry-run`
   sweep — ~9.5 minutes wall clock for the ~60-key fast corpus, run in the background and polled to
   completion). Found 3 REGRESS pillars, **all in worlds this ticket does not touch**:
   `dungeon_crawl_seed42_200t` (COMBAT A→C, PROGRESSION A→C) and `urban_political_seed42_200t`
   (PROGRESSION A→C). Confirmed unrelated to this ticket by: (a) zero diff exists to either world's
   profile YAML, world content, or any engine code; (b) the same grades reproduce deterministically
   under a standalone `calibrate_simq.py` re-run for each world in isolation. Most likely cause
   (not confirmed): the recent `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` population fix for
   exactly these two worlds left their anchors stale. **Filed as a follow-up ticket**,
   `tickets/todos/TCK-20260712-SIMQ-DUNGEON-URBAN-ANCHOR-DRIFT.md` (hotfix, P1), per this ticket's
   own Scope point 9 discipline — not fixed here (`dungeon_crawl`/`urban_political` anchors and
   profiles remain byte-identical to their pre-ticket state). The already-documented pre-existing
   COGNITION signal from `ENABLE_BELIEF_ASSIMILATION` (prior INFORMATION expansion ticket) was
   present in both `frontier_living_world`/`highland_traverse` before this ticket and did not move
   — correctly not misattributed to this ticket's SOCIAL flag flip.

4. **SOC-007 parity-ledger fix.** Corrected `v2_evidence`'s stale path
   (`src/systems/groups.py` → `src/systems/world_systems/groups.py`, class `GroupSystem` was
   already correct) and replaced the broken `test_path`
   (`tests_v2/parity/test_group_coordination.py`, which does not exist) with
   `tests/unit/social/test_social_party_regression.py::test_no_proximity_only_groups` (confirmed
   real and passing). Extended `v2_evidence` with a corpus-scale corroboration clause citing the
   two newly-activated worlds' `seed{42,123,456}_200t` runs. No other `SOC-*` entry touched.

5. **Docs.** Added SOCIAL-activation writeups to `eval_matrix_results.md` for
   `frontier_living_world` and `highland_traverse` (following the existing FACTION/INFORMATION
   section format), plus a `dungeon_crawl` rejection note with the structural reason and empirical
   zero-event evidence. Updated `corpus_tier_taxonomy.md`'s three affected world rows. Ran
   `make knowledge-index-update` (2 files re-embedded) since `docs/` content changed.

6. **Full regression pass.** All of test_plan.md's scoped pytest commands were run. Two categories
   of pre-existing, unrelated failures surfaced (both confirmed unrelated to this ticket's changes
   — no diff touches the code paths involved):
   - `tests/simulation_quality/test_grade_regression.py`/`tests/simulation_quality/`:
     `dungeon_crawl_seed42_200t` and `urban_political_seed42_200t` fail (same drift as point 3
     above — expected, tracked in the same follow-up ticket).
   - `tests/unit/social/test_group_lifecycle_fields.py::test_group_canonical_dict_has_no_missing_keys`
     (stale `EXPECTED_KEYS` missing `composition_score`) and
     `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`'s two scenario tests
     (asserting a pre-serialization-fix `.selected_posture` attribute access on what
     `phase.py:139` now intentionally stores as a plain string) — both pre-existing, confirmed via
     code-path analysis (this ticket makes zero changes to `src/domains/cooperation/` or
     `src/systems/world_systems/groups.py`). `tests/perf/test_phase7_social_cooperation_budget.py`
     also showed one apparently load-dependent flaky failure (27.8ms vs. 25ms budget in one run,
     passed in another, identical code both times). **Filed as a second follow-up ticket**,
     `tickets/todos/TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS.md` (hotfix, P2) — not fixed
     here, since this ticket's scope is profile-YAML activation plus the one parity-ledger entry,
     not stale-test repair in unrelated files.
   - All other scoped commands (cooperation domain unit/integration — 30 passed;
     `tests/unit/social/` minus the one stale test — 187 passed; observability event-extractor
     tests — 63 passed; grade regression minus the 2 unrelated failures — 70/72 passed;
     `tests/simulation_quality/` full — 457 passed, 2 skipped, 2 unrelated failures) passed clean.

**Two follow-up-candidate observations identified but explicitly NOT actioned in this ticket**
(both noted in investigation.md, both out of this ticket's stated scope):
1. `docs/simulation/domains/cooperation_contract.md` is stale relative to live code — missing the
   `current_objective_id` hard-gate in its trigger table, references non-existent file names
   (`contract_service.py`/`group_evaluator.py`/`partner_scoring.py`/`posture.py`) instead of the
   live `services.py`/`providers.py`/`postures.py`.
2. The vestigial `state.social_cooperation_enabled` dead-flag check at
   `src/domains/cooperation/phase.py:40` (always defaults `True`, never set anywhere, harmless but
   confusing) — a candidate for a small cleanup ticket, not touched here since it is engine code
   and this ticket's Out of Scope explicitly excludes engine work.

## Test Summary

- `pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ -q` — 30 passed.
- `pytest tests/unit/social/ -q` — 187 passed, 1 failed (pre-existing, unrelated — see follow-up
  ticket `TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS`).
- `pytest tests/unit/observability/test_event_extractor_social_faction.py
  tests/unit/observability/test_event_extractor_social_memory.py -q` — 63 passed.
- `pytest tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py
  tests/perf/test_phase7_social_cooperation_budget.py -q` — 1 passed, 2 pre-existing failures
  (same follow-up ticket).
- `pytest tests/simulation_quality/test_grade_regression.py -q` — 70 passed, 2 pre-existing
  failures (`dungeon_crawl_seed42_200t`, `urban_political_seed42_200t` — follow-up ticket
  `TCK-20260712-SIMQ-DUNGEON-URBAN-ANCHOR-DRIFT`).
- `pytest tests/simulation_quality/ -q` — 457 passed, 2 skipped, 2 pre-existing failures (same as
  above).
- `pytest tests/unit/social/test_social_party_regression.py::test_no_proximity_only_groups -v` —
  1 passed (SOC-007's corrected `test_path`).
- `python3 tools/evaluate_simq.py` (full corpus sweep, non-`--dry-run`) — 710 pillars checked, 3
  REGRESS, all attributed to the pre-existing, unrelated `dungeon_crawl`/`urban_political` drift.

## Files Changed

- `config/simulation_quality/profiles/frontier_living_world.yaml`
- `config/simulation_quality/profiles/highland_traverse.yaml`
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `docs/parity_ledger/social_narrative.yaml`
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/simulation_quality/corpus_tier_taxonomy.md`
- `tickets/todos/TCK-20260712-SIMQ-DUNGEON-URBAN-ANCHOR-DRIFT.md` (new, follow-up)
- `tickets/todos/TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS.md` (new, follow-up)

## Completion Summary

SOCIAL pillar activation (`ENABLE_SOCIAL_COOPERATION`) extended from 1 to 3 corpus worlds. Both
`frontier_living_world` and `highland_traverse` moved SOCIAL C → S across all 3 seeds via pure
feature-flag activation in their calibration profile YAML — no engine, `WorldCompiler`, or content
changes, consistent with the ticket's Out-of-Scope guarantee. `dungeon_crawl` was investigated as
the third candidate and **rejected**: it has no settlement/civilian module, so no entity ever
accrues `entity.strategic.current_objective_id`, and `HelpNeedEvaluator`'s hard gate
(`evaluators.py:34-35`) never opens — confirmed empirically via a live probe showing 0
`cooperation_event`s. This is **not** an AQ-2 "fewer than 2 candidates" situation: 2 of the
original 3 candidates panned out, so no 4th candidate (`swamp_border_world`/`frontier_extended`)
was promoted, per the plan's own resolution of that open question.

The required full corpus regression sweep (`tools/evaluate_simq.py`, non-dry-run) surfaced 3
REGRESS pillars, all in `dungeon_crawl_seed42_200t`/`urban_political_seed42_200t` — worlds this
ticket does not touch. Confirmed unrelated (zero diff to either world's profile/content/engine
code; reproduces identically in standalone isolation) and filed as a separate follow-up ticket
(`TCK-20260712-SIMQ-DUNGEON-URBAN-ANCHOR-DRIFT`, hotfix/P1) rather than silently absorbed or
fixed out-of-scope. The Step 6 regression pass separately surfaced 3 pre-existing, unrelated test
failures (a stale `EXPECTED_KEYS` set in a group-canonical-dict test, two scenario tests asserting
a pre-serialization-fix API shape, and one apparently load-dependent perf-budget flake) — also
filed separately (`TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS`, hotfix/P2).

`docs/parity_ledger/social_narrative.yaml`'s SOC-007 entry (P0) had its stale `v2_evidence` file
path and broken `test_path` corrected, and was extended with corpus-scale corroboration from the
two newly-activated worlds. `eval_matrix_results.md` and `corpus_tier_taxonomy.md` were updated
with the new SOCIAL grade tables/tier notes and the `dungeon_crawl` rejection rationale.

Two follow-up-candidate observations from investigation.md were explicitly identified but **not**
actioned in this ticket, per its Out-of-Scope discipline (no engine-code changes permitted):
(1) `docs/simulation/domains/cooperation_contract.md` is stale relative to live code (missing the
`current_objective_id` hard-gate, wrong file-name references); (2) the vestigial
`state.social_cooperation_enabled` dead-flag check at `src/domains/cooperation/phase.py:40`
(always defaults `True`, unrelated to the real gating mechanism) is a candidate for a small
cleanup ticket. Both are noted only, not fixed, and not filed as tickets here since neither rises
to the level of a newly-discovered *bug* the way the two drift findings above do — they remain
documented candidates for whoever picks up the roadmap's next phase.
