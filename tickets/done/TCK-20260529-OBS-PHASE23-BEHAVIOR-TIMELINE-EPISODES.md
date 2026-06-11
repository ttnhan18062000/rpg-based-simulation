---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260529-OBS-PHASE23-BEHAVIOR-TIMELINE-EPISODES
phase: done
date: 2026-05-29
tags: [obs, phase23, behavior, timeline, episodes]
---

# TCK-20260529-OBS-PHASE23-BEHAVIOR-TIMELINE-EPISODES

## Title

Behavior Timeline and Episode Reconstruction (Phase 23)

## Status

INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Build readable entity behavior histories by grouping behavioral events chronologically and reconstructing episodes post-run.

## Scope

- Implement immutable `BehaviorEpisode` model
- Implement `EntityBehaviorTimeline` and capacity-bounded `BehaviorTimelineStore`
- Implement post-run/async `EpisodeDetector` capturing combat, quest, information, and failure-response episodes
- Guarantee zero simulation tick overhead

## Out of Scope

- Running episode detection inside the engine tick loop

## Acceptance Criteria

- Fully covered by unit, integration, and compatibility tests
- All tests pass cleanly under the `not slow` marker
- Documentation in `docs/entity/entity_base.md` updated with Section 36

## Related Tickets

- None

## Related Docs

- `docs/entity/entity_base.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/behavior/`

## Assumptions / Open Questions

- None

## Test Summary

- Pending execution

## Files Changed

- Pending modification
