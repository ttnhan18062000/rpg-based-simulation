---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE
phase: open
date: 2026-10-06
tags: [engine, combat]
---

# TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE

## Title
`resolve_live_tracking_target` returns the live position of `payload["target_id"]` for every movement mode, so a
`BRACKETING` move discards its `bracket_pos` after one tick and a `SEEK_COVER` move would be steered toward the
threat it is meant to avoid

## Status
OPEN

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
- [ ] Per-mode intent recorded.
- [ ] Fixed-point modes no longer live-tracked; a disabling-control test for each.
- [ ] A `SEEK_COVER` scenario test moves away from the threat.

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
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
