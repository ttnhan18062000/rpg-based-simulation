---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER
phase: open
date: 2026-07-03
tags: [simulation_quality, information, belief, cognition, self-model, deferred]
---

# TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER

## Title
Wire a reachable trigger for InformationBeliefPhase so INFORMATION pillar events can actually fire

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260702-SIMQ-UPLIFT2-INFORMATION` shipped compile-time scaffolding for
`information_source_profiles` (schema/compiler/resolver plumbing + two corrected profiles in
`urban_political` + `ENABLE_BELIEF_ASSIMILATION=ON`), but investigation found this scaffolding
alone cannot produce any INFORMATION-pillar events: `InformationBeliefPhase.apply()`'s two trigger
branches are unreachable in the current engine, for reasons independent of the flag/profile fix.

This ticket is the deferred follow-up to actually make one of those triggers reachable. Full
investigation, root cause, and two candidate fixes are documented in
`docs/plans/idea_information_belief_trigger_wiring.md` — read that first, it is the primary source
for this ticket's Scope.

Summary of the gap: Branch A (`InformationBeliefPhase.apply()`, assimilate a pending response)
requires `state.pending_information_responses`, which nothing in `src/` ever writes. Branch B
(route a new query) requires `self_model.knowledge.unknowns`, but `SelfModelUpdatePhase.apply()`
hardcodes `events=[]`, so the assimilation loop that would populate it never executes. Every
alternate path to `lead_certainty_updated` or `paid_information_transaction` is either the same
dead state, or orphaned code with zero callers (`InformationNeedDetector.detect_and_generate()`,
`GuildAction.visit()`).

## Scope
1. Re-verify the idea doc's findings against current `src/` (this ticket may be picked up after
   other changes land — do not assume the investigation snapshot from 2026-07-03 is still accurate
   without checking).
2. Choose between the idea doc's Option 1 (wire Branch B via `self_model.knowledge.unknowns`
   seeding or fixing `SelfModelUpdatePhase`'s `events=[]`) and Option 2 (wire the
   `paid_information_transaction` path via `InformationNeedDetector` + `state.information_providers`
   seeding) — this requires its own investigation/plan/architecture-review, not a reflexive pick.
3. Implement the chosen option, scoped to `urban_political` calibration content where possible;
   if the fix necessarily touches shared engine code (`SelfModelUpdatePhase`, `CognitionDomain`),
   regression-test across ALL calibration worlds, not just `urban_political`.
4. Recalibrate; confirm `belief_assimilated`, `lead_certainty_updated`, or
   `paid_information_transaction` shows `calibration_hits > 0` in at least one `urban_political_*`
   run; update `grade_anchors.json`; verify 0 regressions elsewhere.
5. Update `docs/simulation_quality/event_type_coverage.md` and the parity ledger entry created by
   `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` (`docs/parity_ledger/infrastructure.yaml::INFRA-256` —
   confirmed ID, shipped 2026-07-03; extends `INFRA-245`) to reflect the pillar as actually
   active, not just scaffolded. `INFRA-256`'s `divergence_note` and `support_boundary` currently
   state the pillar is inactive pending this ticket — both must be updated (not just appended to)
   once a trigger is made reachable, and `status`/`text` should be revised to describe genuine
   pillar activation rather than compile-time scaffolding only.

## Out of Scope
- Re-litigating the schema/compiler/resolver plumbing already shipped by
  `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` (assume it is correct; only revisit if this ticket's
  implementation finds a defect in it)
- A full information marketplace or NPC query-response loop beyond what's needed for
  `calibration_hits > 0`
- Activating INFORMATION in any world other than `urban_political` (unless the chosen fix
  necessarily touches shared code, in which case regression coverage — not activation — extends
  to other worlds)

## Acceptance Criteria
- [ ] Idea doc's findings re-verified against current `src/` before planning
- [ ] One of Branch A, Branch B, or the paid-information path made reachable in `urban_political`
- [ ] At least one of `belief_assimilated`, `lead_certainty_updated`, or
      `paid_information_transaction` has `calibration_hits > 0` in at least one `urban_political_*`
      calibration run
- [ ] `make evaluate --dry-run` exits 0 (0 regressions across all worlds, including any shared-code
      changes' impact on non-`urban_political` worlds)
- [ ] `docs/simulation_quality/event_type_coverage.md` and parity ledger updated to reflect the
      pillar as genuinely active

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION — parent; shipped scaffolding, deferred this work
- TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO — original root-cause diagnosis (incomplete; this ticket
  and its parent correct/extend it)
- TCK-20260702-SIMQ-UPLIFT2-FACTION — sibling ticket; compiler-plumbing template already applied
  by the parent ticket

## Related Docs
- `docs/plans/idea_information_belief_trigger_wiring.md` — primary source; full investigation,
  options, and recommendation
- `docs/simulation_quality/event_type_coverage.md` — rows for `belief_assimilated`,
  `paid_information_transaction`, `lead_certainty_updated`, and sibling INFORMATION/COGNITION rows
  updated 2026-07-03 by the parent ticket to note the scaffolding-shipped/trigger-still-dead state
- `docs/parity_ledger/infrastructure.yaml::INFRA-256` — scaffolding-verified/pillar-inactive entry
  shipped by the parent ticket 2026-07-03; this ticket's completion should revise its `status`/
  `text`/`divergence_note`/`support_boundary` to reflect genuine activation (extends `INFRA-245`)
- `docs/mechanics/04_strategic_cognition.md` — has no chapter on `InformationSourceProfile` /
  `InformationBeliefPhase` at all; flagged as a Mechanics Bible coverage gap by the parent
  ticket's investigation, may need a new section depending on which option is chosen

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/investigation.md` — full file:line
  evidence for the dead trigger paths

## Related Code Areas
- `src/domains/information/phase.py:28-110` — `InformationBeliefPhase.apply()`, both dead branches
- `src/core/state.py:1144` — `AuthoritativeState.pending_information_responses` (never written)
- `src/core/self_model.py:179` — `self_model.knowledge.unknowns` (never populated)
- `src/cognition/self_model_phase.py:32-56` — `SelfModelUpdatePhase.apply()`, hardcoded `events=[]`
- `src/cognition/knowledge_model.py:93-101` — `KnowledgeModelService.assimilate()`
- `src/engine/domain/cognition_extras.py:36-98` — `InformationNeedDetector.detect_and_generate()` (orphaned)
- `src/town/guild.py:11-` — `GuildAction.visit()` (orphaned)
- `src/engine/pipeline_phases/paid_information.py:74-183` — `PaidInformationTransactionSystem.enforce()`
- `src/core/state.py:1150` — `AuthoritativeState.information_providers` (different field from
  `information_source_profiles` — do not conflate)

## Assumptions / Open Questions
- UQ-1: Which option (Branch B wiring vs. paid-information path) is the right long-term fix? Not
  resolved by the idea doc on purpose — requires its own investigation/plan/architecture-review.
- UQ-2: If Branch B is chosen and requires touching `SelfModelUpdatePhase`, does
  `ENABLE_SELF_MODEL_COGNITION` (currently OFF, separate flag) also need to be turned ON, and what
  is the blast radius of doing so across other calibration worlds?

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation — must include a regression sweep across all calibration
worlds if the chosen fix touches shared cognition-pipeline code)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
