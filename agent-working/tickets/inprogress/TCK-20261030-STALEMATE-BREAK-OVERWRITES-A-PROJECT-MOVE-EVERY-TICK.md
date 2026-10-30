---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK
phase: open
date: 2026-10-30
tags: []
---

# TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK

## Title
The stalemate breaker replaces a project's move with a one-tile wander every tick on a move that reports no failure ("LEGAL", path length 0), so the subject oscillates between two tiles and never reaches its target

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by lane B during EARN's D73-shape probe. Urban s44 person 1, ticks 2200-2300, traced every tick:
- task ENTITY_MOVE with reason STALEMATE_BREAK in 101 of 101 ticks, movement_mode WANDER;
- last_failure_reason "LEGAL" every tick, path length 0;
- the position alternates (50,26)/(50,25), occasionally (49,25/26), 11 tiles from the target;
- the hunger project re-issues its move to the hiring inn (39,23) about every 10 ticks, and the breaker overwrites it at once;
- oscillation_count cycles 0..3, wait_count 0.
There is no main comparison for this person, because it died in COMBAT on the base run. EARN's code is not on this path.
Raw data: /mnt/data/scratch-rpg-implementer-2/probe/nav_u44_earn3.json.
Designer framing: this is a third "repeated failure, never learned" shape, after the failed service dispatch and the position swap. A stalemate on a move that reports no failure looks like a wrong trigger.

## Scope
1. COUNTS FIRST, with no behaviour change. On main and D73-shape, 3 worlds × s42-46 × 5000t:
   - how often a project move is overwritten by STALEMATE_BREAK within 1 tick, with run lengths;
   - how often last_failure_reason == "LEGAL" with path length 0 at the breaker's trigger;
   - per subject, the distance to the target over the run.
   Send to rpg-planner, who passes them to rpg-designer.
2. Find the trigger, i.e. why the breaker fires on a path the nav reports as legal, and propose a fix scoped to the trigger. The designer rules before code.
3. Divergence entry (if behaviour changes), Bible/parity, paired run.

## Out of Scope
- The combat stalemate rule (2.87).
- Turning repeated failures into blockers in general (TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER).

## Acceptance Criteria
- The counts table is delivered before any code.
- A regression test with the s44 p1 shape: a project move is not replaced by a wander every tick while the nav reports no failure.
- The paired run is reported.

## Related Tickets
- TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT (trigger B, the near-target WANDER jitter at a full door, is worked under that ticket; this one keeps trigger A, STALEMATE_BREAK)
- TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER (same family)
- TCK-20260418-MOV-CONGESTION, TCK-20260326-HYSTERESIS (earlier anti-oscillation work)
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO (where it was found)

## Related Docs
- docs/guidelines/intentional_divergences.md 2.87
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer-2/probe/nav_u44_earn3.json

## Related Code Areas
- the stalemate breaker and its stall/oscillation counters, navigation last_failure_reason, the tactical move path

## Assumptions / Open Questions
- WIDENED 2026-10-30 (SLEEP-WINS wake-window count, urban s46): 122 of 1,108 post-wake windows held the hunger project but stalled within 1-6 tiles of the target (median 3) in MovementMode.WANDER, WITHOUT STALEMATE_BREAK (p7, t1905-1950, target (27,20), jitter (25,20)-(25,22)). The en-route branch in tactical.py sets WANDER. The counts must cover both triggers: STALEMATE_BREAK, and the en-route WANDER jitter near the target.
- Main-law frequency unknown; the counts decide the priority.

- 2026-10-30 designer (N14 ruling): this ticket is the STALEMATE/WANDER nav FAMILY. Add as evidence the 100 of 155 urban s46 stalls aimed at an entity or position (mostly resolve_blocker), with counts split by target type. Named sub-finding: the movement rungs consider only the subject's own neighbours, so they never route to a door tile 2+ steps away (p4, fatigue, t1267: a free tile for 65 ticks, failure LEGAL). Sequenced after N14 F1 and the A' re-measure, before #781. Lane B counts (main): trigger A STALEMATE_BREAK 12 runs; trigger B (door) belongs to TCK-20261021.
## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
