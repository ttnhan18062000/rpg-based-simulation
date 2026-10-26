---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95

## Title
town_return outbids an escalated hunger goal until about hunger 95, but SURV-07 says the need outranks ordinary goals "well before the line"

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A traced blacksmith 13 (crowded_frontier s45, 2026-10-20) while building step 2, TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY.
- The hunger goal passes its escalation onset (need_is_pressing, 0.6 of the line, about hunger 60) at t1201.
- It still loses to town_return (about 115 to 139) at every brain tick until about hunger 95. Examples: t1207, hunger 60: town_return 115.2 against hunger 66.5. t2187, hunger 100: hunger 160.0 against town_return 139.6.
- SURV-07 says escalation makes the need outrank ordinary goals well before the line. Winning only near 95 leaves a few ticks of margin, so any delay (a hit, a block, travel) turns into starvation.

The designer's ruling (2026-10-20): this is a real gap but not a pre-v1 fix. It is another behaviour change in every world, and D78 allows one variable per step. It becomes pre-v1 only if step 2's paired run shows a V3 from it. It is disclosed in v1_disclosure.md (row N13).

The existing leash ticket does not cover this. TCK-20261009-HEROES-ON-A-LEASH-NEVER-SEEK-FOOD-AND-STARVE-WITHOUT-ONE-EAT-ATTEMPT (done, #500, divergence 2.106, D57) bounded the leash return and which food ways count as in range. It did not touch town_return's score against an escalated need.

## Scope
- Designer first: how an escalated need outranks town_return (and any other ordinary goal that outbids it) from the onset. Use the existing escalation scale, not a new knob. Coordinate with TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE.
- Find every ordinary-goal scorer that can outbid an escalated hunger or fatigue goal past onset in the gate worlds, and report the score bands.
- Implement, then add real-kernel tests: past onset, the need wins against town_return.
- Tighten step 2's bs13 replay test, which pins current scoring with a hunger project by about 95 ("tightens when the town_return outbid is fixed").
- Measure paired against v1 (seeds 42-46, D76).

## Out of Scope
- Capacity admission (step 2, before v1).
- The suspended-project slot leak (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK).

## Acceptance Criteria
- Past onset, an escalated need wins scoring against town_return in the gate worlds. The hunger-project start tick moves from about 95 toward the onset, with numbers reported.
- The bs13 test is tightened.
- D76 shows no unexplained drift against v1, and N13 in v1_disclosure is closed with the numbers.

## Related Tickets
- TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY (step 2)
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
- TCK-20261009-HEROES-ON-A-LEASH-NEVER-SEEK-FOOD-AND-STARVE-WITHOUT-ONE-EAT-ATTEMPT (done; does not cover this)
- TCK-20261019-RECORD-BASELINE-V1

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1
- SURV-07 (world rules), v1_disclosure.md N13

## Related Stored Artifacts
- Lane A probes: /mnt/data/scratch-rpg-implementer/probes_hs/bs13_trace.py, with output in /mnt/data/scratch-rpg-implementer/cn_meas/

## Related Code Areas
- the town_return scorer and the hunger scorer (src/ai/goals/, scorers)
- need_is_pressing

## Assumptions / Open Questions
- Is town_return's band (115 to 139) a fixed priority or need-aware?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
