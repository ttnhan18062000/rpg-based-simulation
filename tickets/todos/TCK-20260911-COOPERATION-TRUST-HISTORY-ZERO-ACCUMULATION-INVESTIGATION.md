---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION
phase: open
date: 2026-09-11
tags: [cognition, social, observability]
---

# TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION

## Title
A complete-looking `entity.social.trust_history` pipeline produced zero entries across 2470 real
`cooperation_event`s in a real 500-tick Campaign episode — determine where it's actually dropped

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Surfaced during `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`: grief's mid-episode trigger
(`EventExtractor.detect_grief_triggers()`) requires some alive entity's real
`entity.social.trust_history` toward a newly-dead entity to meet `ALLY_TRUST_THRESHOLD=0.30`. A
real 500-tick `frontier_living_world` episode produced 4 real deaths and 2470 real
`cooperation_event`s, yet a direct check of every alive entity's `trust_history` toward each dead
entity — at the real point of death, not inferred — found it **uniformly empty for the entire
run**. That result closed the grief investigation as inconclusive (the trigger's own precondition
was never met, not evidence the detection code is broken) but left open a real, more consequential
question this ticket exists to answer.

**This is not the usual "unwired path" shape** — the chain looks complete end to end, unlike prior
findings in this arc (`decay_stale_leads`, the raid-discard stub):
- `src/systems/social_systems/cooperation/services.py:350-372` computes **real** trust deltas
  (concrete values observed: `0.08`, `0.22`, `-0.25`, `-0.75` — not placeholders or zero).
- `src/systems/social_systems/cooperation/phase.py:156` builds a real `SocialUpdate` from them
  (`new_trust = dict(soc_up.trust_delta)`).
- `src/systems/social_systems/relationships.py:39` applies them
  (`for eid, delta in update.trust_delta.items()`).

Every step in the chain is real, non-stub code, and yet the end state — `trust_history` as
actually read by `entity.social.trust_history` — never carries an entry. Something between
"computed" and "applied" (or between "applied" and "read back") drops it, or a gate somewhere in
this chain rarely/never opens under real gameplay conditions. **Neither hypothesis is confirmed —
this ticket exists to determine which, not to assume either one.**

**Why this matters beyond grief.** Every other real consumer of trust reads it as
`entity.social.trust_history.get(other_id, 0.5)` — defaulting to a neutral value
(`src/systems/social_systems/appraisal.py:53,526`, `party.py:60`, `party_composition.py:126`).
Those consumers behave plausibly either way, since a missing key silently reads as "neutral trust"
rather than erroring or looking obviously wrong. Grief is the one real consumer that requires an
actual populated entry (no default it can fall back to and still mean something), which is why it
is the mechanism that surfaced this at all. If trust genuinely never accumulates in practice, then
`SocialBond`, cooperation partner selection, and the episode-boundary `relationship_scores`
carry-forward may all be silently operating on defaults rather than real history — with nothing
about their own behavior looking visibly wrong from the outside, the same "documented/complete-
looking but never actually populated" pattern this whole follow-up arc has repeatedly found.

## Scope
- Trace the real trust-delta chain end to end with direct instrumentation (not just reading code):
  confirm `CooperationService`'s own computed deltas actually reach `phase.py`'s `SocialUpdate`
  construction for a real cooperation event, confirm that `SocialUpdate` actually reaches
  `RelationshipService.process_update()` (`relationships.py:39`) unmodified, and confirm the
  resulting `trust_history` dict is actually written back onto the entity state the pipeline
  carries forward tick-to-tick (not silently discarded by an unrelated reconstruction elsewhere,
  matching this arc's own recurring shape of a downstream constructor dropping a field it never
  explicitly threads).
- Identify whether there's a gate (a condition, a feature flag, a cadence/skip check) between any
  of these steps that rarely or never opens under real gameplay conditions, distinct from an
  outright unwired/dropped-field bug.
- Determine the real, confirmed root cause — do not stop at "confirmed reproducible," go one level
  further to "confirmed why," matching this whole batch's own established standard.
- Once root-caused: decide the fix approach and route it through peer review before implementing,
  given the blast radius this ticket's own Request Summary already identifies (every real trust
  consumer, not just grief).

## Out of Scope
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`'s own scope — already closed with real
  evidence; this ticket investigates the deeper question that closure surfaced, not a re-litigation
  of that ticket's own grief/nemesis-specific findings.
- Any other real or perceived correctness gap in `cooperation_event` processing beyond trust-value
  accumulation specifically (e.g. partner selection logic, cooperation outcome fairness) — not
  investigated here unless directly implicated by this ticket's own root cause.

## Acceptance Criteria
- [ ] Real, direct instrumentation (not code-reading alone) confirms exactly which step in the
      chain — computation, `SocialUpdate` construction, `RelationshipService.process_update()`
      application, or downstream state carry-forward — is where a real trust delta stops reaching
      `entity.social.trust_history` as actually read back.
- [ ] The determination distinguishes "a gate rarely/never opens under real gameplay" from "the
      value is computed but discarded/dropped by a downstream constructor" — these have different
      fixes, and the ticket must not conflate them.
- [ ] If a real bug is confirmed: a fix-approach decision is obtained via peer review before
      implementation (given the cross-cutting blast radius named in the Request Summary), and a
      real test confirms `trust_history` actually accumulates from real cooperation events in a
      real multi-tick run.
- [ ] If no bug is found and trust genuinely accumulates correctly under conditions this
      investigation's own reproduction case didn't happen to meet: record the real condition with
      evidence, not a guess.

## Related Tickets
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (origin of this finding — closed with the
  grief mid-episode leg recorded inconclusive; this ticket investigates the open question that
  closure deliberately did not chase further, per its own scope)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/systems/social_systems/cooperation/services.py` (trust-delta computation, lines ~350-372)
- `src/systems/social_systems/cooperation/phase.py` (`SocialUpdate` construction, line ~156)
- `src/systems/social_systems/relationships.py` (`RelationshipService.process_update()`, line ~39)
- `src/observability/event_extractor.py` (`detect_grief_triggers()`, the real consumer that
  surfaced this — reads `entity.social.trust_history` directly)
- `src/systems/social_systems/appraisal.py`, `party.py`, `party_composition.py` (other real trust
  consumers, all defaulting to neutral on a missing key — potentially masking the same gap)

## Assumptions / Open Questions
- Whether the root cause is a rarely-opening gate or a silently-dropped value is the central,
  deliberately-unresolved question this ticket exists to answer — not assumed either way here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
