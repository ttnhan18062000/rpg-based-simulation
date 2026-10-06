---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-SEEK-COVER-LIVE-TRACKED-TOWARD-ITS-THREAT-LATENT-TRIGGER
phase: open
date: 2026-10-06
tags: [engine, combat]
---

# TCK-20261006-SEEK-COVER-LIVE-TRACKED-TOWARD-ITS-THREAT-LATENT-TRIGGER

## Title
Latent, trigger ticket: a `SEEK_COVER` move would be live-tracked toward the ranged threat it is meant to avoid. Fires when any corpus world produces a `SEEK_COVER` move.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Split out of `TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE` by the planner's ruling (option C, 2026-10-06). `tactical.py:562` issues a `REPOSITION` move with reason `SEEK_COVER`, a fixed `cover_pos` as its destination and the ranged threat as `payload["target_id"]`. `MovementCandidateSelector.resolve_live_tracking_target` returns the live position of `target_id` for every movement mode, so by the code the entity is steered **toward the threat** instead of to `cover_pos`.

**Latent, not observed:** 0 `SEEK_COVER` moves in the corpus (4 worlds x 2 runs x 2000 ticks, gate 4 probe), so it is by code reading only and untested end to end.

**Trigger:** fires when any corpus world produces a `SEEK_COVER` move. Check with gate 4's `target_move_lifetimes.py` probe (group `REPOSITION/SEEK_COVER`), run from the worktree it measures (content seeds from the cwd-relative `data/content`).

## Scope
1. When triggered, confirm on the real move that the entity approaches the threat.
2. Candidate fix, **needs an owner decision (it widens the Sticky-Task Law)**: exempt the fixed-point modes (`REPOSITION` with `BRACKETING`/`SEEK_COVER`, and `RETREAT` with `KITING`) from live tracking **and** end those moves on arrival (position equals destination) through `tracked_move_complete`. Exempting alone would reintroduce the hold family: the movement phase only stops moving on arrival and leaves the task, so a fixed-point move with no arrival end holds indefinitely.
3. A constructed scenario that asserts a `SEEK_COVER` move heads away from the threat.

## Out of Scope
- `BRACKETING`: recorded as de-facto pursuit by the planner's ruling (a diagonal flank is distance 2 > melee reach 1, so exempting it would hold).
- Ending moves on a dead target (done in `TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION`).

## Acceptance Criteria
- [ ] Trigger observed on a real corpus move, or the ticket remains parked.
- [ ] Owner decision recorded on arrival-ends-a-fixed-point-move.
- [ ] A `SEEK_COVER` move heads away from the threat, with a disabling control.

## Related Tickets
- `TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE` (resolved by recording).
- `TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION`.

## Related Docs
- `docs/engine/kernel.md` (Sticky-Task Law); `docs/engine/contracts/tactical_contract.md` section 3.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE/investigation.md`.

## Related Code Areas
- `src/engine/tactical.py:562`; `src/engine/candidate_selector.py` (`resolve_live_tracking_target`, `tracked_move_complete`); `src/engine/pipeline_phases/movement.py` (the `continue` at arrival).

## Assumptions / Open Questions
- **KITING** (`RETREAT` + reason `KITING`) has the same shape by the code (its `target_id` is the hostile, so live tracking would approach it) and is also unobserved (0 corpus moves). The ticket this was split from never covered it; the owner decision above should cover both.
- Lane A, only once triggered.

## Implementation Notes
(parked until triggered)

## Test Summary
(parked until triggered)

## Files Changed
(parked until triggered)

## Completion Summary
(parked until triggered)
