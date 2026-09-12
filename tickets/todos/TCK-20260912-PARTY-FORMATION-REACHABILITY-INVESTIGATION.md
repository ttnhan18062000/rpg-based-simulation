---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION
phase: open
date: 2026-09-12
tags: [cognition, social]
---

# TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION

## Title
`state.groups` was empty across an entire real 500-tick episode — determine whether party formation (the `FORM_PARTY` adventure route) ever actually occurs under real gameplay conditions, or is itself a keystone-unreachable mechanic; carries the "trust demonstrably accumulates in a real run" acceptance bar forward from `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`

## Status
OPEN

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
- [ ] Real, direct instrumentation (not code-reading alone) determines whether `FORM_PARTY`/party
      formation is reachable, rare, or genuinely broken under real gameplay conditions.
- [ ] If reachable-but-rare: real conditions and real frequency documented with evidence.
- [ ] If genuinely broken: real root cause confirmed (not just reproduced), matching this whole
      batch's own "confirmed why, not just confirmed that" standard.
- [ ] The blast radius (every mechanism gated on `state.groups`/party existence) is enumerated,
      even for pieces not fixed by this ticket.
- [ ] If a real bug is confirmed: fix-approach decision obtained via peer review before
      implementation.
- [ ] **Acceptance bar transferred from `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-
      ACCUMULATION-INVESTIGATION`**: a real run demonstrates `entity.social.trust_history`
      actually accumulating a non-empty entry from real gameplay — via the party-cohesion-collapse
      repair that ticket already made, once party formation is confirmed reachable, or via
      whatever real fix this ticket's own investigation determines is needed. If this ticket's own
      findings show party formation genuinely cannot be made reachable within its own scope, the
      bar moves again to whichever ticket owns that remaining piece — recorded explicitly, not
      allowed to quietly disappear.

## Related Tickets
- `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION` (done — origin of this
  finding, and the ticket whose own "trust demonstrably accumulates" acceptance bar is transferred
  here explicitly. Confirmed two live, correctly-wired, party-gated trust writers this ticket's own
  resolution would unblock: the party-cohesion-collapse penalty (`CooperationPhase.execute()`,
  now correctly calling `CooperationLearningService.learn()` after that ticket's own repair) and
  the same-party-betrayal penalty (`SocialAppraisalSystem.process_betrayal()`, called from
  `combat_actions.py`).

## Related Docs
- `docs/archive/entity-enhance/entity_enhance_phase7.md` (Phase 7's own cooperation/party design
  spec — includes `PartyCohesionService`'s own intended design)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/adventure/generator.py` (`FORM_PARTY` route generation eligibility)
- `src/ai/goals/adventure_scorer.py` (`FORM_PARTY` route scoring)
- `src/systems/social_systems/party_composition.py` (party-fit scoring feeding `FORM_PARTY`'s
  `expected_benefit`)
- `src/engine/pipeline_phases/groups.py` (real `state.groups` population/management phase)
- `src/domains/cooperation/services.py` (`PartyCohesionService`, gated on groups existing)

## Assumptions / Open Questions
- Whether zero groups forming in the one real reproduction run so far is representative of typical
  gameplay, or an artifact of that specific seed/scenario/tick-count, is the central,
  deliberately-unresolved question this ticket exists to answer — not assumed either way here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
