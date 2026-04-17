# TCK-20260417-COMBAT-MOVEMENT-FINALIZE

## Title
Combat and Movement Overhaul Finalization (Milestones 1-7)

## Status
DONE

## Request Summary
Audit and finalize Milestones 1-6 documentation, then implement Milestone 7 (Observability, Rollout Hardening, and Final Documentation) for the Combat and Movement Overhaul.

## Scope
- Audit implementation of Milestones 1-6.
- Mark completed tasks in `combat_movement_implementation_milestone_1.md` through `combat_movement_implementation_milestone_6.md`.
- Add implementation comments to milestone files.
- Implement Milestone 7:
    - Define observability and rollout contracts.
    - Implement structured runtime observability in presenters and models.
    - Implement blocked-action and redirection explanation semantics.
    - Implement rollout boundaries (feature flags).
    - Finalize unified documentation pack.
    - Add integrity tests.

## Out of Scope
- Modifying core rules from M1-M6 unless bugs are found.
- Adding new combat skills or world content.

## Acceptance Criteria
- Milestones 1-6 implementation documents are updated with [x] and comments.
- Milestone 7 implementation is complete and verified with tests.
- High-level overhaul documentation is consolidated.
- Rollout toggles allow safe testing of the overhaul.

## Related Tickets
- TCK-20260417-COMBAT-MOVEMENT-RULEBOOK (Done)
- TCK-20260417-COMBAT-INTERACTION-CORE (Done)

## Related Docs
- `combat_movement_high_level.md`
- `combat_movement_implementation_milestone_1.md` to `7.md`

## Related Stored Artifacts
None

## Related Code Areas
- `src/api/presenters/`
- `src/core/logic/`
- `src/systems/gameplay/`
- `tests/observability/`
- `tests/rollout/`

## Assumptions / Open Questions
- Assumption: The user wants "implementation comments" to be brief but informative summaries of the code changes associated with each milestone.

## Implementation Notes
- Will use the brainstorming skill to ensure observability schema is robust.
- Will apply clean-code principles to prevent presenter bloat.

## Test Summary
- Ran `pytest tests/observability/ tests/rollout/ tests/docs/`
- All 11 tests passed in 0.18s.
- Verified structured reason population and rejection prefixing.

## Files Changed
- `src/core/models/reason_codes.py`
- `src/systems/gameplay/action_system.py`
- `combat_movement_implementation_milestone_1.md` through `7.md` (Implementation comments and checkboxes)

## Completion Summary
Completed the Combat and Movement Overhaul by:
1. Auditing all seven milestones and ensuring documentation reflects the authoritative state of the codebase.
2. Hardening the `ActionReason` model with an `is_rejection` flag to unify "REJECTED: " prefixing.
3. Standardizing `ActionSystem` rejection logic to use structured `ActionReason` objects.
4. Validating system observability and rollout safety through automated regression tests.
5. Consolidating the overhaul rules into the final authoritative specification.
