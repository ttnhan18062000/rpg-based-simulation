---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-BRANCH-B
phase: open
date: 2026-07-03
tags: [simulation_quality, information, cognition, self-model, bug]
---

# TCK-20260703-SIMQ-UPLIFT3-BRANCH-B

## Title
Wire Branch B: fix SelfModelUpdatePhase's hardcoded events=[] so self_model.knowledge.unknowns can be populated

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`docs/cognition/self_model_contract.md` and `docs/cognition/README.md` (both `status: active`,
`authority: P1`) document `SelfModelUpdatePhase`'s Step 1 (`KnowledgeModelService.assimilate`) as
running "only if InformationResponse events exist for this entity this tick" — implying the
`events` parameter passed into `SelfModelUpdatePhase.run()` should carry the tick's actual
`InformationResponse` events. Investigation during `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`
found `src/cognition/self_model_phase.py`'s call to `SelfModelUpdatePhase.run()` hardcodes
`events=[]` — a genuine contract violation, not a design choice. As a result,
`self_model.knowledge.unknowns` is never populated by any code path in the standard pipeline, which
means `InformationBeliefPhase`'s Branch B (route a new query) is permanently unreachable,
independent of `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`'s Branch A fix.

That ticket deliberately did NOT fix this — wiring `SelfModelUpdatePhase`'s `events=[]` touches
shared cognition-pipeline code used by every world, and was judged out of scope for a ticket that
was primarily about the information domain's compile-time plumbing (the investigation found this
mid-implementation and it required its own architecture review to scope correctly, mirroring the
Branch A investigation's own scope-discipline). This ticket picks that fix up properly.

## Scope
1. Re-verify the finding against current `src/` (`self_model_phase.py`'s exact line may have
   shifted) — do not assume the 2026-07-03 investigation snapshot is still accurate without
   checking.
2. Trace where `InformationResponse` events actually originate in a tick (Branch A of
   `InformationBeliefPhase.apply()`, or elsewhere) and determine the correct, minimal way to pass
   them into `SelfModelUpdatePhase.run()`'s `events` parameter — this may require new per-tick
   event plumbing between phases, which is exactly the kind of infrastructure the parent ticket's
   investigation flagged as "genuinely new... shared-engine-path scope" requiring careful design.
3. Fix the `events=[]` hardcoding so `KnowledgeModelService.assimilate()` actually runs when
   `InformationResponse` events exist for an entity.
4. Confirm `self_model.knowledge.unknowns` becomes populated in at least one calibration scenario
   as a result, and that `InformationBeliefPhase`'s Branch B becomes reachable (or, if it's still
   blocked by something else discovered during investigation, document that honestly rather than
   claim success).
5. Regression-test across ALL calibration worlds, not just `urban_political` — this phase runs for
   every alive/active entity in every world, every tick.

## Out of Scope
- `InformationNeedDetector.detect_and_generate()` (still orphaned, separate from this fix) and the
  `paid_information_transaction` path — those depend on `state.information_providers`, a different
  field, and are not part of Branch B
- Re-litigating Branch A (`pending_information_responses`) — already shipped and working
  (`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`)
- Turning on `ENABLE_SELF_MODEL_COGNITION` globally (confirmed not required for this fix — Branch B
  reachability depends on the `events=[]` bug, not this separate flag)
- Any change to `SelfAssessmentService`, `NeedInterpretationService`, or `CapabilityEstimateService`
  (the other 3 steps of `SelfModelUpdatePhase`'s pipeline) — this ticket touches only Step 1's event
  plumbing

## Acceptance Criteria
- [ ] `self_model_phase.py`'s `events=[]` hardcoding replaced with the tick's actual
      `InformationResponse` events for that entity
- [ ] `self_model.knowledge.unknowns` confirmed populated in at least one calibration scenario after
      the fix (via direct-pipeline test, not just a unit test in isolation)
- [ ] `InformationBeliefPhase`'s Branch B confirmed reachable (or the reason it's still blocked, if
      any, is documented honestly)
- [ ] Full regression sweep across all calibration worlds (not just `urban_political`) — 0
      unintended regressions
- [ ] `docs/cognition/self_model_contract.md`'s documented behavior now matches actual code (no
      doc update needed if the fix makes the doc accurate, but verify)
- [ ] `make evaluate --dry-run` exits 0

## Related Tickets
- TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER (done) — found this bug, deliberately deferred the
  fix to this ticket
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION (done) — parent of the INFORMATION-pillar work this
  eventually feeds into

## Related Docs
- `docs/cognition/self_model_contract.md` — the contract this fixes a violation of
- `docs/cognition/README.md` — Step 1 pipeline description
- `docs/plans/idea_information_belief_trigger_wiring.md` — original idea doc naming this as Option 1

## Related Stored Artifacts
- `stored_artifacts/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER/investigation.md` — full file:line
  evidence for the `events=[]` bug and its contract violation

## Related Code Areas
- `src/cognition/self_model_phase.py` — `SelfModelUpdatePhase.apply()`/`.run()`, the `events=[]`
  hardcoding
- `src/cognition/knowledge_model.py` — `KnowledgeModelService.assimilate()`
- `src/core/self_model.py` — `self_model.knowledge.unknowns`
- `src/domains/information/phase.py` — `InformationBeliefPhase.apply()` Branch B, the consumer of
  `unknowns`

## Assumptions / Open Questions
- UQ-1: Where should the per-tick `InformationResponse` events actually be sourced from for
  `SelfModelUpdatePhase.run()`'s `events` parameter — does this require new pipeline-level event
  plumbing (a per-tick event list passed between phases), or is there an existing mechanism this
  ticket's investigation should find? Resolve with evidence during investigation, not assumed.
- UQ-2: Does `ENABLE_SELF_MODEL_COGNITION` (separate flag, currently OFF everywhere) need
  consideration here, or is it orthogonal? The prior investigation found it orthogonal — reconfirm.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation — must include a regression sweep across all calibration
worlds since this touches shared cognition-pipeline code)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
