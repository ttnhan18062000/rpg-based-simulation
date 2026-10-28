---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-TWO-SUBJECTS-HOLD-A-MUTUAL-THREATENING-FLEE-STANDOFF
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-TWO-SUBJECTS-HOLD-A-MUTUAL-THREATENING-FLEE-STANDOFF

## Title
Two subjects can each treat the other as THREATENING and hold a flee standoff for half a run (frontier s42, alpha 49 and blacksmith 13)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A's frontier flight-reason split for the corpse fix (TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT, 23fbe0ecf against base, frontier_living_world s42, 5000t, 2026-10-21; probe flee_reason.py, data in /mnt/data/scratch-rpg-implementer/paired_cn/fr/):
- In the new arm, alpha 49 (a wolf, alive 5000/5000 in both arms) and blacksmith 13 flee from EACH OTHER via FLEE_THREAT (the `avoid_what_can_eat_me` path, THREATENING relation).
  - The alpha flees blacksmith 13 213 times; the blacksmith's top trigger is the alpha (226 for blacksmiths).
  - From t2500 to t5000 both sit flat at about 180 flight ticks per 500 ticks, about 36% of their time.
  - Blacksmith 13 has 45 flee -> non-flee -> flee alternations within 10 ticks.
- Workers also flee alpha 49 at about 540 flight ticks per 500 ticks (worker FLEE_THREAT 6.4 -> 139.4 per 1000 alive-ticks), and the alpha flees workers 4, 2, 6 and 7.
- In base, blacksmith 13 was dead, so this never showed.
- Overall oscillation is down (235 -> 190), so it is not a shuttle toward danger. It is a standoff that never resolves.

The designer's ruling (2026-10-21): it is its own item, after v1, not accepted as is, and does not block the STOP or v1. Two wary creatures keeping their distance is fine fiction. THREATENING holding BOTH ways, with neither side ever resolving it by fighting, leaving or settling into ignoring the other for 2500 ticks, is not. Disclosed in v1_disclosure.md as C7.

## Scope
- The cause, asked first: is the THREATENING relation meant to be asymmetric (predator -> prey)? Why is it mutual between alpha 49 and blacksmith 13, and between the alpha and the workers? That decides between:
  - a relation bug (THREATENING should not hold both ways), or
  - a missing standoff resolution (it may hold both ways but must resolve).
- The designer rules the shape. Implement, add real-kernel tests (a mutual standoff resolves within a bound), and measure paired against v1 (seeds 42-46, D76).

## Out of Scope
- The corpse fix (before v1).
- Retuning flee distances without a ruling.

## Acceptance Criteria
- The cause is named (relation asymmetry, or the resolution gap) with evidence.
- No pair holds a mutual FLEE_THREAT standoff past the ruled bound in the 3 gate worlds × seeds 42-46.
- D76 shows no unexplained drift against v1, and C7 is closed with numbers.

## Related Tickets
- TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE (C6)
- TCK-20261020-A-PURSUING-HOSTILE-WAKES-ITS-TARGET (D32 wake)
- TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT (which surfaced this)

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1
- docs/plans/systemic_world/v1_disclosure.md (C7)

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/paired_cn/fr/base.json, new.json (probe flee_reason.py)

## Related Code Areas
- the `avoid_what_can_eat_me` / FLEE_THREAT path and the THREATENING relation classification

## Assumptions / Open Questions
- Why does a wolf classify a blacksmith (and workers) as something that can eat it?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
