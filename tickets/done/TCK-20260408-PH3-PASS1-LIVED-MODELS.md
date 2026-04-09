# Ticket: TCK-20260408-PH3-PASS1-LIVED-MODELS
# Title: Phase 3 Pass 1: Lived-Structure Core Models

## Request Summary
Implement the core data structures for Phase 3: Macro-Continuity and Strategic Realism. This involves defining models for routines, roles, place attachments, and group coordination.

## Scope
- [ ] Establish Phase 3 boundary in `phase_3_ds_implementation_plan.md`.
- [ ] Create `src/core/models/lived_structure.py` with `RoutineProfile`, `PlaceAttachment`, and `GroupRecord`.
- [ ] Standardize `LifeRole`, `GroupKind`, and `AttachmentKind` in `src/core/models/enums.py`.
- [ ] Integrate these models into `IdentityAspect` and `MindAspect`.
- [ ] Add registries (groups, etc.) to `WorldState`.

## Out of Scope
- AI behavioral integration (Pass 2).
- Routine/Group scheduling services (Pass 3).
- Presentation layer extensions (Pass 4).

## Acceptance Criteria
- New models exist and are properly typed (Pydantic).
- `Entity` model integrates `world_role`, `cluster_id`, and `household_id`.
- `MindAspect` integrates `routine_profiles` and `place_attachments`.
- Serialized snapshots can persist and reload these new structures correctly.
- Basic instantiation unit tests pass.

## Related Tickets
- Supersedes `TCK-20260408-PH3-STG1-HOUSEHOLD`.

## Status
DONE
