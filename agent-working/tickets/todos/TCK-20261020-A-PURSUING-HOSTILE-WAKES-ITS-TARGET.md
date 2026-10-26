---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261020-A-PURSUING-HOSTILE-WAKES-ITS-TARGET
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-A-PURSUING-HOSTILE-WAKES-ITS-TARGET

## Title
A perceived hostile pursuing the subject (INTERCEPT/PURSUE on it) wakes its brain, extending D32's adjacency wake

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
OWNER-CONFIRM ITEM: this extends owner decision D32. The designer ruled on 2026-10-20 that it comes after v1, as its own measured step, and will put it to the owner.

Lane A's real-kernel probe on rpg-v3-starvation-threat 70402779d (/mnt/data/scratch-rpg-implementer/v3_close2.py) set this up:
- frontier 42, merchant 37 starving (hp 40/85, hunger 100) with an inn in reach;
- a hostile scout closing from 7 tiles, INTERCEPT from t7 at 1 tile a tick, contact at t12, ATTACK from t15.

The merchant never reacted before contact. The brain runs only at the strategic cadence (10 ticks, staggered by id, cadence.py), and the adjacency wake (scheduler.py:53-55, D32) fires only for a hostile beside the subject. A hunter crosses 6 tiles inside one cadence window. A tactical pass called on those ticks would have pre-empted from distance 6 (PURSUE, then engage). This is disclosed in v1 as row C5 (designer f8913b038).

## Scope
- In the scheduler wake rule: a perceived hostile whose current task is INTERCEPT or PURSUE targeting the subject wakes the subject's brain on that tick.
- Before-numbers, measured before the change:
  - this probe's trace (the hunter crosses 6 tiles unseen);
  - from the paired run, a count of contact attacks where the attacker had been pursuing for 2 or more ticks before contact.
- Measure it as its own step: paired 3 × 42-46, crowded first, with a STOP to the owner. Report the wake rate and its tick cost.
- Finding to record here, not to fix here: during the closing window the merchant's task was a held, empty ENTITY_ACT (action None, payload {}). Find out whether an empty act being held as a task is a defect, and file it if so.

## Out of Scope
- The cadence length. The hunger and threat logic (V3 step (ii)).

## Acceptance Criteria
- The owner confirms the D32 extension before it lands.
- In the probe scenario, the subject reacts before contact. This is pinned by a real-kernel test.
- The paired measurement passes the stop line, or the result goes to the owner.
- The empty-ENTITY_ACT finding is recorded, with a verdict.

## Related Tickets
- the V3 step (ii) ticket on rpg-v3-starvation-threat
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md (D32)
- docs/plans/systemic_world/v1_disclosure.md (C5)
- docs/engine/kernel.md (scheduling)

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/v3_close2.py (probe)

## Related Code Areas
- src/engine scheduler.py:53-55 (adjacency wake)
- cadence.py (strategic_intelligence 10)
- tactical.py

## Assumptions / Open Questions
- Is the wake costed per perceived hostile? Bound it the same way the adjacency wake is bounded.

## Implementation Notes
After v1. Needs the owner's confirmation.

## Test Summary

## Files Changed

## Completion Summary
