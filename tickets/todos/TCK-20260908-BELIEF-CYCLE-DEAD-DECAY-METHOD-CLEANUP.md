---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP
phase: open
date: 2026-09-08
tags: [architecture, strategy]
---

# TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP

## Title
BeliefCycleSystem.decay_stale_beliefs() has zero callers and only decays leads, never beliefs, despite its name

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found by peer review (`rpg-feature-planning`) while diagnosing the `combat_risk` belief-staleness
bug on `TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN`, independently verified against real code
before filing here rather than fixed inline (out of scope for that ticket, per the peer's own
explicit framing):

`BeliefCycleSystem.decay_stale_beliefs()` (`src/systems/strategic_systems/belief.py:42-79`) — its
name and docstring ("LEG-RPG-150: Beliefs decay over time") both promise it decays
`entity.strategic.beliefs`. It does not: the method body iterates `entity.strategic.leads` only and
never touches `beliefs` at all. Confirmed via grep it also has **zero call sites** anywhere in
`src/` — it is dead code, not merely mis-scoped.

This is a real trap for future work: `TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN`'s own
correction round needed a producer-side no-threat-belief write specifically because nothing decays
`beliefs`, and the peer's own investigation notes that they initially assumed this method would
cover it — "as I initially did" — before checking. The mismatch between what the name promises and
what the code does invites the same mistake again.

## Scope
Pick exactly one of the following (a real decision, but a small and low-risk one — does not need
its own investigation/plan/test_plan staging artifacts given the tier and size):
1. Delete `decay_stale_beliefs()` entirely (dead code, no callers, no behavior loss).
2. Rename it to `decay_stale_leads()` (matching what it actually does) and correct its docstring —
   keeps the method available if something is expected to wire it in later.
3. Actually wire it into the pipeline AND extend it to decay `entity.strategic.beliefs` too, making
   the name accurate by building the behavior it promises — this is the largest option and should
   only be chosen if a real, current need for generic belief decay is identified during
   investigation (e.g. beliefs like `combat_risk` accumulating unboundedly without ever being
   pruned, beyond the specific fix `COMBAT-RISK-BELIEF-PRODUCER-DESIGN` already applied for that
   one belief).

Whichever is chosen, update/add tests accordingly and confirm no other code assumed the old
(non-existent) decay behavior.

## Out of Scope
- Any other method in `src/systems/strategic_systems/belief.py`.
- Re-litigating the `combat_risk` staleness fix itself — already fixed and closed on
  `TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN`.

## Acceptance Criteria
- [ ] `decay_stale_beliefs()` either deleted, renamed to accurately describe its real behavior, or
      genuinely extended to decay beliefs (and wired into the pipeline) — no state where the name
      still promises something the code doesn't do.
- [ ] No remaining references to a stale name if renamed/deleted.
- [ ] Relevant tests updated or added; existing `tests/unit/strategic/` (or wherever this module's
      tests live) sweep stays green.

## Related Tickets
- TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (origin of this finding, via its own second
  correction round)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, self-evident intent.

## Related Code Areas
- src/systems/strategic_systems/belief.py

## Assumptions / Open Questions
- Whether any *current* real need exists for generic belief decay (option 3 above) is not yet
  investigated — left for this ticket to determine; default assumption going in is option 1 or 2
  (delete or rename), since option 3 is speculative without an identified real trigger.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
