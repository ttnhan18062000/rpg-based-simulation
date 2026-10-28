---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-FLIGHT-OSCILLATION-COUNTS-NO-DECISION-TICKS-AND-A-CORNERED-SUBJECT-HOLDS
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-FLIGHT-OSCILLATION-COUNTS-NO-DECISION-TICKS-AND-A-CORNERED-SUBJECT-HOLDS

## Title
The flight-oscillation measure counts no-decision cadence ticks as "non-flee", and a cornered subject with no flight destination holds in place for about 190 ticks

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A's guard flicker trace on step 2 (TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY, f9b21b55b, crowded_frontier 42-46, 2026-10-21; probes flicker_probe.py and guard_probe.py, data /mnt/data/scratch-rpg-implementer/paired_en2/fl_43_11.json, fl_45_9.json, gp/).

Crowded guard re-onsets rose from 28 to 174. 92 of the 174 are one guard: s43 guard 11, t1984-~2170, hp 8/245, cornered with raiders 35 and 37 one tile away.
- Even ticks: the tactical pass returns PANIC_RETREAT with the destination equal to its own tile (`_destination_or_hold`).
- Odd ticks: the move has finished, so the task is an idle ENTITY_ACT with empty payload. The scheduler gives it a brain turn only on the strategic cadence (every 2nd tick for this guard), so no pass runs, no action is taken and the guard does not move.
- The oscillation measure (flee, then non-flee, then flee within 10 ticks) counts that no-decision tick as non-flee, so it is a label flip with no behaviour.
- It is not a perception drop, not a hysteresis edge (panic is constant at 0.505), and not an escalated need beating panic (escalated_need_wins and the need pull never fire).
- The same mechanism is in base: 9 such flickers from one guard (s45 guard 9).

Designer ruling (2026-10-21): out of family for v1. The metric definition and the cornered-hold question go to an after-v1 ticket linked to C6. The v1 N9 clause uses an oscillation share recomputed on the decision-tick definition.

Open before v1, tracked elsewhere: whether the hold is a hole in the pre-v1 (b) panic fall-through (owner_decision_memo row 83, a49896e1c), meaning an own-tile PANIC_RETREAT taken with no hostile acting on the subject. If it is a hole, that is a pre-v1 correction ruled by the designer, not this ticket.

## Scope
- (a) Metric: the oscillation and flight-onset measures count only ticks where a decision was made. A no-decision cadence tick continues the previous label. Apply it in the probe tooling and in any gate or row that counts flight alternation.
- (b) Design, ruled by the designer after v1: what a cornered subject with no flight destination does when a hostile IS acting on it (fight back, surrender or hold), and with what bound. Linked to C6 (a held ATTACK never disengages) and to the collapse question.
- Real-kernel tests for whatever is ruled for (b). Measure paired against v1 (seeds 42-46, D76).

## Out of Scope
- The (b) fall-through hole check before v1 (designer, 2026-10-21).
- Changing the brain cadence.

## Acceptance Criteria
- The oscillation measure ignores no-decision ticks, and its definition is written down where the measure lives.
- The designer's ruling on a cornered subject with no destination is in Bible 04 §1 with a test, and D76 shows no unexplained drift against v1.

## Related Tickets
- TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE (C6)
- TCK-20261021-SHOULD-A-PRESENT-ATTACKER-PUSH-THE-COLLAPSE-LINE
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
- TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1
- docs/plans/systemic_world/owner_decision_memo.md (row 83)
- docs/plans/systemic_world/v1_disclosure.md (N9)

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/paired_en2/ (fl_43_11.json, fl_45_9.json, gp/, fc/)

## Related Code Areas
- src/engine/tactical.py (`_destination_or_hold`, panic gate)
- scheduler.py (`_throttled`, strategic cadence)

## Assumptions / Open Questions
- A held subject still lands hits (designer, 2026-10-21; DeathLedger, Lane A probe hp_multi_probe.py, paired_en2/pp/). Guard 11 (crowded s43, f9b21b55b) struck raider 37 at t1990, 1996 and 2007 while its tactical result was an own-tile PANIC_RETREAT hold. Which path issues the attack, and is the hold actually the action on those ticks? Not yet traced; after v1.
- Method (designer, 2026-10-21): every "attacks / never attacks" claim comes from DeathLedger HIT entries with attacker ids, never from the post-tick task payload, because an attack that resolves inside a tick leaves no payload behind.
- The oscillation definition chosen for v1 rows N7/N9/§7 is (4), decisions only: a flee decision, then 1-2 non-flee decisions, then a flee decision, independent of cadence, with raw (1) shown beside it. This ticket adopts (4).
- Cross-link: the definition of "a hostile acting on the subject" (today a state test, see guard 11) is ruled in TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE, not here. Here, (b) of the scope follows that definition.
- Does the same counting artefact inflate N7's frontier oscillation (235 -> 190)? The recompute answers it.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
