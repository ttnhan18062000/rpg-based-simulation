---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE
phase: open
date: 2026-07-10
tags: [cognition, self-model, simulation-quality, calibration, investigation]
---

# TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE

## Title
Investigate whether Branch B (self-model) generalizes beyond `unit_selfmodel_pilot` to a real, already-populated archetype world

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This is Phase 4 (Depth Wave 3: COGNITION) of `docs/plans/simq_development_roadmap.md` — explicitly
flagged there as the roadmap's highest-uncertainty phase ("Why last: this is the least-proven
pillar"). COGNITION's only live-fire, multi-tick, multi-entity evidence is
`unit_selfmodel_pilot` (`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`), a purpose-built
16-entity, 1-region Unit-tier world that deliberately isolates only the self-model
*materialization* half of Branch B (`ENABLE_BELIEF_ASSIMILATION` kept OFF by that ticket's own
Scope item 3, so `InformationBeliefPhase` — which contains Branch B's query-routing logic —
structurally never executes there). Reaching even that pilot required
`TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` fixing 3 causally-linked bugs in one ticket:
`SelfModelUpdatePhase.run()` hardcoded `events=[]` (Step 1 fix), `pipeline.py`'s
`InformationBeliefPhase.apply(...)` call site was missing the `u.merge(...)` wrapper every sibling
phase in that file uses (Finding 4), and `EntityUpdate.self_model_bundle_set` was never durably
materialized into `EntityState.self_model` for ANY entity, ANY world, ever — requiring a new
`SelfModelPatch` (18th `ComponentPatch` subclass) added mid-implementation as a supplementary fix
(Finding 5). That ticket's own "Honesty note" states plainly: "Branch B does not fire in any shipped
calibration scenario as a result of this ticket... not a change to any shipped world's live
behavior." There is currently zero evidence this generalizes to a real, already-populated archetype
world with both flags ON simultaneously, exercising the full assimilate→route sequence.

This ticket is **investigation-only**: attempt to seed `self_model.knowledge.unknowns` for exactly
one real archetype world and honestly report whether Branch B's mechanism holds up outside its
isolated pilot, or whether more engine work is needed first. It does not scope a multi-world
rollout, and its Acceptance Criteria are "a documented, evidence-based answer," not "COGNITION
activated in world X" — a conclusion of "does not generalize cleanly, here's why" is a valid,
complete outcome.

**Candidate-world correction (found during scoping, must not be silently dropped):** the roadmap
text and this ticket's originating request both name `hero_guild_routing` as "a real archetype
world (candidate)... the corpus's most cognition-adjacent non-pilot world per its AGENCY/COGNITION
grades." Verifying this against `docs/simulation_quality/corpus_tier_taxonomy.md:136` and
`tests/simulation_quality/fixtures/grade_anchors.json` directly during scoping found this framing is
**not accurate as stated**:
- `hero_guild_routing` is classified **Unit-tier** in `corpus_tier_taxonomy.md`, described exactly
  as isolating "AGENCY/route-selection only via `ENABLE_ADVENTURE_ROUTING`" — the same
  single-mechanic-isolation category as `unit_selfmodel_pilot` itself, not the End-to-end/
  Regression-baseline "archetype" tier the roadmap's own Phase 4 framing contrasts against ("a real,
  already-populated archetype world rather than a small, deliberately-isolated pilot"). Its
  `config/simulation_quality/profiles/hero_guild_routing.yaml` sets only
  `ENABLE_ADVENTURE_ROUTING: "ON"` — `ENABLE_SELF_MODEL_COGNITION` is absent, and its existing
  `COGNITION` grade (`A`/`S` across 4 grade-anchor entries) is driven by `strategic_intelligence`
  (PP-30) signal from route-selection, not by self-model materialization at all.
- The one genuine End-to-end/Regression-baseline-tier world with any self-model content already
  populated is **`urban_political`** (`corpus_tier_taxonomy.md:126`: "the only world with any
  FACTION/INFORMATION/self-model content populated"). `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` already
  seeded a `pending_self_model_information_events` entry there (`pop_1`, `answer_kind: "unknown"`,
  `material.moon_resin.source`) as part of its own Step 8 world-content change — but
  `ENABLE_SELF_MODEL_COGNITION` was deliberately kept OFF in its shipped profile (orthogonal to that
  ticket's code fix, per its UQ-2 resolution).

Given this, the Investigate step below must explicitly re-confirm which candidate — `hero_guild_routing`
(real-archetype *scale*, already routing-active, but Unit-tier by classification) or `urban_political`
(genuine archetype/baseline tier, already has seeded self-model content, flag currently OFF) — best
satisfies the roadmap's actual intent, rather than defaulting to the as-given `hero_guild_routing`
framing uncritically.

## Scope
1. **Investigate step (required first):** using current calibration data
   (`tests/simulation_quality/fixtures/grade_anchors.json`,
   `docs/simulation_quality/corpus_tier_taxonomy.md`, `docs/simulation_quality/eval_matrix_results.md`),
   confirm which single real, already-populated world is the best-evidenced candidate for this
   investigation — `hero_guild_routing` or `urban_political` (see Candidate-world correction above)
   — and record the reasoning. Do not proceed to seeding without this confirmation.
2. For the confirmed candidate world, seed (or confirm already-seeded)
   `pending_self_model_information_events` content and scope `ENABLE_SELF_MODEL_COGNITION: "ON"` —
   as a test/verification-scoped override for this investigation, not necessarily a shipped profile
   default (mirrors `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`'s UQ-2 resolution: the flag is orthogonal to
   the mechanism and does not need to ship ON to be evaluated).
3. If the candidate is `urban_political`, also scope `ENABLE_BELIEF_ASSIMILATION: "ON"` alongside
   `ENABLE_SELF_MODEL_COGNITION` for at least one investigation run — this is the specific
   combination `unit_selfmodel_pilot` deliberately never exercised (it kept
   `ENABLE_BELIEF_ASSIMILATION` OFF), and is required to observe Branch B's actual query-routing
   half, not just materialization.
4. Run a real multi-tick calibration (following the existing 200+ tick, multi-seed pattern used by
   `unit_selfmodel_pilot` and the corpus's other calibration anchors) against the candidate world
   with the flag(s) scoped ON, and observe: does `self_model.knowledge.unknowns` populate for real
   entities in this world's actual (non-synthetic) population; does `InformationBeliefPhase`'s
   Branch B route a query end-to-end across a real tick boundary in this world's real compiled
   state (not just the hand-built state test in `test_fused_loop.py`); does the resulting
   COGNITION/INFORMATION pillar grade behave as expected or reveal a new gap.
5. Document the result honestly in a form usable by the Coverage Decision Gate (Phase 5 of the
   roadmap) — whichever of the three outcomes actually occurred:
   (a) the mechanism generalizes cleanly to this real world — record the evidence and grade;
   (b) it generalizes with a scoped caveat (e.g. only reachable at a certain population/content
   density) — record the caveat precisely;
   (c) it does not generalize and more engine work is needed — record exactly what broke and why,
   with enough detail that a follow-up engine-fix ticket could be scoped directly from this
   investigation's findings without re-deriving them.
6. Do NOT modify any shipped calibration profile's default flags as a side effect of this
   investigation unless Acceptance Criteria explicitly requires it — investigation runs use scoped
   per-test/per-run overrides, matching precedent (`unit_selfmodel_pilot`'s own flag stayed
   world-local, not global).
7. Update the relevant parity ledger entries (`docs/parity_ledger/strategic_cognition.yaml`,
   cross-referencing `STRAT-245`/`SUB-374`, and `docs/parity_ledger/infrastructure.yaml`'s
   `INFRA-259`/`INFRA-260` `support_boundary` text) if this investigation changes what is true about
   Branch B's real-world reachability — the current `support_boundary` language already says
   real-world reachability beyond the pilot is unverified; this must be corrected either direction
   based on what this ticket actually finds.

## Out of Scope
- Any multi-world rollout or turning `ENABLE_SELF_MODEL_COGNITION` ON in more than the one
  confirmed candidate world's profile — per the roadmap's explicit instruction, "Do not commit to a
  multi-world rollout until this single-world investigation reports back."
- Fixing any engine gap this investigation discovers — if outcome (c) above occurs, file a separate,
  clearly scoped follow-up engine-fix ticket rather than patching engine code inside this
  investigation ticket without a scope update first (mirrors `unit_selfmodel_pilot`'s own precedent
  for handling discovered bugs).
- Combining self-model activation with `ENABLE_ADVENTURE_ROUTING`/AGENCY in the same investigation
  run — `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`'s Finding 5 blast-radius sweep flagged this exact
  three-way combination (`AdventureRouteGenerator`/`scoring.py`) as the only live conditional-behavior
  consumers of `entity.self_model`, and no shipped profile combines these flags today — deliberately
  excluded here to keep this investigation single-variable (self-model in a real world), consistent
  with `unit_selfmodel_pilot`'s own isolation precedent and the roadmap's explicit exclusion of that
  third combination.
- The Phase 5 Coverage Decision Gate itself — this ticket feeds evidence into that future decision,
  it does not make the decision.
- Any change to `SelfAssessmentService`, `NeedInterpretationService`, or `CapabilityEstimateService`
  (the other 3 steps of `SelfModelUpdatePhase`'s pipeline) — out of scope for the same reason
  `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` excluded them (this ticket touches only Step 1's
  event-driven path in the confirmed candidate world).
- Retroactively re-deciding `hero_guild_routing`'s or `unit_selfmodel_pilot`'s existing tier
  classification in `corpus_tier_taxonomy.md` — the candidate-world correction above is scoped to
  choosing the right target for *this* investigation, not relitigating prior tickets' tier calls.

## Acceptance Criteria
- [ ] Candidate-world choice (`hero_guild_routing` vs. `urban_political`, or another world if
      evidence points elsewhere) is confirmed against current `grade_anchors.json` and
      `corpus_tier_taxonomy.md` data and the reasoning is recorded in this ticket's Implementation
      Notes before any seeding work begins
- [ ] `self_model.knowledge.unknowns` seeding attempted for the confirmed candidate world with
      `ENABLE_SELF_MODEL_COGNITION` scoped ON for at least one real, multi-tick (200+), calibration
      run against that world's real compiled population (not a hand-built state test)
- [ ] If the candidate is `urban_political` (or any world where `ENABLE_BELIEF_ASSIMILATION` is
      also relevant), at least one run scopes both `ENABLE_SELF_MODEL_COGNITION` and
      `ENABLE_BELIEF_ASSIMILATION` ON together, to exercise Branch B's query-routing half, not only
      materialization
- [ ] A documented, evidence-based answer to "does Branch B generalize beyond
      `unit_selfmodel_pilot`" is recorded — citing specific observed behavior (grade values, event
      counts, whether/where the mechanism broke down) — not a restatement of the pilot's own
      already-known result
- [ ] If a gap or bug is found, it is documented with enough detail (file:line, exact failure
      condition) that a follow-up engine-fix ticket could be scoped directly from this
      investigation's findings, and that follow-up is named/referenced (even if not yet filed) in
      this ticket's Completion Summary
- [ ] Relevant parity ledger entries (`strategic_cognition.yaml`, `infrastructure.yaml`
      `INFRA-259`/`INFRA-260`) are updated to reflect whatever this investigation actually finds
      about real-world reachability, replacing the current "unverified beyond the pilot" language
      one way or the other
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions on the pre-existing corpus (this
      investigation must not silently break any existing calibration anchor)

## Related Tickets
- `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` (done) — the 3-bug fix chain this ticket tests for real-world
  generalization; source of the "Honesty note" this ticket directly follows up on
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT` (done) — the sole existing pilot-world
  evidence this ticket attempts to extend beyond
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` (done, referenced) — authored `hero_guild_routing` as
  a Unit-tier, AGENCY-isolating world; relevant to the candidate-world correction above
- Parent: Phase 4 of `docs/plans/simq_development_roadmap.md` — this is that roadmap's ticket 4.1
  ("1 firm" ticket per the roadmap's own Estimated Ticket Count table); any follow-up engine-fix or
  additional-world tickets this investigation surfaces are Phase 4's "2-4 contingent" tickets, not
  pre-filed here

## Related Docs
- `docs/plans/simq_development_roadmap.md` — Phase 4 section (source of this ticket's framing and
  explicit "investigate one world first, do not pre-size" instruction)
- `docs/simulation_quality/quality_scoring_contract.md` §5 COGNITION section — pillar definition,
  scored event types (`self_model_updated`, `belief_updated`, `decision_divergence_detected`, etc.),
  traceability path
- `docs/simulation_quality/corpus_tier_taxonomy.md` — world tier classifications; source of the
  candidate-world correction (lines 126, 136)
- `docs/simulation_quality/eval_matrix_results.md` — existing `unit_selfmodel_pilot` and
  `hero_guild_routing` sections; the pattern this investigation's own results section should follow
- `docs/cognition/self_model_contract.md`, `docs/cognition/README.md` — Branch B's documented
  contract, already corrected by `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` Step 10 to describe the
  compile-time-seed event source and `SelfModelPatch` materialization mechanism
- `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-245`), `docs/parity_ledger/infrastructure.yaml`
  (`INFRA-259`, `INFRA-260`), `docs/parity_ledger/substrate.yaml` (`SUB-374`) — the parity entries
  this investigation's findings must reconcile against
- `docs/guidelines/design_patterns.md` Pattern 6 — the compile-time pillar activation pattern
  underlying `pending_self_model_information_events`/`pending_information_responses`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-BRANCH-B/` — full investigation/plan for the 3-bug fix
  chain, including the Finding 4/Finding 5 discoveries and the explicit "Honesty note" this ticket
  follows up on
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT/` — the pilot world's own
  plan/methodology (12-step plan, 3-seed/200-tick calibration pattern) this investigation should
  reuse where applicable, adapted to a real archetype world instead of a purpose-built isolated one

## Related Code Areas
- `src/cognition/self_model_phase.py::SelfModelUpdatePhase.apply()`/`.run()` — Step 1 event
  assimilation; confirmed still reads `state.pending_self_model_information_events` grouped by
  `actor_id`
- `src/engine/patches.py::SelfModelPatch` (line ~629) — durable materialization into
  `EntityState.self_model`; confirmed present, `is_noop()`/`merge()`/`apply()` structurally mirror
  `KindPatch`
- `src/core/self_model.py::SelfModelBundle`, `KnowledgeModelComponent`, `UnknownFact`,
  `KnowledgeFact` — the self-model data shapes this investigation seeds/observes
- `src/domains/information/phase.py::InformationBeliefPhase.apply()` — Branch B's query-routing
  logic, the consumer of `self_model.knowledge.unknowns`
- `src/engine/pipeline.py:152` — the `u.merge(...)`-wrapped `information_belief` call site
  (Finding 4 fix)
- `config/simulation_quality/profiles/hero_guild_routing.yaml`,
  `config/simulation_quality/profiles/urban_political.yaml` — candidate worlds' feature-flag profiles
- `data/worlds/hero_guild_routing/world.yaml`, `data/worlds/urban_political/world.yaml` — candidate
  worlds' content, including `urban_political`'s existing `pending_self_model_information_events`
  seed
- `tests/simulation_quality/fixtures/grade_anchors.json`, `tests/simulation_quality/test_grade_regression.py`
  — grade-anchor data this ticket must both read (to confirm the candidate) and extend (if new
  anchors are added)
- `tests/integration/domains/test_fused_loop.py` — existing hand-built-state Branch B tests this
  investigation's real-world runs should be compared against

## Assumptions / Open Questions
- UQ-1: The candidate-world correction above assumes `corpus_tier_taxonomy.md`'s Unit vs.
  End-to-end/Regression-baseline tier distinction is the correct proxy for the roadmap's own "real
  archetype world" language. If a future reader judges `hero_guild_routing`'s real-archetype *scale*
  (31 entities, 4 regions) makes it an acceptable substitute despite its Unit-tier classification,
  that would invalidate this ticket's recommendation to re-verify against `urban_political` — this
  should be settled explicitly in the Investigate step (Scope item 1), not assumed either way here.
- UQ-2: Whether `urban_political`'s pre-existing `pending_self_model_information_events` seed
  (`pop_1`, `material.moon_resin.source`, added by `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` Step 8) is
  still present and valid against the current compiled world, or needs re-verification/re-seeding —
  should be confirmed empirically during investigation, not assumed from the prior ticket's
  Implementation Notes alone.
- UQ-3: Whether "generalizes" for Acceptance Criteria purposes requires Branch B's query-routing
  half to fire end-to-end in the real world's compiled state, or whether confirming only the
  materialization half (matching `unit_selfmodel_pilot`'s own scope) is sufficient for this
  ticket's Acceptance Criteria to be considered met with an honest "materialization-only" finding.
  Default: per Scope item 3/4 above, at least one run must attempt to exercise the full
  materialization + routing sequence (both flags ON) — a materialization-only result is an
  acceptable, complete, and honestly-reported *outcome* of that attempt, but the attempt itself is
  required, not optional.
- `layer: world` was chosen because this ticket's actual work (candidate-world seeding, real-world
  calibration runs, tier-taxonomy reconciliation) is world-content/calibration-shaped, matching
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`'s own layer choice — not `simulation` (used
  by the underlying `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` engine-fix ticket) or `ai`/`strategy`
  (this repo's `ai` layer tag denotes the Claude agent system, not gameplay cognition, per the
  registered `ai` tag's own note). If a future reader judges the engine-investigation angle
  dominates once work begins, `layer: simulation` would be the next-best fit.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
