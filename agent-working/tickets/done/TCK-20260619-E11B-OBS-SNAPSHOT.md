---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E11B-OBS-SNAPSHOT
phase: done
date: 2026-06-19
tags: [entity-differentiation, observability, personality, class-system, phase-1]
---

# TCK-20260619-E11B-OBS-SNAPSHOT

## Title
E11-B · Add per-entity personality snapshot to LIGHT observability mode

## Status
DONE

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
Used `entity.identity.personality` (NOT `entity.personality` which was incorrect in the original ticket). Added three fields after `latest_anomaly_flags` in `EntityInspectionSnapshot` with safe defaults. Populated via a block labelled "8. Identity extension" before the single constructor call in `inspect_entity()`. All early-return stubs (L33, L40, L44) remain unmodified; defaults handle them.

## Test Summary
New tests in `tests/unit/observability/test_personality_snapshot.py` (4 tests):
- `test_light_snapshot_includes_personality` — explicit personality values; asserts exact key set, float types, and `pytest.approx` values.
- `test_light_snapshot_personality_non_none_for_compiled_entity` — default PersonalityComponent; asserts all four keys present and non-None.
- `test_light_snapshot_missing_entity_has_no_personality` — missing entity ID 999; asserts `exists=False` with safe defaults.
- `test_existing_fields_unaffected` — asserts all 16 original field names still present in `model_fields`.

All 4 new tests pass. 453 unit observability tests pass. 5 integration observability tests pass.

## Files Changed
- `src/observability/live/entity_inspector.py` — added 3 fields to `EntityInspectionSnapshot`; added identity-extension block + 3 kwargs to `inspect_entity()` constructor call.
- `tests/unit/observability/test_personality_snapshot.py` — created; 4 new tests.
- `docs/parity_ledger/infrastructure.yaml` — appended INFRA-205.

## Completion Summary
LIGHT mode entity snapshot now surfaces `role` (Optional[int]), `class_id` (Optional[str]), and `personality` dict (greed, bravery, sociability, industry as float) per entity. No breaking changes; additive fields with defaults. Parity ledger entry INFRA-205 added and verified.
