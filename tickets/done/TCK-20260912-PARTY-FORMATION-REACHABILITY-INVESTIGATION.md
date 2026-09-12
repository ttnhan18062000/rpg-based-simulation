---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION
phase: done
date: 2026-09-12
tags: [cognition, social]
---

# TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION

## Title
Confirmed genuinely broken (not rare, not density-related) and fixed: `CooperationPosture.JOIN_PARTY` — the designed-but-never-connected accept half of recruitment-offer party formation — is now wired; real groups form and `entity.social.trust_history` demonstrably accumulates in a real run

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Surfaced during `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`'s own
real instrumented reproduction: a real 500-tick `frontier_living_world` episode (seed 7) produced
2470 real `cooperation_event`s and **zero groups ever formed** (`state.groups` empty for the
entire run, confirmed by direct instrumentation, not inferred). That investigation found two real,
live, correctly-wired trust-writing mechanisms — a party-cohesion-collapse penalty and a same-
party-betrayal penalty — that both require a party/group to exist first, and neither got a single
chance to fire because none ever formed.

**This is bigger than a trust-accumulation problem — party formation is the keystone for this
whole thread, not an adjacent curiosity.** If it never occurs under real conditions, then
everything gated on `state.groups` being non-empty is equally dormant: `PartyCohesionService`'s
own leader/member dynamics, the `FORM_PARTY` adventure route and its own scoring machinery
(`src/domains/adventure/generator.py`, `src/ai/goals/adventure_scorer.py`,
`src/systems/social_systems/party_composition.py`), **both real, live trust-writing mechanisms**
`TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION` confirmed (the party-
cohesion-collapse penalty and the same-party-betrayal penalty), and plausibly party-relevant
`SocialBond.role` promotion from the broader Dormant Mechanism epic. A single 500-tick run not
forming a party could be a rare-but-real outcome, or it could mean the whole party subsystem is a
keystone-unreachable mechanic behind which several other real, tested mechanisms sit dormant —
this ticket exists to determine which, not to assume either one.

**This ticket explicitly inherits the "trust demonstrably accumulates in a real run" acceptance
bar** from `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`, closed on its
own narrower claim (two dead trust-writing mechanisms identified, one inline-shortcut repaired,
cooperation/appraisal separation confirmed as intended design) precisely because that repair,
while correct, is itself party-gated and therefore not demonstrable until this ticket's own
question is resolved. Same pattern as the survivor-reconstruction arc: position → identity → (now)
party formation, each layer only visible once the one beneath it was fixed.

## Blocking Dependency (added 2026-09-12, via peer review — read before picking this up)
**Do not start this investigation until `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-
DIVERGENCE` (the `count: N` spawns-one-entity-per-group bug) is fixed and landed.** Party formation
needs multiple compatible entities in proximity; the current count-expansion bug means
`frontier_living_world` spawns roughly one entity per population group, scattered by region —
substantially under-populated relative to what the world declares. Investigating party-formation
reachability against this under-populated world risks exactly the false-negative trap this whole
audit arc has hit twice already (the dead-episode trap; the grief/nemesis trap): concluding a
mechanism can't fire from a run that never gave it a real chance to.

**Required first step once picked up**: re-measure `state.groups` on a real run of the
post-count-expansion world, before any party-formation-specific investigation begins. If parties
start forming once density is real, this ticket's own premise dissolves — trust may already
accumulate without further fixes here, meaning the transferred acceptance bar (see below) is
satisfied by the count-expansion fix alone, and that should be reported as such rather than
investigating a question the density fix already resolved. Only if `state.groups` stays empty at
real density does the reachability investigation below proceed as originally scoped.

## Scope
- Determine, with real evidence (direct instrumentation of a real run, not code-reading alone):
  does the `FORM_PARTY` route ever actually get selected and successfully executed under real
  gameplay conditions? Check across more than one seed/scenario if the first reproduction doesn't
  settle it — a single non-forming run is not sufficient evidence that it never can.
- If party formation is reachable but rare: characterize the real conditions under which it
  occurs (what has to be true about candidate eligibility, scoring, motivation) and how rare, with
  real numbers from real runs — not a guess.
- If party formation is genuinely unreachable (a real bug, not rarity): trace to the specific
  root cause (a scoring weight that never favors it, an eligibility check that's too strict, a
  missing wiring step) with the same rigor this whole audit arc has applied elsewhere — confirmed
  why, not just confirmed that.
- Identify every other real mechanism gated on `state.groups`/party existence that this finding
  would also affect, so the blast radius is documented even if not all of it is fixed here.
- Once root-caused: decide the fix approach (if any) via peer review before implementing, given
  the potentially wide blast radius this ticket's own Request Summary already names.

## Out of Scope
- `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`'s own trust-specific
  fix — proceeds independently; this ticket investigates the deeper, separate question that
  investigation surfaced but explicitly did not chase, per peer review's own routing decision.
- Fully fixing every downstream consumer this finding implicates (party cohesion dynamics,
  `SocialBond.role` promotion, etc.) — this ticket determines reachability and root cause; further
  fixes route through their own tickets once the real scope is known.

## Acceptance Criteria
- [x] Real, direct instrumentation (not code-reading alone) determines whether `FORM_PARTY`/party
      formation is reachable, rare, or genuinely broken under real gameplay conditions.
      **Genuinely broken** — re-measured at real post-count-expansion density first (16→49
      entities, 0 groups both times, ruling out density as the cause), then confirmed via real
      instrumentation that 235 recruitment offers were created but zero were ever accepted.
- [ ] ~~If reachable-but-rare~~ N/A — confirmed genuinely broken, not rare.
- [x] If genuinely broken: real root cause confirmed (not just reproduced), matching this whole
      batch's own "confirmed why, not just confirmed that" standard. `CooperationPosture
      .JOIN_PARTY` — the accept-side posture, whose own `PostureDefinition.intent_mapping` is
      literally `"accept_recruitment_offer"` — was never selected by any decision logic and had no
      handling in `map_decision()`. Three independent confirmations: `accept_contract()` zero real
      callers and zero real calls; `execute_recruit()`'s own trigger intent zero real construction
      sites; `JOIN_PARTY` referenced nowhere outside its own enum/definition.
- [x] The blast radius (every mechanism gated on `state.groups`/party existence) is enumerated,
      even for pieces not fixed by this ticket. See investigation.md Step 2's Blast Radius section.
- [x] If a real bug is confirmed: fix-approach decision obtained via peer review before
      implementation. Reported the full root cause before writing any code; user approved building
      the minimal accept path, with acceptance-criteria richness explicitly deferred.
- [x] **Acceptance bar transferred from `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-
      ACCUMULATION-INVESTIGATION`**: a real run demonstrates `entity.social.trust_history`
      actually accumulating a non-empty entry from real gameplay. **Satisfied** — 3/49 entities
      with non-empty `trust_history` in the final real run, verified not just as a non-zero count
      but as exactly explained by its own real triggers (6 real `MEMBER_ABANDONING`/`LEADER_LOST`
      events, all in 2-member groups, matched tick-for-tick and entity-for-entity against 6 real
      `CooperationLearningService.learn()` calls).

## Related Tickets
- `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION` (done — origin of this
  finding, and the ticket whose own "trust demonstrably accumulates" acceptance bar is transferred
  here explicitly. Confirmed two live, correctly-wired, party-gated trust writers this ticket's own
  resolution would unblock: the party-cohesion-collapse penalty (`CooperationPhase.execute()`,
  now correctly calling `CooperationLearningService.learn()` after that ticket's own repair) and
  the same-party-betrayal penalty (`SocialAppraisalSystem.process_betrayal()`, called from
  `combat_actions.py`).
- `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` (**hard blocking dependency**
  — must land first, per peer review. `count: N` currently spawns one entity per population group
  instead of N, leaving real worlds substantially under-populated and scattered by region. This
  ticket's own reachability question cannot be answered validly against that under-populated
  baseline — see "Blocking Dependency" above.)

## Related Docs
- `docs/archive/entity-enhance/entity_enhance_phase7.md` (Phase 7's own cooperation/party design
  spec — includes `PartyCohesionService`'s own intended design)
- `docs/plans/deferred_tuning_decisions_register.md` D-09 (new — the deferred acceptance-criteria
  richness this ticket's own minimal fix deliberately left open)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION/` (this ticket's own
  investigation.md/plan.md/test_plan.md, including the full real-instrumentation evidence trail)

## Related Code Areas
- `src/domains/cooperation/services.py` (`CooperationDecisionService.find_pending_incoming_offer()`
  — new; `.select()` — new step 0 for JOIN_PARTY)
- `src/domains/cooperation/phase.py` (`CooperationPhase.execute()` — relaxed skip-gate, new
  JOIN_PARTY contract-promotion block)
- `src/systems/social_systems/contracts.py` (`ContractService.accept_contract()` — previously dead,
  now the real caller; `create_recruitment_contract()`, the real offer-creation path)
- `src/systems/world_systems/groups.py` (`GroupSystem.update_groups()` — the real, live,
  unmodified group-formation consumer this fix finally feeds)
- `src/domains/adventure/generator.py`, `src/ai/goals/adventure_scorer.py` (`FORM_PARTY` route —
  confirmed a feeder into this same pipeline, not a separate mechanism; unmodified)
- `src/ai/goals/social_contract_scorer.py` (`SocialContractGoalScorer` — its RECRUITMENT half was
  starved by the same gap; unmodified, now unblocked as a side effect)

## Assumptions / Open Questions
- ~~Whether zero groups forming... is representative of typical gameplay, or an artifact of that
  specific seed/scenario~~ **Resolved**: genuinely broken, confirmed via real root cause, not an
  artifact of seed/scenario choice.
- ~~Whether the zero-groups result is a property of `FORM_PARTY` itself rather than a downstream
  consequence of the under-population bug~~ **Resolved false, as required before proceeding**:
  re-measured at real density first (49 entities, same 0 groups), ruling out density.
- New, deliberately deferred: acceptance-criteria richness (trust/need/faction/commitment checks)
  — see `deferred_tuning_decisions_register.md` D-09.

## Implementation Notes
See `stored_artifacts/TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION/investigation.md`
Steps 4-5 for the full implementation and verification narrative, including the real expiry-tick
bug found and fixed within this same change (a naive `dataclasses.replace()` promotion would have
carried over the OFFER-stage's ~10-tick expiry, causing `GroupSystem.update_groups()` to
immediately dissolve any group that formed — caught via real instrumentation showing
`PartyCohesionService` evaluations firing but `state.groups` still empty by tick 500, root-caused
rather than reported as a partial result, and fixed by switching to the already-correct
`ContractService.accept_contract()` instead of hand-rolling the transition).

Summary of the shape actually built, matching the three pieces peer review named against the
scaffolding's own declared intent (`JOIN_PARTY`'s `intent_mapping = "accept_recruitment_offer"`):
1. Detection (`find_pending_incoming_offer()`) — scans `state.entities` since contracts are never
   mirrored to their target, only stored on the offering entity's own record.
2. Selection (`select()` step 0) — pending offer takes priority over the entity's own help-needs
   evaluation.
3. Promotion (`CooperationPhase.execute()`'s new block) — calls the previously-dead
   `ContractService.accept_contract()`, writing the result into a different entity's
   `EntityUpdate` than the one being evaluated, mirroring the existing party-cohesion-collapse
   block's own established pattern for the same structural reason
   (`map_decision()`'s single-entity-return signature can't target another `entity_id`).

Acceptance-criteria richness (which offers to accept, not just whether a pending one exists) is
explicitly deferred — see `deferred_tuning_decisions_register.md` D-09 — per the user's own
standing rule that tuning decisions are separate from wiring decisions.

## Test Summary
- 5 new unit tests (`tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`):
  `find_pending_incoming_offer` finds a real offer and respects both disqualifiers (already
  grouped, offerer dead), rejects expired offers, and `select()` returns `JOIN_PARTY` with priority
  over the entity's own help-needs evaluation.
- 1 new integration test
  (`tests/integration/domains/cooperation/test_phase7_cooperation_phase.py::
  test_join_party_promotes_offerers_contract_to_active_with_extended_expiry`) — the direct
  regression guard for the real expiry-tick bug found and fixed within this same implementation.
- Real 500-tick instrumented reproduction (primary evidence for this ticket's own Acceptance
  Criteria, not a substitute for the tests above) — see investigation.md Step 5's full three-point
  controlled measurement table, and the dedicated event-correlation verification confirming the
  trust-accumulation rate is exactly explained by its own real triggers (6 collapse events, all in
  2-member groups, matched tick-for-tick and entity-for-entity against 6 real `learn()` calls).
- `pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ tests/unit/social/
  tests/unit/domains/optimization/test_strategic_work_queue.py tests/unit/world/ -q` — 671 passed.
- `pytest tests/unit/social/ tests/unit/strategic/test_strategic_social_contracts.py
  tests/unit/ai/goals/test_social_contract_goal_scorer.py tests/integration/campaigns/
  test_loyalty_pressure_campaign_bridge.py tests/architecture/
  test_adventure_route_score_max_unchanged.py -q` — 304 passed (broader sweep for anything touching
  `accept_contract`/`GroupSystem`/`SocialContractGoalScorer`, all previously-dead-or-starved
  consumers this fix newly exercises for real).
- `pytest tests/refactor/test_import_compatibility.py tests/refactor/test_public_facades.py -q` —
  6 passed.

## Files Changed
- `src/domains/cooperation/services.py` — `find_pending_incoming_offer()` new;
  `CooperationDecisionService.select()` gains step 0
- `src/domains/cooperation/phase.py` — skip-gate relaxed; new JOIN_PARTY promotion block
- `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py` — 5 new tests
- `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py` — 1 new test
- `docs/plans/deferred_tuning_decisions_register.md` — new D-09 entry

## Completion Summary
This ticket was expected to dissolve — the count-expansion fix landing first meant the most likely
outcome, per its own framing, was "zero-groups was a density artifact, nothing further to do here."
That hypothesis was tested first, deliberately, and definitively ruled out: re-measuring at real
post-count-expansion density (16→49 entities) still produced 0 groups, the identical result. Only
after that negative was confirmed did the investigation proceed to root cause — which is what
justified building a fix here rather than deferring or closing on a dissolved premise.

The real root cause was a designed-but-never-connected accept path: `CooperationPosture.JOIN_PARTY`
had a real `PostureDefinition` whose own `intent_mapping` field already named the missing function
("accept_recruitment_offer"), but nothing anywhere selected it or handled it — confirmed via three
independent lines of evidence, not inferred. Built exactly the three missing pieces the scaffolding
already specified, per peer review's explicit framing that this was "not inventing a connector" but
"building the missing pieces of a path whose endpoints are both already specified." Found and fixed
a real bug within the same implementation (a naive contract-promotion that would have silently
undone the fix by leaving groups to dissolve within ticks of forming) before ever reporting a
result, via real instrumentation rather than assuming success from partial evidence.

Final, real, three-point controlled measurement: 16 entities/0 groups → 49 entities/0 groups (density
ruled out) → 49 entities/12 distinct groups formed, cohesion lifecycle exercising all four real
statuses, 3/49 entities with real, non-empty `trust_history`. Verified the trust-accumulation rate
itself — not just its non-zero fact — is exactly explained by its own real triggers: all 6 real
collapse events occurred in 2-member groups, matching the 6 real `CooperationLearningService.learn()`
calls tick-for-tick and entity-for-entity. The transferred acceptance bar from
`TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION` — "trust demonstrably
accumulates in a real run" — is satisfied on the strongest available evidence, not a plausible-looking
proxy. Acceptance-criteria richness (which offers an entity should actually accept) is real,
substantive design work explicitly deferred to `docs/plans/deferred_tuning_decisions_register.md`
D-09, not silently absorbed into this ticket's own minimal, wiring-only scope.
