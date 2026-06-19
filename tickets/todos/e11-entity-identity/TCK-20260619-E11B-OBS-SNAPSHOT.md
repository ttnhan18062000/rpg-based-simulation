---
status: open
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E11B-OBS-SNAPSHOT
phase: open
date: 2026-06-19
tags: [entity-differentiation, observability, personality, class-system, phase-1]
---

# TCK-20260619-E11B-OBS-SNAPSHOT

## Title
E11-B · Add per-entity personality snapshot to LIGHT observability mode

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
LIGHT observability mode currently does not expose personality vectors or class_id per entity. This makes it impossible to measure behavioral differentiation or correlate personality with route choices. After this ticket, LIGHT mode snapshots include: role, class_id, and personality vector (greed, bravery, sociability, industry) for each entity at each snapshot tick.

## Scope
- Read `src/observability/` to understand LIGHT mode snapshot structure
- Extend the per-entity snapshot record to include:
  - `role` — from `entity.identity.role`
  - `class_id` — from `entity.identity.class_id`
  - `personality` — dict of `{greed, bravery, sociability, industry}` from `entity.personality`
- The extension must not change the snapshot format in a breaking way (add fields, don't remove or rename)
- Update any snapshot dataclass or dict structure accordingly
- Write a unit test verifying that a compiled world's LIGHT snapshot includes personality data

## Out of Scope
- FULL or DEBUG mode changes
- Visualizing or exporting personality data to external systems

## Acceptance Criteria
- LIGHT snapshot per-entity record contains `role`, `class_id`, `personality` dict
- Test verifies personality fields are non-None in a compiled world snapshot

## Related Tickets
- TCK-20260619-E11-ENTITY-IDENTITY (parent epic)
- TCK-20260619-E11A-HERO-AUTHORING (run after — needs HERO entities)
- TCK-20260619-P0-ENTITY-INIT (prerequisite — personality seeding done)

## Related Docs
- `src/observability/config.py` (LIGHT mode definition)
- `docs/mechanics/01_entity_anatomy.md` § Biological Laws

## Related Code Areas
- `src/observability/`
- `src/core/state.py:PersonalityComponent`

## Assumptions / Open Questions
- What does the LIGHT mode snapshot currently include? Read `src/observability/config.py` and related files first.
- Is there a snapshot serialization method that needs updating?

## Implementation Notes
Read the observability module before any changes. Follow existing snapshot field patterns. Personality is on `entity.personality` (a `PersonalityComponent` dataclass).

## Test Summary
New test in `tests/unit/observability/test_personality_snapshot.py`:
- `test_light_snapshot_includes_personality()` — build minimal world; run snapshot; assert entity record has personality fields

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
