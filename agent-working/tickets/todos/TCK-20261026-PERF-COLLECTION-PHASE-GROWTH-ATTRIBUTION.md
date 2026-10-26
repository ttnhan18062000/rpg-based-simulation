---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261026-PERF-COLLECTION-PHASE-GROWTH-ATTRIBUTION
phase: open
date: 2026-10-26
tags: [performance, investigation]
---

# TCK-20261026-PERF-COLLECTION-PHASE-GROWTH-ATTRIBUTION

## Title
Attribute the collection phase's growth from about 50 ms to about 260 ms per tick (movement, measurement-only)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
`TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP` recorded that `collection` grew from about 50 ms to about 260 ms per tick, around index 85 of its bisect series. Neither H1 nor the tick-cost growth investigation attributed it. It has no ticket. rpg-planner has no objection to perf filing it as measurement-only (#593 issuecomment-6420451647).

## Scope
- On a lead-granted heavy-run slot, one process at a time: profile `collection` at movement[1000] with the same pinned setup as `TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1`. Use 3 serial `--sampler none` runs plus one py-spy run.
- Name the callees that make up at least 80 % of the phase.
- If a single cause stands out, bisect it with `git archive` arms against its introducing window.
- Report a CLOSE or FIX verdict against the 2 % of the tick threshold (the H3/H4 rule). Any fix goes to the code's owner.

## Out of Scope
- Any fix in `src/` outside `src/perf/`.
- `combat_engagement` (its own ticket).

## Acceptance Criteria
- The collection-phase cost at movement[1000] on current main is measured, PROVISIONAL.
- At least 80 % of it is attributed to named callees.
- The verdict is recorded in `docs/performance/tick_cost_growth.md`.

## Related Tickets
- `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`
- `TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1`

## Related Docs
- `docs/performance/tick_cost_growth.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/perf/profile_tick.py`
- the collection phase in `src/engine/` (rpg-owned; read only)

## Assumptions / Open Questions
- The 50 to 260 ms figures come from single runs on a loaded host (2026-10-06). The growth may be smaller on a pinned measurement; that would be a finding too.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
