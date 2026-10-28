---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-A-READMITTED-NEED-RESUMES-ITS-LIVE-PROJECT
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-A-READMITTED-NEED-RESUMES-ITS-LIVE-PROJECT

## Title
A re-admitted escalated need opens a fresh project id each time it flips with another need, instead of resuming its live same-kind project

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A's step-2 trace (TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY, f9b21b55b, 2026-10-21) showed raider 37 on crowded_frontier s42 flipping between hunger and fatigue. Each time hunger is admitted again it opens a NEW hunger project id, and does not make its existing live hunger project current again. This is the #406 shape.

The pre-ruling (rpg-planner and designer, 2026-10-21) said: if raider 37 starves in the V3-on-15, it is in family and is built before v1 as step 3; if it eats, file it after v1 as P2. In the V3-on-15 on f9b21b55b, crowded 42 is V3 0 with 0 starved. So it goes after v1 and is measured against v1.

## Scope
- Designer first: confirm the shape. A re-admitted escalated need resumes its same-kind live project (same id, made current). No new constant, and the tactical suspend is unchanged.
- Implement it in the authoritative path, together with the per-kind trim (`live_projects_in_the_trim`, src/core/strategic.py).
- Real-kernel tests: when a need flips hunger -> fatigue -> hunger, the same hunger project id becomes current again, and no second live hunger project is created.
- Measure paired against v1 (seeds 42-46, D76). Report the count of project ids created per need episode before and after.

## Out of Scope
- Capacity admission (step 2, before v1).
- The suspended-project lifecycle (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK). Coordinate with it, because both decide what "resume" means.

## Acceptance Criteria
- No entity holds two live projects of one need kind because of a flip, in the 3 gate worlds × seeds 42-46.
- D76 shows no unexplained drift against v1.

## Related Tickets
- TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY
- TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
- TCK-20261019-RECORD-BASELINE-V1

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1, §4

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/paired_en2/v3/ (V3-on-15, f9b21b55b)

## Related Code Areas
- src/ai/goals/escalation.py (escalated_need_wins)
- src/core/strategic.py (live_projects_in_the_trim)
- src/ai/intelligence.py (project creation)

## Assumptions / Open Questions
- Does any other need pair (hunger and thirst, fatigue and safety) flip the same way?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
