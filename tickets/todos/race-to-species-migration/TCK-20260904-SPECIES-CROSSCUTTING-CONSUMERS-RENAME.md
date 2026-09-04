---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME
phase: open
date: 2026-09-04
tags: [content, observability]
---

# TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME

## Title
Rename remaining race_id/RaceDefinition consumers outside the core schema and race-relations subsystem

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child 3/4 of `TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY`. Depends on
`TCK-20260904-SPECIES-CORE-SCHEMA-RENAME`. Covers every remaining `race`/`race_id` consumer not
already handled by child 1 (core schema) or child 2 (race-relations subsystem) — the kernel, engine
cognition/replay, observability, quests, API websocket stream, world environment, and remaining
content data files.

## Scope
- `src/engine/kernel.py`, `src/engine/cognition.py`, `src/engine/replay_manager.py`.
- `src/observability/event_recorder.py`, `src/observability/event_shapers.py`,
  `src/observability/alerts/sinks.py`.
- `src/quests/generator.py`, `src/api/ws/stream.py`.
- `src/world/environment.py` (the `RaceDefinition`-referencing comment about hazard_immunities noted
  during investigation), `src/content_semantics/personality.py`.
- Remaining content data: `data/content/entities/entity_archetypes.yaml`,
  `data/content/social/factions.yaml`, `data/content/social/personality_bias.yaml`.
- Any remaining `race`-referencing test file not already covered by child 2's list — confirm the
  actual remaining set at pickup time (14 of the 20 originally-found test files, per the epic's
  count, since 6 are child 2's).

## Out of Scope
- Core schema/entity plumbing — child 1.
- Race-relations subsystem — child 2.
- Docs sweep — child 4.

## Acceptance Criteria
- [ ] Every listed file's `race`/`race_id` reference renamed consistently with child 1's chosen
      naming.
- [ ] Remaining content data files updated to reference the renamed catalog paths/field names.
- [ ] All affected tests pass unchanged.

## Related Tickets
- TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY (parent epic)
- TCK-20260904-SPECIES-CORE-SCHEMA-RENAME (dependency)

## Related Docs
None beyond the parent epic.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/kernel.py`, `src/engine/cognition.py`, `src/engine/replay_manager.py`
- `src/observability/event_recorder.py`, `src/observability/event_shapers.py`,
  `src/observability/alerts/sinks.py`
- `src/quests/generator.py`, `src/api/ws/stream.py`, `src/world/environment.py`,
  `src/content_semantics/personality.py`
- `data/content/entities/entity_archetypes.yaml`, `data/content/social/factions.yaml`,
  `data/content/social/personality_bias.yaml`

## Assumptions / Open Questions
- Exact remaining test-file list should be re-confirmed at pickup time (childrens' scopes may shift
  slightly once child 1/2 land and some renames turn out to already be covered).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
