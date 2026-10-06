---
status: historical
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE
phase: done
date: 2026-10-06
tags: [engine, combat]
---

# TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE

## Title
`resolve_live_tracking_target` returns the live position of `payload["target_id"]` for every movement mode, so a
`BRACKETING` move discards its `bracket_pos` after one tick and a `SEEK_COVER` move would be steered toward the
threat it is meant to avoid

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by `rpg-implementer` measuring gate 4
(`TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION`) on
`lane-a-sticky-family-2` (`audit_mode`, budget disabled, seed 42, 2000 ticks, values).

`src/engine/candidate_selector.py:34`, `resolve_live_tracking_target`, resolves the live position of the move's
`target_id` **regardless of movement mode**. Consequences:

- **`BRACKETING` (observed, 1 instance):** `bracket_pos` is honoured only on the issuing tick, then overridden by
  live tracking of the target. The single real `BRACKETING` move on the corpus (`dungeon_crawl`, entity 12, from
  t318) never stood on its bracket tile; it chased and circled the hostile at distance 1-2 and never attacked.
  This answers gate 4's open question: **`bracket_pos` is a one-tick snapshot.**
- **`SEEK_COVER` (unobserved, 0 corpus instances):** a `REPOSITION` move that carries a ranged threat's
  `target_id` would, by the code, be live-tracked **toward** that threat.

**Why separate from gate 4, and why P3:** gate 4's fix (a dead, inactive or gone target ends the move) stops the
observed `BRACKETING` hold. Whether a `BRACKETING` move should walk to `bracket_pos` at all, rather than track the
target, is a tactical-design question that fix does not answer. `SEEK_COVER` has no instance on the corpus.

## Scope
1. State, per movement mode, whether it intends to track a live entity or to reach a fixed point. `PURSUE` and
   `INTERCEPT` track; `BRACKETING` and `SEEK_COVER` aim for a point; `KITING` holds a range.
2. Make `resolve_live_tracking_target` respect that intent: fixed-point modes keep their position, tracking modes
   track.
3. Add a constructed `SEEK_COVER` scenario, since the corpus never produces one, and assert it moves away from
   the threat.

## Out of Scope
- Ending moves on a dead target (gate 4).
- Guard-move lifecycles.

## Acceptance Criteria
- [x] Per-mode intent recorded (investigation section 2): `PURSUE` and `INTERCEPT` track; `BRACKETING` is de-facto pursuit by the code's own comment; `SEEK_COVER` and `KITING` aim for a point or a range but are live-tracked by the helper; guard unchanged.
- [ ] **Not done, superseded by the planner's ruling (option C, 2026-10-06):** fixed-point modes are not exempted from live tracking, because exempting alone makes a bracketing move hold at its tile and the complete fix (arrival ends a fixed-point move) widens the Sticky-Task Law, which is the owner's call. The candidate fix is carried by `TCK-20261006-SEEK-COVER-LIVE-TRACKED-TOWARD-ITS-THREAT-LATENT-TRIGGER`.
- [ ] **Not done, moved to the same trigger ticket:** a constructed `SEEK_COVER` scenario test; with no helper change there is nothing for it to pin yet.

## Related Tickets
- `TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION` (gate 4).

## Related Docs
- `docs/engine/` tactical contract (the entity-targeted objective section).

## Related Stored Artifacts
- Gate 4's `target_move_lifetimes.py` probe and its investigation.

## Related Code Areas
- `src/engine/candidate_selector.py:34`, `resolve_live_tracking_target`; `src/engine/tactical.py:591-597`.

## Assumptions / Open Questions
- **Lane.** Lane A, after gate 4.

## Implementation Notes
No source change. The planner ruled option C: leave `resolve_live_tracking_target` unchanged and record BRACKETING as de-facto pursuit in `docs/engine/contracts/tactical_contract.md` section 3, divergence 2.70 and parity COMB-331, citing the comment at `pipeline_phases/movement.py:242-243` and the diagonal-flank fact (distance 2 > melee reach 1, and arriving never ends a move).

The planner also asked to drop `bracket_pos` in `tactical.py` if nothing else reads it. **It is read**, in the same block: the walkability and `!= current position` checks gate whether a bracketing move is issued, and it is the issuing tick's destination and the payload `target_position`. Removing it would change which moves are issued, so it was kept (the planner's own condition), and the planner was told.

The latent `SEEK_COVER` case (and, by the same helper, `KITING`) is parked as `TCK-20261006-SEEK-COVER-LIVE-TRACKED-TOWARD-ITS-THREAT-LATENT-TRIGGER`, with the arrival-end rule as the candidate fix needing an owner decision.

## Test Summary
No behavior changed, so no tests were added or run for this ticket; the existing helper tests are unaffected because the helper is untouched. Nothing about `SEEK_COVER` or `KITING` was measured: the corpus has no such move.

## Files Changed
`docs/engine/contracts/tactical_contract.md`, `docs/guidelines/intentional_divergences.md` (2.70), `docs/parity_ledger/combat_movement.yaml` (COMB-331 support boundary); new parked ticket `agent-working/tickets/todos/TCK-20261006-SEEK-COVER-LIVE-TRACKED-TOWARD-ITS-THREAT-LATENT-TRIGGER.md`.

## Completion Summary
Resolved by recording, per the planner's ruling. BRACKETING is documented as de-facto pursuit; `bracket_pos` is kept because it gates issuance; the latent `SEEK_COVER` live-tracking case is parked as `TCK-20261006-SEEK-COVER-LIVE-TRACKED-TOWARD-ITS-THREAT-LATENT-TRIGGER` (fires when any corpus world produces a `SEEK_COVER` move). Known gaps: no behavior was measured for `SEEK_COVER` or `KITING` (0 corpus moves, by reading only); whether bracketing should walk to its tile is left to the owner.
