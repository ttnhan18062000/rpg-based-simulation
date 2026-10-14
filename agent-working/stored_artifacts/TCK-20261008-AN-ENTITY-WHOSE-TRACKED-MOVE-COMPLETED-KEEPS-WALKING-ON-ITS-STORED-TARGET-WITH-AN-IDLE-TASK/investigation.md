---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261008-AN-ENTITY-WHOSE-TRACKED-MOVE-COMPLETED-KEEPS-WALKING-ON-ITS-STORED-TARGET-WITH-AN-IDLE-TASK
phase: done
date: 2026-10-08
tags: [combat]
---

# Investigation: TCK-20261008-AN-ENTITY-WHOSE-TRACKED-MOVE-COMPLETED-KEEPS-WALKING-ON-ITS-STORED-TARGET-WITH-AN-IDLE-TASK

## Attribution (read-only, file and line)
- The completion's `target_clear` (`executor.py`, `candidate_selector.tracked_move_completion_update`) survives every merge and the target is None at the end of its tick (urban seed 45 eids 20, 17, 15).
- The target comes back on a later tick from a different writer: `intelligence.py:665-667` (objective with a position and no target entity: resolve_blocker/reach_location, stabilize/investigate, guild/reach_location), `intelligence.py:674` (town target + REGROUP), `pipeline_phases/groups.py:119`, `domain/cognition.py:78` (the brain), `domains/cooperation/phase.py:200`. Urban seed 45, 400 ticks: 43 completions, 13 re-seeded within 3 ticks (8 by line 667, 1 by 674, 2 groups, 1 brain, 1 unattributed); `frontier_living_world` seed 42: 3 of 43.
- Mover: `MovementPhase.route_movement_intent` -> `MovementSystem.resolve_move`, fed by `movement_target`'s stored-target branch (the executor only reaffirms targets for ENTITY_MOVE work).

## Classification (current main, pinned 5x3, mean (SD) hits per run)
base: held move 102.4 / 92.6 / 40.6 (REGROUP 19.6 / 49.2 / 13.4); idle walker 74.2 / 56.4 / 39.0; decided 8.6 / 9.0 / 7.8. See divergence 2.89 for the batch.

## Three arms (main / engaged-only / any perceived hostile)
OA hits 185.2 / 179.8 / 14.0; 158.0 / 123.0 / 37.4; 87.4 / 64.6 / 8.4. Total deaths within 1 SD in all arms. any-hostile stalls: blocked entity-ticks 1250 / 1567 / 694 per run, longest 137 / 219 / 138 ticks. Decision 32 (notice and decide) took the event-driven path.

## Freeze split (engaged-only before the release)
Held REGROUP up to 65 / 109 / 66 ticks, PANIC_RETREAT 33 / 43 / 33, LEASH_RETURN 33; idle ENTITY_ACT at most 15. A queued-ATTACK hold never reaches the counter. Fixed by the flight exemption and the release (`move_ends_here`).

## Final batch (engaged-only + exemption + release)
Longest blocked run for a held move 1 tick in every class; idle ENTITY_ACT up to 19 / 18 / 14. Digests equal across two runs (df4c991cbbab).

## #424 5-seed report (parent 07da5d1e9 to 2a50072f2)
OA hits 279.0 to 291.4, 276.2 to 241.2, 135.8 to 133.0; total deaths 37.6 to 37.8, 43.2 to 43.0, 23.8 to 25.8; alive t=1100 2.8 to 2.2, 13.4 to 13.6, 6.8 to 4.6; all inside 1 SD (recorded in divergence 2.83).

## Open
Unattributed re-seeds (1 of 13, 2 of 3); the stale PURSUE label is cosmetic. Probes: probes/.
