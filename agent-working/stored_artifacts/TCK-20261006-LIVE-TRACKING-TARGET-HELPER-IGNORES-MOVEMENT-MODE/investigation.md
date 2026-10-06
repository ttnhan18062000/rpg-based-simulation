---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE
artifact_type: investigation
tags: [engine, combat]
---

# Investigation: should `resolve_live_tracking_target` respect the movement mode?

Outcome: **no change** (planner ruling, option C, 2026-10-06). The behavior is recorded, not fixed.

## 1. Facts (read from code; corpus: BRACKETING 1 move, SEEK_COVER 0)

- `resolve_live_tracking_target` returns the live position of `payload["target_id"]` when that entity is alive and active, for **every** movement mode.
- `tactical.py` 5.2 computes `bracket_pos` (a tile one step past the target on the far side from an ally, `positioning.py:84`) and uses it in four places, all in one block: a walkability check and a `!= current position` check that **gate whether the move is issued**, the issuing tick's destination, and the payload `target_position`. There is no other reader (`grep bracket_pos` over `src/` and `tests/`; `get_bracketing_position` is called only here).
- A comment at `pipeline_phases/movement.py:242-243` names `BRACKETING` (and `KITING`, `GUARDING_ALLY`) among the "real entity-tracking modes".
- Arriving does not end an `ENTITY_MOVE`: the movement phase `continue`s when position equals destination and leaves the task. Only `tracked_move_complete` ends a move.
- The flank tile is one step past the target, so its Manhattan distance to the target is 1 or 2 (2 on a diagonal). Gate 4's in-reach end needs distance <= reach, and a melee entity's reach is 1.

## 2. Per-mode intent, as the code states it

| mode / reason | intent | live tracking today |
|---|---|---|
| `PURSUE`, `INTERCEPT` | track the entity | as intended |
| `REPOSITION` + `BRACKETING` | de-facto pursuit (the code's own comment names it tracking; `bracket_pos` is honored on the issuing tick only) | as the code intends |
| `REPOSITION` + `SEEK_COVER` | reach `cover_pos` | would approach the threat; **latent, 0 corpus moves** |
| `RETREAT` + `KITING` | hold range | would approach the hostile by the same helper; **unobserved, 0 corpus moves** |
| `GUARD` (two reasons) | stand beside the target | unchanged (lifecycle: `TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER`) |

## 3. Why the ticket's fix was not made

Exempting the fixed-point modes from live tracking alone makes a bracketing entity walk to the flank tile and hold the move there, because arriving never ends a move and a diagonal flank is outside melee reach: it replaces "chase until adjacent, then the move ends and the brain can choose ATTACK" with an indefinite hold. A complete fix needs arrival to end a fixed-point move, which widens the Sticky-Task Law. The planner ruled that this is the owner's decision, not warranted by a P3 ticket with one corpus instance, and chose to record BRACKETING as de-facto pursuit and park the `SEEK_COVER` case as a trigger ticket.

## 4. Decision on `bracket_pos` (planner item 3)

The planner asked to drop `bracket_pos` if nothing else reads it. It is read, in the same block, as the issuance gate and the first-tick destination (section 1). Removing it would change which bracketing moves are issued and where they first head, so it is **kept**, and the planner was told. It is documented as de-facto pursuit instead.

## 5. Limits

- No behavior was measured: the corpus has one `BRACKETING` move and no `SEEK_COVER` or `KITING` move. Everything about `SEEK_COVER` and `KITING` is by reading the code.
- Whether bracketing should walk to the tile is a design question left to the owner, with the arrival-end rule it requires parked in `TCK-20261006-SEEK-COVER-LIVE-TRACKED-TOWARD-ITS-THREAT-LATENT-TRIGGER`.
