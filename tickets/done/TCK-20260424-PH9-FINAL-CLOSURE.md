# TCK-20260424-PH9-FINAL-CLOSURE

## Title
Phase 9: Strategic & Social Cognition Final Closure

## Status
DONE

## Request Summary
Finalize the implementation of Phase 9 milestones including biological needs, hero lifecycle, recruitment negotiation, and regional dynamics. Update all project management artifacts.

## Scope
- Implement authoritative biological decay (hunger, sleep) and routine actions.
- Implement hero lifecycle (aging, permadeath) and near-death hardening.
- Implement recruitment cost scaling and social bargaining.
- Implement regional hazards (passive HP drain) and suppression.
- Implement anchored-world behavior (home return) and role-based biasing.
- Update legacy checklists and project artifacts.

## Acceptance Criteria
- [x] Biological decay logic integrated into `ApplyPath`.
- [x] Routine actions (EAT, SLEEP) correctly reduce debt.
- [x] Hero aging and death resolved in `LifecycleSystem`.
- [x] Near-death survival grants permanent max HP boost.
- [x] Recruitment cost scales with level and trust.
- [x] Regional hazard damage and action suppression enforced in pipeline.
- [x] Entities return to home region when idle.
- [x] 19 contract tests pass.
- [x] Artifacts updated and archived.

## Implementation Notes
- Resolved `NameError` in `RoutineService` (missing `replace`).
- Resolved `RuntimeError` in `AuthoritativeApplyPipeline` (dictionary changed size during iteration).
- Centralized role-based biasing in `RoutineService`.

## Test Summary
- `pytest tests_v2/strategic/test_biological_needs.py` (PASS)
- `pytest tests_v2/progression/test_lifecycle.py` (PASS)
- `pytest tests_v2/social/test_recruitment.py` (PASS)
- `pytest tests_v2/world/test_regional_consequences.py` (PASS)
- `pytest tests_v2/world/test_anchored_world.py` (PASS)
- `pytest tests_v2/strategic/test_role_biasing.py` (PASS)

## Files Changed
- `src_v2/core/state.py`
- `src_v2/core/strategic.py`
- `src_v2/core/enums.py`
- `src_v2/engine/apply.py`
- `src_v2/engine/pipeline.py`
- `src_v2/systems/social.py`
- `src_v2/systems/routine.py`
- `src_v2/systems/strategic.py`
- `legacy_checklist_part5.md`
- `legacy_checklist_part4.md`

## Completion Summary
Phase 9 is closed. The engine now supports high-fidelity strategic and social behaviors with authoritative kernel enforcement of biological and regional constraints.
