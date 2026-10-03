---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT
phase: open
date: 2026-08-21
tags: [architecture, performance]
---

# TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT

## Title
Server-side spatial broadcast filtering (Area of Interest) for the live map, at real scale — gated on M1

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (M1 of `docs/plans/live_map_scaling_roadmap.md`) ships a
per-tick entity-delta broadcast that sends every connected viewer every changed entity, regardless of
whether it's anywhere near what that viewer is actually looking at. `GameCanvas.tsx` already computes a
`vision_range`-filtered visible set client-side, but purely for cosmetic fog-of-war dimming — the server
ships the full world to every client today. An external design review of M1's proposal, followed by
independent verification (see `docs/plans/live_map_reconnection_epic.md` §D), reworked the review's own
bandwidth extrapolation and found the underlying concern is real and likely more urgent than either the
original epic or the reviewer first stated: at the actual `CLASS_A` target scale (10,000 entities), even a
modest 10-20% per-tick changed-entity fraction produces an estimated ~1.5-5MB/s per viewer — a real risk,
not a hypothetical one, though still an analytical estimate rather than a live measurement. M1 reserves an
unused spatial-subscription field in its broadcast envelope specifically so this epic can be built later
without a breaking protocol change. This epic exists to track that follow-on work as its own milestone
(M3), independent of M2's rendering-performance work.

## Scope
Not created yet — this epic is scope-only, gated, and not to be broken into child tickets until M1 ships
(see Assumptions / Open Questions). Prospective scope:
- Turn the existing client-side `vision_range` filtering logic (`GameCanvas.tsx`) into real server-side
  broadcast filtering — the server computes, per connected viewer/spectated-entity, which entities are
  actually relevant to send, using the spatial-subscription field M1's broadcast envelope reserves for
  this.
- Define the actual subscription granularity (e.g. per-spectated-entity vision radius, vs. a coarser
  region/chunk subscription) — an open design decision for this epic's own Investigate phase, not resolved
  here.
- Preserve correctness: a viewer switching what/who they're spectating must not silently miss entities that
  just entered their new area of interest — ties into the same connect-time-handoff correctness discipline
  M1's Scope item 2 already established (register interest before consuming the filtered stream, not
  after).

## Out of Scope
- Everything in M1's own scope (`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`) — this epic starts only after
  M1 ships.
- Starting any implementation before M1's real performance-validation pass provides measured bandwidth
  numbers at real entity/viewer counts — the hard gate stated in `docs/plans/live_map_scaling_roadmap.md`.
  The 1.5-5MB/s figure motivating this epic is an analytical estimate from this session, not a live
  measurement; this epic does not start implementation on the strength of that estimate alone.
- Rendering-side performance work (chunked terrain caching, dirty-rect entity rendering) — that's
  `TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE` (M2), a separate, independent epic with no dependency
  on this one.
- Priority/update-rate tiering (updating distant entities less frequently than nearby ones) — a related but
  distinct technique, explicitly deferred in M1's plan doc as premature before even this epic's own
  filtering is measured; not assumed in scope here either.

## Acceptance Criteria
- [ ] Not started until `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (M1) is DONE and its performance-validation
      pass has produced real measured bandwidth numbers showing this work is actually needed
- [ ] A documented, ordered child-ticket breakdown exists before implementation begins (not created yet)
- [ ] Each child ticket, when opened, references this epic, `docs/plans/live_map_reconnection_epic.md` §D,
      and `docs/plans/live_map_scaling_roadmap.md`
- [ ] No implementation happens directly on this epic ticket

## Related Tickets
- `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` — M1, a hard prerequisite (not a soft reference): this epic
  does not start, and should not even be broken into child tickets, until M1 ships and measures. M1's
  Scope item 7 (reserved spatial-subscription field) exists specifically to unblock this epic later without
  a breaking change.
- `TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE` — M2, an independent sibling epic (also gated on M1,
  no dependency between M2 and M3 in either direction).

## Related Docs
- `docs/plans/live_map_scaling_roadmap.md` — the milestone sequencing this epic is M3 of
- `docs/plans/live_map_reconnection_epic.md` — §D documents the bandwidth reassessment motivating this
  epic, including the corrected math and the explicit note that it's an estimate, not a measurement

## Related Stored Artifacts
None.

## Related Code Areas
- Backend broadcast/presenter layer (`src/api/presenters/state_presenter.py`, `src/api/ws/stream.py`, or
  wherever M1 lands the delta-broadcast logic) — this epic's primary target
- `frontend/src/components/GameCanvas.tsx` — the existing client-side `vision_range` filtering logic this
  epic's server-side version is modeled on (read-only reference, not necessarily modified)

## Assumptions / Open Questions
- **Hard gate, not an assumption**: this epic must not begin — including its own child-ticket breakdown —
  until M1 is DONE and has produced real bandwidth numbers. The motivating ~1.5-5MB/s/viewer estimate is
  analytical, not measured; real numbers from M1 may show this is unnecessary, more urgent, or differently
  shaped than currently understood.
- Subscription granularity (per-entity vision radius vs. coarser region/chunk subscriptions) is
  unresolved — left to this epic's own Investigate phase once unblocked.
- Whether this epic's filtering interacts with the minimap's existing display (which currently shows a
  full-world overview even when spectating, per `GameCanvas.tsx`) is unresolved — a real product question
  about whether the minimap should also become filtered, not assumed either way here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
