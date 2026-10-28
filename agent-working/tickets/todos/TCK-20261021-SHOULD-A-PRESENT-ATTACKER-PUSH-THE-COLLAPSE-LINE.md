---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-SHOULD-A-PRESENT-ATTACKER-PUSH-THE-COLLAPSE-LINE
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-SHOULD-A-PRESENT-ATTACKER-PUSH-THE-COLLAPSE-LINE

## Title
Owner question after v1: should a present attacker push an exhausted subject's collapse line? (D41 collapse is ordered before panic)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Split from TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE (crowded s44, merchant 12, corpse-fix new arm), following the designer's ruling of 2026-10-21.

At t2048 merchant 12's single tactical pass returned `{'action': 'SLEEP', 'collapse': True}`:
- sleep_debt was 100.0 (measured 92.5 at t1851 and 100.0 from t2036, with nothing sampled between);
- the collapse line is 98.0 (`SLEEP_DEBT.collapse_line`, src/engine/sleep_debt.py:34; `must_collapse` at lines 52-54);
- the gate is src/engine/tactical.py:166-167, the first gate after legality, before the panic gate.

So this is the D41 involuntary collapse, not a voluntary sleep that outranks flight. The designer reads it as defensible fiction under D41: the body gives out. The merchant fell asleep beside raider 35 at hp 1 and died at t2066.

The open design question for the OWNER: should a present attacker (a perceived live hostile adjacent or engaging) push the collapse line, so that adrenaline delays the collapse? If so, by what rule, and with what bound?

It is not a defect, so no disclosure row: the designer adds C7 only for a defect.

Note: the debt was at 100.0 from at least t2036 (when it first crossed 98 is not measured), but no tactical pass ran until t2048 to apply the collapse. That part belongs to the disengage ticket (a held ATTACK bypasses the tactical pass), not to this one.

## Scope
- Designer framing, then the owner's ruling: keep D41 as it is, or let a present attacker push the line (rule and bound).
- If the owner says change it: implement, add real-kernel tests, and measure paired against v1 (seeds 42-46, D76).

## Out of Scope
- The held-ATTACK bypass (the disengage ticket).
- Any change to the collapse line value without a ruling.

## Acceptance Criteria
- The owner's ruling is recorded (owner_decision_memo row).
- If it changes: the tests pass, D76 shows no unexplained drift against v1, and the Bible, parity and divergence docs are updated.

## Related Tickets
- TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md (D41)
- docs/mechanics/04_strategic_cognition.md §1

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/probes_hs/m12_sleep.py (output in paired_cn/m12_sleep.json)

## Related Code Areas
- src/engine/sleep_debt.py
- src/engine/tactical.py:166-167

## Assumptions / Open Questions
- None beyond the owner question.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
